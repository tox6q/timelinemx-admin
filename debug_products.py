import csv
import json
from typing import List, Dict

def read_csv_file(filename: str) -> List[Dict]:
    """Read CSV file and return list of dictionaries"""
    data = []
    with open(filename, 'r', encoding='utf-8', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Clean empty strings to None for proper database insertion
            cleaned_row = {}
            for key, value in row.items():
                cleaned_row[key] = value if value.strip() else None
            data.append(cleaned_row)
    return data

def process_products_data(products: List[Dict]) -> List[Dict]:
    """Process products data to handle array fields and proper formatting"""
    processed = []
    
    for product in products:
        processed_product = product.copy()
        
        # Handle images array
        if 'images' in processed_product and processed_product['images']:
            try:
                # If it's already a JSON string, parse it
                if isinstance(processed_product['images'], str):
                    if processed_product['images'].startswith('['):
                        processed_product['images'] = json.loads(processed_product['images'])
                    else:
                        # Single image, convert to array
                        processed_product['images'] = [processed_product['images']]
            except Exception as e:
                print(f"Error processing images for {processed_product.get('name', 'unknown')}: {e}")
                processed_product['images'] = [processed_product['images']]
        
        # Handle collection_ids array
        if 'collection_ids' in processed_product and processed_product['collection_ids']:
            try:
                if isinstance(processed_product['collection_ids'], str):
                    # Handle various formats: "1,2,3" or "[1,2,3]" or "{1,2,3}"
                    ids_str = processed_product['collection_ids'].strip('{}[]')
                    if ids_str:
                        processed_product['collection_ids'] = [int(x.strip()) for x in ids_str.split(',')]
                    else:
                        processed_product['collection_ids'] = None
            except Exception as e:
                print(f"Error processing collection_ids for {processed_product.get('name', 'unknown')}: {e}")
                processed_product['collection_ids'] = None
        
        # Handle capsule_ids array
        if 'capsule_ids' in processed_product and processed_product['capsule_ids']:
            try:
                if isinstance(processed_product['capsule_ids'], str):
                    # Handle various formats: "1,2,3" or "[1,2,3]" or "{1,2,3}"
                    ids_str = processed_product['capsule_ids'].strip('{}[]')
                    if ids_str:
                        processed_product['capsule_ids'] = [int(x.strip()) for x in ids_str.split(',')]
                    else:
                        processed_product['capsule_ids'] = None
            except Exception as e:
                print(f"Error processing capsule_ids for {processed_product.get('name', 'unknown')}: {e}")
                processed_product['capsule_ids'] = None
        
        # Handle price
        if 'price' in processed_product and processed_product['price']:
            try:
                processed_product['price'] = float(processed_product['price'])
            except Exception as e:
                print(f"Error processing price for {processed_product.get('name', 'unknown')}: {e}")
                processed_product['price'] = 0.0
        
        processed.append(processed_product)
    
    return processed

# Test the data processing
print("🔍 Testing product data processing...")

# Read the CSV
data = read_csv_file('products.csv')
print(f"✅ Read {len(data)} products from CSV")

# Process the data
processed_data = process_products_data(data[:3])  # Test first 3 products
print(f"✅ Processed {len(processed_data)} products")

# Show sample data
for i, product in enumerate(processed_data):
    print(f"\n📦 Product {i+1}: {product.get('name', 'Unknown')}")
    print(f"   ID: {product.get('id')}")
    print(f"   Price: {product.get('price')}")
    print(f"   Images: {len(product.get('images', []))} images")
    print(f"   Collection IDs: {product.get('collection_ids')}")
    print(f"   Capsule IDs: {product.get('capsule_ids')}")

print("\n✅ Debug complete!") 