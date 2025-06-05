import os
import cloudinary
import cloudinary.api
from dotenv import load_dotenv
from collections import defaultdict

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

def analyze_all_folders():
    """Analyze all folders and their contents in Cloudinary"""
    try:
        print("🔍 Analyzing ALL Cloudinary folders and images...")
        
        # Get all resources (no folder filter)
        all_images = []
        next_cursor = None
        
        while True:
            result = cloudinary.api.resources(
                type="upload",
                max_results=500,
                next_cursor=next_cursor
            )
            
            images = result.get('resources', [])
            all_images.extend(images)
            
            next_cursor = result.get('next_cursor')
            if not next_cursor:
                break
        
        print(f"📸 Found {len(all_images)} total images in Cloudinary")
        
        # Group by folder
        folders = defaultdict(list)
        
        for image in all_images:
            public_id = image['public_id']
            
            # Extract folder from public_id
            if '/' in public_id:
                folder = '/'.join(public_id.split('/')[:-1])  # Everything except filename
                filename = public_id.split('/')[-1]
            else:
                folder = "ROOT"  # Images in root directory
                filename = public_id
            
            folders[folder].append({
                'filename': filename,
                'public_id': public_id,
                'url': image['secure_url']
            })
        
        # Print analysis
        print("\n" + "="*80)
        print("📁 FOLDER ANALYSIS")
        print("="*80)
        
        for folder, images in sorted(folders.items()):
            print(f"\n🗂️  Folder: {folder}")
            print(f"   📊 Image count: {len(images)}")
            print(f"   📋 Sample files:")
            
            # Show first 5 files as samples
            for i, img in enumerate(images[:5]):
                print(f"      {i+1}. {img['filename']}")
            
            if len(images) > 5:
                print(f"      ... and {len(images) - 5} more files")
        
        return folders
        
    except Exception as e:
        print(f"❌ Error analyzing folders: {e}")
        return {}

def get_jerseys_only():
    """Get images from jerseys folder only"""
    try:
        print("\n" + "="*80)
        print("👕 JERSEYS FOLDER ONLY")
        print("="*80)
        
        # Specific folder extraction
        jerseys_images = []
        next_cursor = None
        
        while True:
            result = cloudinary.api.resources(
                type="upload",
                asset_folder="TimelineMX/jerseys",  # Specific folder
                max_results=500,
                next_cursor=next_cursor
            )
            
            images = result.get('resources', [])
            jerseys_images.extend(images)
            
            next_cursor = result.get('next_cursor')
            if not next_cursor:
                break
        
        print(f"👕 Found {len(jerseys_images)} images in jerseys folder")
        
        # Show samples
        print("\n📋 Sample jersey files:")
        for i, img in enumerate(jerseys_images[:10]):
            filename = img['public_id'].split('/')[-1]
            print(f"   {i+1}. {filename}")
        
        if len(jerseys_images) > 10:
            print(f"   ... and {len(jerseys_images) - 10} more files")
        
        return jerseys_images
        
    except Exception as e:
        print(f"❌ Error getting jerseys: {e}")
        return []

def get_covers_folders():
    """Get images from cover folders (portada-capsulas, portada-collection)"""
    try:
        print("\n" + "="*80)
        print("🖼️  COVER FOLDERS")
        print("="*80)
        
        cover_folders = ["TimelineMX/portada-capsulas", "TimelineMX/portada-collection"]
        all_covers = {}
        
        for folder in cover_folders:
            try:
                covers = []
                next_cursor = None
                
                while True:
                    result = cloudinary.api.resources(
                        type="upload",
                        asset_folder=folder,
                        max_results=500,
                        next_cursor=next_cursor
                    )
                    
                    images = result.get('resources', [])
                    covers.extend(images)
                    
                    next_cursor = result.get('next_cursor')
                    if not next_cursor:
                        break
                
                all_covers[folder] = covers
                print(f"🖼️  {folder}: {len(covers)} images")
                
                # Show samples
                for i, img in enumerate(covers[:5]):
                    filename = img['public_id'].split('/')[-1]
                    print(f"      {i+1}. {filename}")
                
                if len(covers) > 5:
                    print(f"      ... and {len(covers) - 5} more files")
                    
            except Exception as e:
                print(f"⚠️  Could not access {folder}: {e}")
        
        return all_covers
        
    except Exception as e:
        print(f"❌ Error getting covers: {e}")
        return {}

def main():
    """Main debug function"""
    print("🐛 TimelineMX Cloudinary Folder Debugger")
    print("=" * 50)
    
    # Setup Cloudinary
    if not setup_cloudinary():
        return
    
    # Analyze all folders
    all_folders = analyze_all_folders()
    
    # Get jerseys specifically
    jerseys = get_jerseys_only()
    
    # Get covers specifically
    covers = get_covers_folders()
    
    # Summary
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    print(f"Total folders found: {len(all_folders)}")
    print(f"Jersey images: {len(jerseys)}")
    print(f"Cover folders analyzed: {len(covers)}")
    
    print("\n💡 RECOMMENDATIONS:")
    print("1. Use asset_folder='TimelineMX/jerseys' for products only")
    print("2. Use asset_folder='TimelineMX/portada-capsulas' for capsule covers")
    print("3. Use asset_folder='TimelineMX/portada-collection' for collection covers")

if __name__ == "__main__":
    main() 