import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_aws_connection():
    """Test AWS S3 connection and list buckets/files"""
    
    print("🔧 AWS S3 Connection Test")
    print("=" * 50)
    
    # Get AWS credentials from environment
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    region = os.getenv('AWS_REGION', 'us-east-1')  # Default to us-east-1
    bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
    
    # Check if credentials are provided
    if not access_key or not secret_key:
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
        
        print(f"✅ AWS S3 client created successfully")
        print(f"   Region: {region}")
        print("")
        
        # Test connection by listing buckets
        print("📋 Listing all available buckets:")
        response = s3_client.list_buckets()
        
        buckets = response.get('Buckets', [])
        if not buckets:
            print("   No buckets found")
        else:
            for i, bucket in enumerate(buckets, 1):
                print(f"   {i}. {bucket['Name']} (Created: {bucket['CreationDate'].strftime('%Y-%m-%d')})")
        
        print("")
        
        # If specific bucket is configured, explore it
        if bucket_name:
            print(f"🔍 Exploring bucket: {bucket_name}")
            explore_bucket(s3_client, bucket_name)
        else:
            print("💡 To explore a specific bucket, add AWS_S3_BUCKET_NAME to your .env file")
            
    except NoCredentialsError:
        print("❌ AWS credentials not found or invalid")
        return False
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'InvalidAccessKeyId':
            print("❌ Invalid AWS Access Key ID")
        elif error_code == 'SignatureDoesNotMatch':
            print("❌ Invalid AWS Secret Access Key")
        elif error_code == 'AccessDenied':
            print("❌ Access denied - check your AWS permissions")
        else:
            print(f"❌ AWS Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

def explore_bucket(s3_client, bucket_name):
    """Explore the contents of a specific bucket"""
    try:
        # Check if bucket exists and we have access
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✅ Successfully connected to bucket: {bucket_name}")
        print("")
        
        # List all objects in the bucket (handle pagination)
        print("📁 Exploring folder structure:")
        
        # Get ALL objects using pagination
        all_objects = []
        continuation_token = None
        
        while True:
            if continuation_token:
                response = s3_client.list_objects_v2(
                    Bucket=bucket_name,
                    ContinuationToken=continuation_token
                )
            else:
                response = s3_client.list_objects_v2(Bucket=bucket_name)
            
            if 'Contents' in response:
                all_objects.extend(response['Contents'])
            
            if response.get('IsTruncated'):
                continuation_token = response.get('NextContinuationToken')
            else:
                break
        
        if not all_objects:
            print("   📂 Bucket is empty")
            return
        
        print(f"   🔍 Found {len(all_objects)} total objects")
        print("")
        
        # Organize files by folder
        folders = {}
        root_files = []
        
        for obj in all_objects:
            key = obj['Key']
            size = obj['Size']
            modified = obj['LastModified'].strftime('%Y-%m-%d %H:%M')
            
            if '/' in key:
                # File is in a folder
                folder = key.split('/')[0]
                filename = key.split('/')[-1]
                
                if folder not in folders:
                    folders[folder] = []
                
                if filename:  # Not just a folder marker
                    folders[folder].append({
                        'name': filename,
                        'size': size,
                        'modified': modified,
                        'full_path': key
                    })
            else:
                # File is in root
                root_files.append({
                    'name': key,
                    'size': size,
                    'modified': modified
                })
        
        # Display root files
        if root_files:
            print("   📄 Root files:")
            for file in root_files[:10]:  # Show first 10
                print(f"      {file['name']} ({format_file_size(file['size'])}) - {file['modified']}")
            if len(root_files) > 10:
                print(f"      ... and {len(root_files) - 10} more files")
            print("")
        
        # Check for folder markers (empty folders)
        folder_markers = set()
        for obj in all_objects:
            key = obj['Key']
            if key.endswith('/') and obj['Size'] == 0:
                folder_name = key.rstrip('/')
                folder_markers.add(folder_name)
                print(f"   📁 {folder_name}/ (empty folder marker)")
        
        if folder_markers:
            print("")
        
        # Display folders and their contents
        if folders:
            for folder_name, files in folders.items():
                print(f"   📁 {folder_name}/ ({len(files)} files)")
                
                # Show first 5 files in each folder
                for file in files[:5]:
                    print(f"      📷 {file['name']} ({format_file_size(file['size'])}) - {file['modified']}")
                
                if len(files) > 5:
                    print(f"      ... and {len(files) - 5} more files")
                print("")
        
        # Show folders that exist but have no files
        all_folder_names = set(folders.keys()) | folder_markers
        if not all_folder_names:
            print("   📂 No folders detected - all files are in root")
        elif len(all_folder_names) != len(folders):
            empty_folders = folder_markers - set(folders.keys())
            if empty_folders:
                print(f"   📂 Empty folders detected: {', '.join(empty_folders)}")
                print("")
        
        # Summary
        total_files = len(root_files) + sum(len(files) for files in folders.values())
        print(f"📊 Summary:")
        print(f"   Total files: {total_files}")
        print(f"   Folders: {len(folders)}")
        print(f"   Root files: {len(root_files)}")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucket':
            print(f"❌ Bucket '{bucket_name}' does not exist")
        elif error_code == 'AccessDenied':
            print(f"❌ Access denied to bucket '{bucket_name}'")
        else:
            print(f"❌ Error accessing bucket: {e}")
    except Exception as e:
        print(f"❌ Unexpected error exploring bucket: {e}")

def format_file_size(size_bytes):
    """Convert bytes to human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    sizes = ['B', 'KB', 'MB', 'GB']
    i = 0
    while size_bytes >= 1024 and i < len(sizes) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {sizes[i]}"

def main():
    """Main function to run the test"""
    if test_aws_connection():
        print("")
        print("🎉 AWS S3 connection test completed successfully!")
        print("💡 You're ready to proceed with the migration!")
    else:
        print("")
        print("🔧 Please fix the connection issues before proceeding.")

if __name__ == "__main__":
    main() 