import os
import csv
import re
from typing import List, Dict
import cloudinary
import cloudinary.api
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
COLLECTIONS_CSV = 'collections.csv'

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

def is_collection_cover(filename: str, url: str) -> bool:
    """Check if filename/URL is a collection cover image"""
    filename_lower = filename.lower()
    url_lower = url.lower()
    
    # Specific collection pattern: contains ZXZX in filename
    if 'zxzx' in filename_lower or 'zxzx' in url_lower:
        return True
    
    return False

def extract_collection_name(filename: str) -> str:
    """Extract collection name from filename"""
    # Remove file extension
    name_without_ext = os.path.splitext(filename)[0]
    
    # Handle URL decoding first
    name_without_ext = name_without_ext.replace('%CC%81', 'á')  # Convert URL encoding back to accent
    
    # Remove the ZXZX pattern and anything after it
    # Pattern: Name_ZXZX or Name_something_ZXZX
    parts = name_without_ext.split('_')
    
    # Find where ZXZX appears and take everything before it
    collection_parts = []
    for part in parts:
        if part.upper() == 'ZXZX':
            break
        collection_parts.append(part)
    
    if collection_parts:
        collection_name = '_'.join(collection_parts)
    else:
        # Fallback: remove common patterns
        match = re.match(r'^(.+?)(?:_zxzx.*)?$', name_without_ext, re.IGNORECASE)
        if match:
            collection_name = match.group(1)
        else:
            collection_name = name_without_ext
    
    # Clean up the name
    collection_name = collection_name.replace('_', ' ')  # Replace underscores with spaces
    collection_name = collection_name.strip()
    
    # Capitalize properly
    return collection_name.title()

def create_slug(name: str) -> str:
    """Create URL-friendly slug from name"""
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)  # Remove special characters
    slug = re.sub(r'\s+', '-', slug)  # Replace spaces with hyphens
    slug = re.sub(r'-+', '-', slug)   # Replace multiple hyphens with single
    slug = slug.strip('-')            # Remove leading/trailing hyphens
    return slug

def get_collection_covers() -> List[Dict]:
    """Get collection cover images from Cloudinary"""
    try:
        print("🔍 Fetching all images and filtering for collection covers...")
        
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
        
        # Filter for collection covers only
        collection_covers = []
        
        for image in all_images:
            public_id = image['public_id']
            filename = public_id.split("/")[-1]
            secure_url = image['secure_url']
            
            # Skip sample images
            if 'samples/' in public_id:
                continue
            
            # Check if this is a collection cover
            if is_collection_cover(filename, secure_url):
                collection_name = extract_collection_name(filename)
                
                collection_covers.append({
                    'filename': filename,
                    'name': collection_name,
                    'url': secure_url
                })
                print(f"⚽ Found collection: {collection_name}")
        
        print(f"⚽ Found {len(collection_covers)} collection covers")
        return collection_covers
        
    except Exception as e:
        print(f"❌ Error fetching collection images: {e}")
        return []

def load_existing_collections() -> Dict[str, int]:
    """Load existing collections from CSV and return name->id mapping"""
    existing_collections = {}
    
    if os.path.exists(COLLECTIONS_CSV):
        try:
            with open(COLLECTIONS_CSV, 'r', encoding='utf-8', newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    existing_collections[row['Name']] = int(row['id'])
            
            print(f"📋 Found {len(existing_collections)} existing collections in CSV")
        except Exception as e:
            print(f"⚠️ Error reading existing CSV: {e}")
    else:
        print("📋 No existing CSV found - will create new one")
    
    return existing_collections

def save_collections_to_csv(collection_covers: List[Dict]):
    """Save collections to CSV with auto-incrementing IDs"""
    if not collection_covers:
        print("❌ No collection covers found")
        return
    
    # Load existing collections
    existing_collections = load_existing_collections()
    
    # Get next available ID
    next_id = max(existing_collections.values()) + 1 if existing_collections else 1
    
    # Prepare new collections (avoid duplicates)
    new_collections = []
    
    for cover in collection_covers:
        name = cover['name']
        
        if name not in existing_collections:
            slug = create_slug(name)
            
            new_collections.append({
                'id': next_id,
                'Name': name,
                'slug': slug,
                'description': '',  # Blank as requested
                'cover': cover['url']
            })
            
            next_id += 1
    
    if not new_collections:
        print("✅ No new collections to add - all collections already exist")
        return
    
    print(f"➕ Adding {len(new_collections)} new collections to CSV")
    
    # Determine if we're creating new file or appending
    file_exists = os.path.exists(COLLECTIONS_CSV)
    
    try:
        with open(COLLECTIONS_CSV, 'a' if file_exists else 'w', encoding='utf-8', newline='') as file:
            fieldnames = ['id', 'Name', 'slug', 'description', 'cover']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            # Write header only if creating new file
            if not file_exists:
                writer.writeheader()
            
            # Write new collections
            for collection in new_collections:
                writer.writerow(collection)
        
        print(f"✅ Successfully {'updated' if file_exists else 'created'} {COLLECTIONS_CSV}")
        
        # Print summary
        total_existing = len(existing_collections)
        total_new = len(new_collections)
        print(f"📊 Summary: {total_existing} existing + {total_new} new = {total_existing + total_new} total collections")
        
        # Show what was added
        print(f"\n⚽ New collections added:")
        for collection in new_collections:
            print(f"   {collection['id']}. {collection['Name']} (slug: {collection['slug']})")
            
    except Exception as e:
        print(f"❌ Error saving CSV: {e}")

def main():
    """Main function to extract collection data from Cloudinary"""
    print("⚽ TimelineMX Collections Extractor")
    print("=" * 50)
    
    # Setup Cloudinary
    if not setup_cloudinary():
        return
    
    # Get collection cover images
    collection_covers = get_collection_covers()
    
    if not collection_covers:
        print("❌ No collection covers found")
        print("\n💡 Make sure your collection images contain 'ZXZX' in the filename")
        return
    
    # Save collections to CSV
    save_collections_to_csv(collection_covers)
    
    print(f"\n🎉 Process completed successfully!")
    print(f"📄 Check {COLLECTIONS_CSV} for your collection data")

if __name__ == "__main__":
    main() 