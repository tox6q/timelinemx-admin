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
CAPSULE_CSV = 'capsule.csv'

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

def is_capsule_cover(filename: str, url: str) -> bool:
    """Check if filename/URL is a capsule cover image"""
    filename_lower = filename.lower()
    url_lower = url.lower()
    
    # Specific capsule pattern: _Coleccio%CC%81n_1_6alphanumeric
    # This is the exact pattern for capsule covers as provided by user
    if re.search(r'coleccio%cc%81n_1_[a-zA-Z0-9]{6}', url_lower):
        return True
    
    # Also check for variations without URL encoding
    if re.search(r'colección_1_[a-zA-Z0-9]{6}', url_lower) or \
       re.search(r'coleccion_1_[a-zA-Z0-9]{6}', url_lower):
        return True
    
    return False

def extract_capsule_name(filename: str) -> str:
    """Extract capsule name from filename"""
    # Remove file extension
    name_without_ext = os.path.splitext(filename)[0]
    
    # Handle URL decoding first
    name_without_ext = name_without_ext.replace('%CC%81', 'á')  # Convert URL encoding back to accent
    
    # Split by underscores and remove the last 2 parts (digit and 6-char code)
    parts = name_without_ext.split('_')
    
    # Remove last 2 parts if there are enough parts
    if len(parts) >= 2:
        # Check if last part is 6 alphanumeric chars and second-to-last is 1-2 digits
        if len(parts[-1]) == 6 and parts[-1].isalnum() and len(parts[-2]) <= 2 and parts[-2].isdigit():
            capsule_parts = parts[:-2]  # Remove last 2 parts
        else:
            capsule_parts = parts[:-1]  # Remove only last part
    else:
        capsule_parts = parts
    
    # Join back and clean up
    capsule_name = '_'.join(capsule_parts)
    capsule_name = capsule_name.replace('_', ' ')  # Replace underscores with spaces
    capsule_name = capsule_name.strip()
    
    # Remove any "Colección" variations (case-insensitive) - all possible spellings
    capsule_name = re.sub(r'\s*coleccián\s*', ' ', capsule_name, flags=re.IGNORECASE)
    capsule_name = re.sub(r'\s*colección\s*', ' ', capsule_name, flags=re.IGNORECASE)
    capsule_name = re.sub(r'\s*coleccion\s*', ' ', capsule_name, flags=re.IGNORECASE)
    capsule_name = re.sub(r'\s*coleccio.*?n\s*', ' ', capsule_name, flags=re.IGNORECASE)  # Catch any variation
    capsule_name = re.sub(r'\s+', ' ', capsule_name)  # Remove multiple spaces
    capsule_name = capsule_name.strip()
    
    # Final cleanup - remove any remaining single letters that might be artifacts
    capsule_name = re.sub(r'\s+[a-záéíóúüñ]\s*$', '', capsule_name, flags=re.IGNORECASE)
    capsule_name = capsule_name.strip()
    
    # Capitalize properly
    return capsule_name.title()

def create_slug(name: str) -> str:
    """Create URL-friendly slug from name"""
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)  # Remove special characters
    slug = re.sub(r'\s+', '-', slug)  # Replace spaces with hyphens
    slug = re.sub(r'-+', '-', slug)   # Replace multiple hyphens with single
    slug = slug.strip('-')            # Remove leading/trailing hyphens
    return slug

def get_capsule_covers() -> List[Dict]:
    """Get capsule cover images from Cloudinary"""
    try:
        print("🔍 Fetching all images and filtering for capsule covers...")
        
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
        
        # Filter for capsule covers only
        capsule_covers = []
        
        for image in all_images:
            public_id = image['public_id']
            filename = public_id.split("/")[-1]
            secure_url = image['secure_url']
            
            # Skip sample images
            if 'samples/' in public_id:
                continue
            
            # Check if this is a capsule cover
            if is_capsule_cover(filename, secure_url):
                capsule_name = extract_capsule_name(filename)
                
                capsule_covers.append({
                    'filename': filename,
                    'name': capsule_name,
                    'url': secure_url
                })
                print(f"🕰️  Found capsule: {capsule_name}")
        
        print(f"🕰️  Found {len(capsule_covers)} capsule covers")
        return capsule_covers
        
    except Exception as e:
        print(f"❌ Error fetching capsule images: {e}")
        return []

def load_existing_capsules() -> Dict[str, int]:
    """Load existing capsules from CSV and return name->id mapping"""
    existing_capsules = {}
    
    if os.path.exists(CAPSULE_CSV):
        try:
            with open(CAPSULE_CSV, 'r', encoding='utf-8', newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    existing_capsules[row['Name']] = int(row['id'])
            
            print(f"📋 Found {len(existing_capsules)} existing capsules in CSV")
        except Exception as e:
            print(f"⚠️ Error reading existing CSV: {e}")
    else:
        print("📋 No existing CSV found - will create new one")
    
    return existing_capsules

def save_capsules_to_csv(capsule_covers: List[Dict]):
    """Save capsules to CSV with auto-incrementing IDs"""
    if not capsule_covers:
        print("❌ No capsule covers found")
        return
    
    # Load existing capsules
    existing_capsules = load_existing_capsules()
    
    # Get next available ID
    next_id = max(existing_capsules.values()) + 1 if existing_capsules else 1
    
    # Prepare new capsules (avoid duplicates)
    new_capsules = []
    
    for cover in capsule_covers:
        name = cover['name']
        
        if name not in existing_capsules:
            slug = create_slug(name)
            
            new_capsules.append({
                'id': next_id,
                'Name': name,
                'slug': slug,
                'description': '',  # Blank as requested
                'cover': cover['url']
            })
            
            next_id += 1
    
    if not new_capsules:
        print("✅ No new capsules to add - all capsules already exist")
        return
    
    print(f"➕ Adding {len(new_capsules)} new capsules to CSV")
    
    # Determine if we're creating new file or appending
    file_exists = os.path.exists(CAPSULE_CSV)
    
    try:
        with open(CAPSULE_CSV, 'a' if file_exists else 'w', encoding='utf-8', newline='') as file:
            fieldnames = ['id', 'Name', 'slug', 'description', 'cover']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            # Write header only if creating new file
            if not file_exists:
                writer.writeheader()
            
            # Write new capsules
            for capsule in new_capsules:
                writer.writerow(capsule)
        
        print(f"✅ Successfully {'updated' if file_exists else 'created'} {CAPSULE_CSV}")
        
        # Print summary
        total_existing = len(existing_capsules)
        total_new = len(new_capsules)
        print(f"📊 Summary: {total_existing} existing + {total_new} new = {total_existing + total_new} total capsules")
        
        # Show what was added
        print(f"\n🕰️  New capsules added:")
        for capsule in new_capsules:
            print(f"   {capsule['id']}. {capsule['Name']} (slug: {capsule['slug']})")
            
    except Exception as e:
        print(f"❌ Error saving CSV: {e}")

def main():
    """Main function to extract capsule data from Cloudinary"""
    print("🕰️  TimelineMX Capsule Extractor")
    print("=" * 50)
    
    # Setup Cloudinary
    if not setup_cloudinary():
        return
    
    # Get capsule cover images
    capsule_covers = get_capsule_covers()
    
    if not capsule_covers:
        print("❌ No capsule covers found")
        print("\n💡 Make sure your capsule images contain words like:")
        print("   - capsula, capsule")
        print("   - tiempo, time")
        return
    
    # Save capsules to CSV
    save_capsules_to_csv(capsule_covers)
    
    print(f"\n🎉 Process completed successfully!")
    print(f"📄 Check {CAPSULE_CSV} for your capsule data")

if __name__ == "__main__":
    main() 