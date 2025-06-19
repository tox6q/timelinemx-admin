import os
import boto3
import csv
import re
import uuid
import json
from urllib.parse import quote
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv
from collections import defaultdict

# Load environment variables
load_dotenv()

def load_existing_csv(csv_filename):
    """Load existing CSV data to preserve manual edits"""
    existing_data = []
    existing_names = set()
    
    if os.path.exists(csv_filename):
        print(f"📂 Found existing {csv_filename}, loading data...")
        try:
            with open(csv_filename, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    existing_data.append(row)
                    existing_names.add(row['name'])
            print(f"   ✅ Loaded {len(existing_data)} existing entries")
        except Exception as e:
            print(f"   ⚠️  Error reading existing CSV: {e}")
            print(f"   📝 Will create fresh CSV file")
    else:
        print(f"📝 No existing {csv_filename} found, creating new file")
    
    return existing_data, existing_names

def group_jersey_images(s3_objects, bucket_name, region):
    """Group jersey images by name and create image arrays"""
    jersey_groups = defaultdict(list)
    
    # Group files by jersey name
    for obj in s3_objects:
        key = obj['Key']
        
        # Skip folder markers and non-image files
        if key.endswith('/') or not key.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
        
        # Extract filename from key (remove all-jerseys/ prefix)
        filename = key.replace('all-jerseys/', '')
        
        # Extract jersey name and number
        # Pattern: "Jersey Name (1).png" -> name="Jersey Name", number=1
        match = re.match(r'^(.+?)\s*\((\d+)\)\.(png|jpg|jpeg)$', filename, re.IGNORECASE)
        
        if match:
            jersey_name = match.group(1).strip()
            image_number = int(match.group(2))
            
            # Generate S3 URL with proper encoding
            encoded_key = quote(key, safe='/')
            image_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{encoded_key}"
            
            jersey_groups[jersey_name].append({
                'number': image_number,
                'url': image_url,
                'filename': filename
            })
        else:
            print(f"   ⚠️  Skipping file with unexpected format: {filename}")
    
    # Sort images within each group by number
    for jersey_name in jersey_groups:
        jersey_groups[jersey_name].sort(key=lambda x: x['number'])
    
    return jersey_groups

def generate_jerseys_csv():
    """Generate jerseys.csv from AWS S3 all-jerseys folder (incremental updates)"""
    
    print("🎯 Generating jerseys.csv from AWS S3 (incremental)")
    print("=" * 60)
    
    # Get AWS credentials from environment
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    region = os.getenv('AWS_REGION', 'us-east-1')
    bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
    
    # Check if credentials are provided
    if not access_key or not secret_key or not bucket_name:
        print("❌ Missing AWS credentials in .env file")
        print("Required:")
        print("  AWS_ACCESS_KEY_ID=your_access_key")
        print("  AWS_SECRET_ACCESS_KEY=your_secret_key")
        print("  AWS_REGION=your_region")
        print("  AWS_S3_BUCKET_NAME=your_bucket_name")
        return False
    
    try:
        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        print(f"✅ Connected to AWS S3 bucket: {bucket_name}")
        print(f"   Region: {region}")
        print("")
        
        # Load existing CSV data
        csv_filename = 'products.csv'
        existing_data, existing_names = load_existing_csv(csv_filename)
        
        # List objects in all-jerseys folder
        print("🔍 Scanning all-jerseys folder for files...")
        
        # Handle pagination for large number of files
        all_objects = []
        continuation_token = None
        
        while True:
            if continuation_token:
                response = s3_client.list_objects_v2(
                    Bucket=bucket_name,
                    Prefix='all-jerseys/',
                    ContinuationToken=continuation_token
                )
            else:
                response = s3_client.list_objects_v2(
                    Bucket=bucket_name,
                    Prefix='all-jerseys/'
                )
            
            if 'Contents' in response:
                all_objects.extend(response['Contents'])
            
            if response.get('IsTruncated'):
                continuation_token = response.get('NextContinuationToken')
            else:
                break
        
        if not all_objects:
            print("❌ No files found in all-jerseys folder")
            return False
        
        print(f"   📊 Found {len(all_objects)} total files")
        
        # Group jersey images by name
        print("🔄 Grouping jersey images by name...")
        jersey_groups = group_jersey_images(all_objects, bucket_name, region)
        
        print(f"   📊 Found {len(jersey_groups)} unique jerseys")
        
        # Process jersey groups
        new_entries = []
        jerseys_processed = 0
        jerseys_skipped = 0
        
        for jersey_name, images in jersey_groups.items():
            print(f"   👕 Processing: {jersey_name} ({len(images)} images)")
            
            # Check if this jersey already exists
            if jersey_name in existing_names:
                print(f"     ⏭️  Skipping existing: {jersey_name}")
                jerseys_skipped += 1
                continue
            
            # Create image URLs array (ordered by number)
            image_urls = [img['url'] for img in images]
            
            # Create new jersey entry
            jersey_entry = {
                'id': str(uuid.uuid4()),  # Generate random UUID
                'name': jersey_name,
                'price': '',  # Leave blank
                'description': '',  # Leave blank
                'images': json.dumps(image_urls),  # Proper JSON array format
                'collection_ids': '',  # Leave blank
                'capsule_ids': ''  # Leave blank
            }
            
            new_entries.append(jersey_entry)
            jerseys_processed += 1
            
            # Show first few image URLs for verification
            print(f"     ✅ Adding: {jersey_name}")
            print(f"        🖼️  Images: {len(image_urls)} files")
            for i, url in enumerate(image_urls[:3]):  # Show first 3
                print(f"           {i+1}. ...{url[-40:]}")
            if len(image_urls) > 3:
                print(f"           ... and {len(image_urls) - 3} more images")
        
        # Combine existing data with new entries
        all_jersey_data = existing_data + new_entries
        
        print(f"\n📊 Processing summary:")
        print(f"   📂 Existing entries: {len(existing_data)}")
        print(f"   ✅ New entries added: {jerseys_processed}")
        print(f"   ⏭️  Jerseys skipped (already exist): {jerseys_skipped}")
        print(f"   📋 Total entries: {len(all_jersey_data)}")
        
        if jerseys_processed == 0 and len(existing_data) == 0:
            print("❌ No jersey data to write")
            return False
        
        # Write CSV file
        print(f"\n📝 Writing to {csv_filename}...")
        
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['id', 'name', 'price', 'description', 'images', 'collection_ids', 'capsule_ids']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header
            writer.writeheader()
            
            # Write all data (existing + new)
            for jersey in all_jersey_data:
                writer.writerow(jersey)
        
        print(f"✅ Successfully updated {csv_filename}")
        
        # Display preview of new entries only
        if jerseys_processed > 0:
            print(f"\n📋 Preview of NEW entries added:")
            print("-" * 100)
            print(f"{'UUID':<36} {'Name':<30} {'Images':<15} {'Price':<8} {'Description'}")
            print("-" * 100)
            
            for jersey in new_entries[:5]:  # Show first 5 new entries
                images_count = len(json.loads(jersey['images'])) if jersey['images'] else 0
                uuid_short = jersey['id'][:8] + "..."
                name_short = jersey['name'][:28] + "..." if len(jersey['name']) > 28 else jersey['name']
                print(f"{uuid_short:<36} {name_short:<30} {images_count:<15} {jersey['price']:<8} {jersey['description']}")
            
            if len(new_entries) > 5:
                print(f"... and {len(new_entries) - 5} more new entries")
            
            print("-" * 100)
        else:
            print(f"\n💡 No new jerseys found - all S3 files already exist in CSV")
            print(f"   Your manual edits have been preserved!")
        
        return True
        
    except NoCredentialsError:
        print("❌ AWS credentials not found or invalid")
        return False
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucket':
            print(f"❌ Bucket '{bucket_name}' does not exist")
        elif error_code == 'AccessDenied':
            print(f"❌ Access denied to bucket '{bucket_name}'")
        else:
            print(f"❌ AWS Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function to run the generator"""
    if generate_jerseys_csv():
        print("")
        print("🎉 Jerseys CSV generation completed successfully!")
        print("💡 You can now upload this data to your database!")
    else:
        print("")
        print("🔧 Please fix the issues before proceeding.")

if __name__ == "__main__":
    main() 