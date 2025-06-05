import os
import csv
import json
import uuid
import re
from typing import List, Dict, Set
import cloudinary
import cloudinary.api
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
PRODUCTS_CSV = 'products.csv'
DELETE_LIST_FILE = 'delete.txt'

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

def is_cover_image(filename: str) -> bool:
    """Check if filename is a cover image (not a jersey)"""
    filename_lower = filename.lower()
    
    # Specific cover pattern in URLs: Coleccio%CC%81n_1_6alphanumeric
    # This matches the actual URL format from Cloudinary (capsule covers)
    if re.search(r'coleccio%cc%81n_1_[a-zA-Z0-9]{6}', filename_lower):
        return True
    
    # Also check for variations and other formats (capsule covers)
    if re.search(r'coleccion_1_[a-zA-Z0-9]{6}', filename_lower) or \
       re.search(r'colección_1_[a-zA-Z0-9]{6}', filename_lower):
        return True
    
    # Collection covers pattern: contains ZXZX in filename
    if 'zxzx' in filename_lower:
        return True
    
    # More general patterns for other cover types
    cover_patterns = [
        'coleccio%cc%81n',  # URL encoded Colección (primary pattern)
        'colección',        # Spanish for collection
        'coleccion',        # Without accent
        'collection',       # English
        'cover',            # Cover images
        'portada',          # Spanish for cover
        'capsule',          # Time capsule
        'capsula',          # Spanish for capsule
    ]
    
    # Check if any cover pattern is in the filename/URL
    for pattern in cover_patterns:
        if pattern in filename_lower:
            return True
    
    return False

def extract_product_name(filename: str) -> str:
    """
    Extract product name from Cloudinary filename format: Product_name_X_XXXXXX
    Examples:
    - Valencia_1980-81_5_crxple -> Valencia 1980-81
    - Colo-Colo_2006_6_cwa7mo -> Colo-Colo 2006
    - Holanda_2010_12_xbngz5 -> Holanda 2010 (double digit)
    - Mexico_Blanca_98_mc3kua -> Mexico Blanca 98 (no digit)
    """
    # Remove file extension if present
    name_without_ext = os.path.splitext(filename)[0]
    
    # Pattern: Product_name_[optional 1-2 digits]_6alphanumeric
    # This handles: _digit_, _doubledigit_, or no digit at all before _6chars
    match = re.match(r'^(.+?)(?:_\d{1,2})?_[a-zA-Z0-9]{6}$', name_without_ext)
    
    if match:
        product_name = match.group(1)
        # Replace underscores with spaces
        product_name = product_name.replace('_', ' ')
        return product_name.strip()
    else:
        # Fallback: try to remove the last one or two underscore sections
        parts = name_without_ext.split('_')
        if len(parts) >= 2:
            # Check if last part is 6 alphanumeric characters
            if len(parts[-1]) == 6 and parts[-1].isalnum():
                # Check if second-to-last is 1-2 digits (optional)
                if len(parts) >= 3 and len(parts[-2]) <= 2 and parts[-2].isdigit():
                    # Has digit: remove last 2 parts
                    product_name = '_'.join(parts[:-2])
                else:
                    # No digit: remove only last part
                    product_name = '_'.join(parts[:-1])
                return product_name.replace('_', ' ').strip()
        
        # Final fallback: just replace underscores
        print(f"⚠️  Pattern didn't match for: {filename}")
        return name_without_ext.replace('_', ' ').strip()

def load_delete_list() -> Set[str]:
    """Load list of files to ignore from delete.txt"""
    delete_list = set()
    
    if os.path.exists(DELETE_LIST_FILE):
        try:
            with open(DELETE_LIST_FILE, 'r', encoding='utf-8') as file:
                for line in file:
                    filename = line.strip()
                    if filename:  # Skip empty lines
                        delete_list.add(filename)
            
            print(f"🗑️  Loaded {len(delete_list)} files to ignore from {DELETE_LIST_FILE}")
        except Exception as e:
            print(f"⚠️ Error reading {DELETE_LIST_FILE}: {e}")
    else:
        print(f"📋 No {DELETE_LIST_FILE} found - processing all files")
    
    return delete_list

def get_jersey_images_only() -> List[Dict]:
    """Get jersey images only (excluding covers and samples)"""
    try:
        print(f"🔍 Fetching ALL images and filtering for jerseys only...")
        
        all_images = []
        next_cursor = None
        
        while True:
            # Get all resources - no folder filter since they're mostly in ROOT
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
        
        # Filter for jersey images only
        jersey_images = []
        cover_count = 0
        sample_count = 0
        covers_found = []  # Track cover filenames for debugging
        
        for image in all_images:
            public_id = image['public_id']
            filename = public_id.split("/")[-1]  # Get filename
            secure_url = image['secure_url']  # Get full URL
            
            # Skip sample images (in samples folder)
            if 'samples/' in public_id:
                sample_count += 1
                continue
            
            # Check for cover images in BOTH filename AND full URL
            if is_cover_image(filename) or is_cover_image(secure_url):
                cover_count += 1
                covers_found.append(filename)
                continue
            
            jersey_images.append(image)
        
        print(f"👕 Filtered to {len(jersey_images)} jersey images")
        print(f"🖼️  Skipped {cover_count} cover images")
        print(f"📦 Skipped {sample_count} sample images")
        
        # Show first few covers that were skipped
        if covers_found:
            print(f"\n🖼️  Sample covers that were skipped:")
            for i, cover in enumerate(covers_found[:10]):
                print(f"      {i+1}. {cover}")
            if len(covers_found) > 10:
                print(f"      ... and {len(covers_found) - 10} more covers")
        
        return jersey_images
        
    except Exception as e:
        print(f"❌ Error fetching images: {e}")
        return []

def group_images_by_product(images: List[Dict], delete_list: Set[str]) -> Dict[str, Dict]:
    """Group images by product name and create product data"""
    products = {}
    skipped_count = 0
    duplicate_count = 0
    seen_combinations = set()  # Track (product_name, digit_number) combinations
    
    for image in images:
        # Get filename from public_id - using split method
        public_id = image['public_id']
        filename = public_id.split("/")[-1]  # Changed extraction method
        
        # Remove file extension for comparison with delete list
        filename_without_ext = os.path.splitext(filename)[0]
        
        # Skip if file is in delete list
        if filename_without_ext in delete_list:
            skipped_count += 1
            continue
        
        # Extract product name
        product_name = extract_product_name(filename)
        
        # Get the secure URL
        image_url = image['secure_url']
        
        # Extract digit number for sorting (if exists)
        # Pattern: Product_name_[digit]_6chars or Product_name_6chars
        digit_match = re.search(r'_(\d{1,2})_[a-zA-Z0-9]{6}$', filename_without_ext)
        digit_number = int(digit_match.group(1)) if digit_match else 999  # 999 for images without digit (put them last)
        
        # Check for duplicates: same product name + same position number
        combination_key = (product_name, digit_number)
        if combination_key in seen_combinations:
            duplicate_count += 1
            continue  # Skip this duplicate
        
        # Mark this combination as seen
        seen_combinations.add(combination_key)
        
        # Group by product name
        if product_name not in products:
            products[product_name] = {
                'id': str(uuid.uuid4()),
                'name': product_name,
                'price': '',
                'description': '',
                'images': [],  # Will store tuples of (digit, url) temporarily
                'collection_ids': '',
                'capsule_ids': ''
            }
        
        # Store image with its digit for sorting
        products[product_name]['images'].append((digit_number, image_url))
    
    # Sort images by digit number and extract URLs in ascending order
    for product_name, product_data in products.items():
        # Sort by digit number (ascending: 1, 2, 3, 4, 5, 6...)
        sorted_images = sorted(product_data['images'], key=lambda x: x[0])
        # Extract just the URLs
        product_data['images'] = [url for digit, url in sorted_images]
    
    print(f"🎯 Grouped into {len(products)} unique products")
    if skipped_count > 0:
        print(f"🗑️  Skipped {skipped_count} files from delete list")
    if duplicate_count > 0:
        print(f"🔄 Skipped {duplicate_count} duplicate images (same product + position)")
    return products

def load_existing_products() -> Set[str]:
    """Load existing product names from CSV"""
    existing_products = set()
    
    if os.path.exists(PRODUCTS_CSV):
        try:
            with open(PRODUCTS_CSV, 'r', encoding='utf-8', newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    existing_products.add(row['name'])
            
            print(f"📋 Found {len(existing_products)} existing products in CSV")
        except Exception as e:
            print(f"⚠️ Error reading existing CSV: {e}")
    else:
        print("📋 No existing CSV found - will create new one")
    
    return existing_products

def save_products_to_csv(products: Dict[str, Dict], existing_products: Set[str]):
    """Save new products to CSV"""
    new_products = {}
    
    # Filter out products that already exist
    for name, product in products.items():
        if name not in existing_products:
            new_products[name] = product
    
    if not new_products:
        print("✅ No new products to add - all products already in CSV")
        return
    
    print(f"➕ Adding {len(new_products)} new products to CSV")
    
    # Determine if we're creating new file or appending
    file_exists = os.path.exists(PRODUCTS_CSV)
    
    try:
        with open(PRODUCTS_CSV, 'a' if file_exists else 'w', encoding='utf-8', newline='') as file:
            fieldnames = ['id', 'name', 'price', 'description', 'images', 'collection_ids', 'capsule_ids']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            # Write header only if creating new file
            if not file_exists:
                writer.writeheader()
            
            # Write new products
            for product in new_products.values():
                # Convert images array to JSON string
                product_copy = product.copy()
                product_copy['images'] = json.dumps(product['images'])
                writer.writerow(product_copy)
        
        print(f"✅ Successfully {'updated' if file_exists else 'created'} {PRODUCTS_CSV}")
        
        # Print summary
        if file_exists:
            total_existing = len(existing_products)
            total_new = len(new_products)
            print(f"📊 Summary: {total_existing} existing + {total_new} new = {total_existing + total_new} total products")
        else:
            print(f"📊 Created CSV with {len(new_products)} products")
            
    except Exception as e:
        print(f"❌ Error saving CSV: {e}")

def main():
    """Main function to extract product data from Cloudinary"""
    print("🚀 TimelineMX Jersey Extractor (Fixed)")
    print("=" * 50)
    
    # Setup Cloudinary
    if not setup_cloudinary():
        return
    
    # Get jersey images only (filtered)
    images = get_jersey_images_only()
    if not images:
        print("❌ No jersey images found")
        return
    
    # Load delete list
    delete_list = load_delete_list()
    
    # Group images by product
    products = group_images_by_product(images, delete_list)
    
    # Load existing products
    existing_products = load_existing_products()
    
    # Save new products to CSV
    save_products_to_csv(products, existing_products)
    
    print("\n🎉 Process completed successfully!")
    print(f"📄 Check {PRODUCTS_CSV} for your product data")
    print("\nNext steps:")
    print("1. Review the CSV file")
    print("2. Fill in price, description, collection_ids, and capsule_ids")
    print("3. Import to your database")

if __name__ == "__main__":
    main() 