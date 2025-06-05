import os
import cloudinary
import cloudinary.api
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_cloudinary():
    """Configure Cloudinary with API credentials"""
    try:
        cloudinary.config(
            cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
            api_key=os.getenv('CLOUDINARY_API_KEY'),
            api_secret=os.getenv('CLOUDINARY_API_SECRET')
        )
        print("✅ Cloudinary configured successfully")
        return True
    except Exception as e:
        print(f"❌ Error configuring Cloudinary: {e}")
        return False

def load_files_to_delete():
    """Load the list of files to delete from delete.txt"""
    if not os.path.exists('delete.txt'):
        print("❌ delete.txt file not found")
        return []
    
    try:
        with open('delete.txt', 'r', encoding='utf-8') as file:
            files = [line.strip() for line in file if line.strip()]
        print(f"📋 Found {len(files)} files to delete")
        return files
    except Exception as e:
        print(f"❌ Error reading delete.txt: {e}")
        return []

def delete_files(files_to_delete, dry_run=True):
    """Delete the specified files from Cloudinary"""
    if not files_to_delete:
        print("❌ No files to delete")
        return
    
    print(f"🗑️  {'DRY RUN - Would delete' if dry_run else 'Deleting'} {len(files_to_delete)} files:")
    
    deleted_count = 0
    failed_count = 0
    
    for file_id in files_to_delete:
        print(f"   - {file_id}")
        
        if not dry_run:
            try:
                result = cloudinary.api.delete_resources([file_id])
                if result.get('deleted', {}).get(file_id) == 'deleted':
                    deleted_count += 1
                else:
                    failed_count += 1
                    print(f"     ❌ Failed to delete {file_id}")
            except Exception as e:
                failed_count += 1
                print(f"     ❌ Error deleting {file_id}: {e}")
    
    if dry_run:
        print(f"\n🔍 DRY RUN COMPLETE")
        print(f"   Would attempt to delete {len(files_to_delete)} files")
    else:
        print(f"\n✅ DELETION COMPLETE")
        print(f"   Successfully deleted: {deleted_count}")
        print(f"   Failed to delete: {failed_count}")

def main():
    """Main function to clean up Cloudinary sample files"""
    print("🧹 Cloudinary Sample Files Cleanup")
    print("=" * 40)
    
    # Setup Cloudinary
    if not setup_cloudinary():
        return
    
    # Load files to delete
    files_to_delete = load_files_to_delete()
    if not files_to_delete:
        return
    
    # Show what will be deleted
    delete_files(files_to_delete, dry_run=True)
    
    # Ask for confirmation
    print("\n" + "=" * 40)
    print("⚠️  WARNING: This will permanently delete these files from Cloudinary!")
    response = input("Do you want to proceed with deletion? (y/N): ").strip().lower()
    
    if response == 'y':
        delete_files(files_to_delete, dry_run=False)
    else:
        print("❌ Deletion cancelled")

if __name__ == "__main__":
    main() 