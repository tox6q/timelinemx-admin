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
CLOUDINARY_FOLDER = 'TimelineMX/jerseys'
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

def get_cloudinary_images() -> List[Dict]:
    """Get all images from the jerseys folder in Cloudinary"""
    try:
        print(f"🔍 Fetching images from {CLOUDINARY_FOLDER} folder...")
        
        all_images = []
        next_cursor = None
        
        while True:
            # Get all resources from the jerseys folder - using asset_folder
            result = cloudinary.api.resources(
                type="upload",
                asset_folder=CLOUDINARY_FOLDER,  # Changed from prefix
                max_results=500,  # Cloudinary API limit per request
                next_cursor=next_cursor
            )
            
            images = result.get('resources', [])
            all_images.extend(images)
            
            # Check if there are more images
            next_cursor = result.get('next_cursor')
            if not next_cursor:
                break
        
        print(f"📸 Found {len(all_images)} images in Cloudinary")
        return all_images
        
    except Exception as e:
        print(f"❌ Error fetching Cloudinary images: {e}")
        return []

def group_images_by_product(images: List[Dict], delete_list: Set[str]) -> Dict[str, Dict]:
    """Group images by product name and create product data"""
    products = {}
    skipped_count = 0
    
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
    print("🚀 TimelineMX Cloudinary Product Extractor")
    print("=" * 50)
    
    # Setup Cloudinary
    if not setup_cloudinary():
        return
    
    # Get all images from Cloudinary
    images = get_cloudinary_images()
    if not images:
        print("❌ No images found or error accessing Cloudinary")
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
