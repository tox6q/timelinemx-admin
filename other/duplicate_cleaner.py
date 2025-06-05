import os
import re
from collections import defaultdict
from typing import List, Dict, Set
import cloudinary
import cloudinary.api
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
CLOUDINARY_FOLDER = 'TimelineMX/jerseys'

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

def extract_base_identifier(filename: str) -> str:
    """
    Extract base identifier (everything except the 6-digit code)
    Examples:
    - Valencia_1980-81_5_crxple -> Valencia_1980-81_5
    - Santos_2012_Visita_4_bzsbbn -> Santos_2012_Visita_4
    """
    # Remove file extension if present
    name_without_ext = os.path.splitext(filename)[0]
    
    # Pattern: everything before the last _6letters
    match = re.match(r'^(.+)_[a-zA-Z]{6}$', name_without_ext)
    
    if match:
        return match.group(1)
    else:
        # If pattern doesn't match, return the whole name
        return name_without_ext

def get_all_images() -> List[Dict]:
    """Get all images from the jerseys folder"""
    try:
        print(f"🔍 Fetching all images from {CLOUDINARY_FOLDER} folder...")
        
        all_images = []
        next_cursor = None
        
        while True:
            # Get resources with pagination - using asset_folder instead of prefix
            result = cloudinary.api.resources(
                type="upload",
                asset_folder=CLOUDINARY_FOLDER,  # Changed from prefix
                max_results=500,
                next_cursor=next_cursor
            )
            
            images = result.get('resources', [])
            all_images.extend(images)
            
            # Check if there are more images
            next_cursor = result.get('next_cursor')
            if not next_cursor:
                break
        
        print(f"📸 Found {len(all_images)} total images")
        return all_images
        
    except Exception as e:
        print(f"❌ Error fetching images: {e}")
        return []

def find_duplicates(images: List[Dict]) -> Dict[str, List[Dict]]:
    """Find duplicate images based on base identifier"""
    grouped_images = defaultdict(list)
    
    for image in images:
        # Get filename from public_id - using split method like your working code
        public_id = image['public_id']
        filename = public_id.split("/")[-1]  # Changed extraction method
        
        # Get base identifier
        base_id = extract_base_identifier(filename)
        
        # Add image info with filename for easier handling
        image_info = image.copy()
        image_info['filename'] = filename
        
        grouped_images[base_id].append(image_info)
    
    # Filter to only groups with duplicates (more than 1 image)
    duplicates = {base_id: images for base_id, images in grouped_images.items() if len(images) > 1}
    
    return duplicates

def display_duplicates(duplicates: Dict[str, List[Dict]]):
    """Display found duplicates for review"""
    if not duplicates:
        print("✅ No duplicates found!")
        return
    
    print(f"\n🔍 Found {len(duplicates)} groups with duplicates:")
    print("=" * 60)
    
    total_duplicates = 0
    for base_id, images in duplicates.items():
        print(f"\n📋 Base: {base_id}")
        print(f"   Duplicates: {len(images)} files")
        
        for i, img in enumerate(images, 1):
            print(f"   {i}. {img['filename']}")
            print(f"      Size: {img.get('bytes', 0):,} bytes")
            print(f"      Created: {img.get('created_at', 'Unknown')}")
        
        total_duplicates += len(images) - 1  # -1 because we keep one
    
    print(f"\n📊 Summary:")
    print(f"   - {len(duplicates)} groups with duplicates")
    print(f"   - {total_duplicates} files to be deleted")
    print(f"   - Will keep {len(duplicates)} files (newest in each group)")

def delete_duplicates(duplicates: Dict[str, List[Dict]], dry_run: bool = True):
    """Delete duplicate images, keeping the newest in each group"""
    if not duplicates:
        print("✅ No duplicates to delete!")
        return
    
    total_deleted = 0
    
    for base_id, images in duplicates.items():
        # Sort by creation date, keep the newest (last)
        sorted_images = sorted(images, key=lambda x: x.get('created_at', ''))
        to_keep = sorted_images[-1]  # Keep the newest
        to_delete = sorted_images[:-1]  # Delete the rest
        
        print(f"\n📋 Processing: {base_id}")
        print(f"   ✅ Keeping: {to_keep['filename']} (newest)")
        
        for img in to_delete:
            if dry_run:
                print(f"   🗑️  Would delete: {img['filename']}")
            else:
                try:
                    cloudinary.api.delete_resources([img['public_id']])
                    print(f"   ✅ Deleted: {img['filename']}")
                    total_deleted += 1
                except Exception as e:
                    print(f"   ❌ Error deleting {img['filename']}: {e}")
    
    if dry_run:
        print(f"\n🔍 DRY RUN COMPLETE - No files were actually deleted")
        print(f"   Would delete {sum(len(images) - 1 for images in duplicates.values())} files")
    else:
        print(f"\n✅ DELETION COMPLETE")
        print(f"   Successfully deleted {total_deleted} duplicate files")

def main():
    """Main function to find and clean duplicate images"""
    print("🧹 TimelineMX Duplicate Cleaner")
    print("=" * 50)
    
    # Setup Cloudinary
    if not setup_cloudinary():
        return
    
    # Get all images
    images = get_all_images()
    if not images:
        print("❌ No images found")
        return
    
    # Find duplicates
    duplicates = find_duplicates(images)
    
    # Display duplicates
    display_duplicates(duplicates)
    
    if duplicates:
        print("\n" + "=" * 50)
        print("⚠️  REVIEW THE DUPLICATES ABOVE")
        print("   The script will keep the NEWEST file in each group")
        print("   and delete the older ones.")
        
        # Ask for confirmation
        response = input("\nDo you want to proceed? (y/N): ").strip().lower()
        
        if response == 'y':
            # Ask for dry run first
            dry_response = input("Start with a dry run? (Y/n): ").strip().lower()
            dry_run = dry_response != 'n'
            
            delete_duplicates(duplicates, dry_run=dry_run)
            
            if dry_run:
                print("\n💡 To actually delete files, run again and choose 'n' for dry run")
        else:
            print("❌ Operation cancelled")

if __name__ == "__main__":
    main() 