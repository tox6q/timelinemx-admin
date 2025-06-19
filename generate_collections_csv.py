import os
import boto3
import csv
import re
import unicodedata
from urllib.parse import quote
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def normalize_string(s):
    """Normalize string to ASCII, removing accents and special characters."""
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn').lower()

def load_existing_csv(csv_filename):
    """Load existing CSV data to preserve manual edits"""
    existing_data = []
    existing_urls = set()
    next_id = 1
    
    if os.path.exists(csv_filename):
        print(f"📂 Found existing {csv_filename}, loading data...")
        try:
            with open(csv_filename, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    existing_data.append(row)
                    existing_urls.add(row['cover'])
                    next_id = max(next_id, int(row['id']) + 1)
            print(f"   ✅ Loaded {len(existing_data)} existing entries")
        except Exception as e:
            print(f"   ⚠️  Error reading existing CSV: {e}")
            print(f"   📝 Will create fresh CSV file")
    else:
        print(f"📝 No existing {csv_filename} found, creating new file")
    
    return existing_data, existing_urls, next_id

def generate_collections_csv():
    """Generate collections.csv from AWS S3 portada-collections folder (incremental updates)"""
    
    print("🎯 Generating collections.csv from AWS S3 (incremental)")
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
        csv_filename = 'collections.csv'
        existing_data, existing_urls, next_id = load_existing_csv(csv_filename)
        
        # List objects in portada-collections folder
        print("🔍 Scanning portada-collections folder for new files...")
        
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix='portada-collections/'
        )
        
        if 'Contents' not in response:
            print("❌ No files found in portada-collections folder")
            return False
        
        # Process files
        new_entries = []
        files_processed = 0
        files_skipped = 0
        
        for obj in response['Contents']:
            key = obj['Key']
            
            # Skip folder markers and non-image files
            if key.endswith('/') or not key.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
            
            # Extract filename from key (remove portada-collections/ prefix)
            filename = key.replace('portada-collections/', '')
            
            # Process the filename to extract clean name
            # Remove " Collection ZXZX (1)" and file extension
            clean_name = filename
            
            # Remove file extension
            clean_name = os.path.splitext(clean_name)[0]
            
            # Process filename to extract clean name
            print(f"   📷 Processing: {filename}")
            
            # Remove unwanted patterns from collections naming
            # Pattern: "Premier League Collection ZXZX (1)" -> "Premier League"
            
            # First, remove " (number)" pattern
            clean_name = re.sub(r'\s*\(\d+\)$', '', clean_name)
            
            # Remove "ZXZX" pattern (case insensitive)
            clean_name = re.sub(r'\s+ZXZX\s*', ' ', clean_name, flags=re.IGNORECASE)
            
            # Remove "Collection" or "Colección" (case insensitive)
            clean_name = re.sub(r'\s+Collection\s*', ' ', clean_name, flags=re.IGNORECASE)
            clean_name = re.sub(r'\s+Colección\s*', ' ', clean_name, flags=re.IGNORECASE)
            
            # Clean up extra spaces
            clean_name = ' '.join(clean_name.split())
            clean_name = clean_name.strip()
            
            # Generate slug: normalize to ASCII, lowercase, spaces to hyphens, add "-coleccion"
            slug = normalize_string(clean_name).replace(' ', '-') + '-coleccion'
            
            # Generate description: leave blank as requested
            description = ''
            
            # Generate S3 URL (use regional endpoint with proper URL encoding)
            encoded_key = quote(key, safe='/')  # Encode everything except forward slashes
            cover_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{encoded_key}"
            
            # Check if this URL already exists in the CSV
            if cover_url in existing_urls:
                print(f"     ⏭️  Skipping existing: {clean_name}")
                files_skipped += 1
                continue
            
            # Create new collection entry
            collection_entry = {
                'id': next_id + files_processed,
                'Name': clean_name,
                'slug': slug,
                'description': description,
                'cover': cover_url
            }
            
            new_entries.append(collection_entry)
            files_processed += 1
            
            print(f"     ✅ Adding new: {clean_name} | {slug}")
        
        # Combine existing data with new entries
        all_collection_data = existing_data + new_entries
        
        print(f"\n📊 Processing summary:")
        print(f"   📂 Existing entries: {len(existing_data)}")
        print(f"   ✅ New entries added: {files_processed}")
        print(f"   ⏭️  Files skipped (already exist): {files_skipped}")
        print(f"   📋 Total entries: {len(all_collection_data)}")
        
        if files_processed == 0 and len(existing_data) == 0:
            print("❌ No collection data to write")
            return False
        
        # Write CSV file
        print(f"\n📝 Writing to {csv_filename}...")
        
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['id', 'Name', 'slug', 'description', 'cover']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header
            writer.writeheader()
            
            # Write all data (existing + new)
            for collection in all_collection_data:
                writer.writerow(collection)
        
        print(f"✅ Successfully updated {csv_filename}")
        
        # Display preview of new entries only
        if files_processed > 0:
            print(f"\n📋 Preview of NEW entries added:")
            print("-" * 80)
            print(f"{'ID':<3} {'Name':<25} {'Slug':<30} {'Description':<30} {'Cover URL'}")
            print("-" * 80)
            
            for collection in new_entries[:5]:  # Show first 5 new entries
                cover_short = collection['cover'][-50:] if len(collection['cover']) > 50 else collection['cover']
                print(f"{collection['id']:<3} {collection['Name']:<25} {collection['slug']:<30} {collection['description']:<30} ...{cover_short}")
            
            if len(new_entries) > 5:
                print(f"... and {len(new_entries) - 5} more new entries")
            
            print("-" * 80)
        else:
            print(f"\n💡 No new files found - all S3 files already exist in CSV")
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
    if generate_collections_csv():
        print("")
        print("🎉 Collections CSV generation completed successfully!")
        print("💡 You can now upload this data to your database!")
    else:
        print("")
        print("🔧 Please fix the issues before proceeding.")

if __name__ == "__main__":
    main() 