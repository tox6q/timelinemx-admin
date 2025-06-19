import os
import csv
import json
from typing import List, Dict, Optional
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
COLLECTIONS_CSV = 'collections.csv'
CAPSULE_CSV = 'capsule.csv'
PRODUCTS_CSV = 'products.csv'  # Assuming this is your products CSV
FAQ_CSV = 'faq.csv'  # FAQ CSV file
CONTACT_JSON = 'contact-content.json'  # Contact content JSON file
BACKUPS_FOLDER = 'backups'

class SupabaseUploader:
    def __init__(self):
        self.supabase: Optional[Client] = None
        self.setup_supabase()
        self.ensure_backups_folder()
    
    def setup_supabase(self):
        """Initialize Supabase client"""
        try:
            url = os.getenv('SUPABASE_URL')
            key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')  # Use service role for admin operations
            
            if not url or not key:
                print("❌ Missing Supabase credentials in .env file")
                print("Required: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY")
                return False
            
            self.supabase = create_client(url, key)
            print("✅ Supabase client initialized successfully")
            return True
        
        except Exception as e:
            print(f"❌ Error initializing Supabase: {e}")
            return False
    
    def ensure_backups_folder(self):
        """Create backups folder if it doesn't exist"""
        if not os.path.exists(BACKUPS_FOLDER):
            os.makedirs(BACKUPS_FOLDER)
            print(f"📁 Created backups folder: {BACKUPS_FOLDER}")
    
    def get_timestamp(self) -> str:
        """Get current timestamp for backup filenames"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def backup_table(self, table_name: str) -> bool:
        """Download and backup current table data before modification"""
        try:
            print(f"💾 Creating backup of {table_name} table...")
            
            # Fetch all data from table
            result = self.supabase.table(table_name).select("*").execute()
            
            if not result.data:
                print(f"⚠️  Table {table_name} is empty - no backup needed")
                return True
            
            # Create backup filename with timestamp
            timestamp = self.get_timestamp()
            backup_filename = f"{BACKUPS_FOLDER}/{table_name}_backup_{timestamp}.csv"
            
            # Write backup to CSV
            if result.data:
                with open(backup_filename, 'w', encoding='utf-8', newline='') as file:
                    if len(result.data) > 0:
                        fieldnames = result.data[0].keys()
                        writer = csv.DictWriter(file, fieldnames=fieldnames)
                        writer.writeheader()
                        for row in result.data:
                            # Convert arrays back to JSON strings for CSV compatibility
                            processed_row = {}
                            for key, value in row.items():
                                if isinstance(value, list):
                                    processed_row[key] = json.dumps(value)
                                else:
                                    processed_row[key] = value
                            writer.writerow(processed_row)
                
                print(f"✅ Backup saved: {backup_filename} ({len(result.data)} records)")
            
            return True
        
        except Exception as e:
            print(f"❌ Error creating backup for {table_name}: {e}")
            return False
    
    def read_csv_file(self, filename: str) -> List[Dict]:
        """Read CSV file and return list of dictionaries"""
        if not os.path.exists(filename):
            print(f"⚠️  CSV file not found: {filename}")
            return []
        
        try:
            data = []
            with open(filename, 'r', encoding='utf-8', newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Clean empty strings to None for proper database insertion
                    cleaned_row = {}
                    for key, value in row.items():
                        cleaned_row[key] = value if value.strip() else None
                    data.append(cleaned_row)
            
            print(f"📋 Read {len(data)} rows from {filename}")
            return data
        
        except Exception as e:
            print(f"❌ Error reading {filename}: {e}")
            return []
    
    def truncate_table(self, table_name: str) -> bool:
        """Safely truncate a table"""
        try:
            print(f"🗑️  Truncating table: {table_name}")
            
            # Delete all records using a condition that works with UUID ids
            # Use 'not is null' instead of 'neq 0' to avoid UUID parsing issues
            result = self.supabase.table(table_name).delete().not_.is_('id', 'null').execute()
            
            print(f"✅ Truncated {table_name} successfully")
            return True
        
        except Exception as e:
            print(f"❌ Error truncating {table_name}: {e}")
            return False
    
    def upload_to_table(self, table_name: str, data: List[Dict]) -> bool:
        """Upload data to specified table"""
        if not data:
            print(f"⚠️  No data to upload to {table_name}")
            return True
        
        try:
            print(f"⬆️  Uploading {len(data)} records to {table_name}")
            
            # Process data for specific tables
            if table_name == 'products':
                data = self.process_products_data(data)
            
            # Insert data in batches of 100 to avoid timeout
            batch_size = 100
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                result = self.supabase.table(table_name).insert(batch).execute()
                print(f"✅ Uploaded batch {i//batch_size + 1}/{(len(data)-1)//batch_size + 1}")
            
            print(f"✅ Successfully uploaded all data to {table_name}")
            return True
        
        except Exception as e:
            print(f"❌ Error uploading to {table_name}: {e}")
            return False
    
    def validate_products_data(self, products: List[Dict]) -> bool:
        """Validate that all products have a price"""
        missing_price_rows = []
        
        for i, product in enumerate(products, 1):
            price = product.get('price', '').strip() if product.get('price') else ''
            if not price or price == '0' or price == '0.0':
                missing_price_rows.append(i)
        
        if missing_price_rows:
            print(f"❌ VALIDATION ERROR: Products missing price!")
            print(f"   Rows with missing/zero price: {missing_price_rows[:10]}")  # Show first 10
            if len(missing_price_rows) > 10:
                print(f"   ... and {len(missing_price_rows) - 10} more rows")
            print(f"   Total rows with issues: {len(missing_price_rows)}")
            print("\n💡 Please fix the prices in your CSV file before uploading.")
            return False
        
        print(f"✅ Price validation passed - all {len(products)} products have valid prices")
        return True
    
    def process_products_data(self, products: List[Dict]) -> List[Dict]:
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
                except:
                    # Fallback: treat as single image
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
                except:
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
                except:
                    processed_product['capsule_ids'] = None
            
            # Handle price
            if 'price' in processed_product and processed_product['price']:
                try:
                    processed_product['price'] = float(processed_product['price'])
                except:
                    processed_product['price'] = 0.0
            
            processed.append(processed_product)
        
        return processed
    
    def upload_single_table(self, table_name: str, csv_file: str) -> bool:
        """Upload data to a single table with backup"""
        if not self.supabase:
            print("❌ Supabase client not initialized")
            return False
        
        print(f"\n🚀 Starting {table_name} upload...")
        print(f"📄 Source: {csv_file}")
        
        # Step 1: Create backup
        if not self.backup_table(table_name):
            print(f"❌ Backup failed for {table_name} - aborting upload")
            return False
        
        # Step 2: Read CSV data
        data = self.read_csv_file(csv_file)
        if not data:
            print(f"❌ No data to upload from {csv_file}")
            return False
        
        # Step 2.5: Validate products data if uploading products
        if table_name == 'products':
            if not self.validate_products_data(data):
                print(f"❌ Products validation failed - aborting upload")
                return False
        
        # Step 3: Confirm upload
        print(f"\n⚠️  This will REPLACE ALL data in {table_name} table!")
        print(f"📊 New data: {len(data)} records")
        confirm = input(f"Proceed with {table_name} upload? (yes/no): ").lower().strip()
        
        if confirm not in ['yes', 'y']:
            print("Upload cancelled.")
            return False
        
        try:
            # Step 4: Truncate and upload
            if not self.truncate_table(table_name):
                return False
            
            if not self.upload_to_table(table_name, data):
                return False
            
            print(f"🎉 {table_name} upload completed successfully!")
            print(f"📊 {len(data)} records uploaded")
            return True
        
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            return False
    
    def show_menu(self):
        """Show interactive menu for upload options"""
        while True:
            print("\n" + "="*50)
            print("TimelineMX - Database Upload Manager")
            print("="*50)
            print("📋 Available CSV files:")
            
            # Check which CSV files exist
            csv_files = {
                'collections': (COLLECTIONS_CSV, os.path.exists(COLLECTIONS_CSV)),
                'capsule': (CAPSULE_CSV, os.path.exists(CAPSULE_CSV)),
                'products': (PRODUCTS_CSV, os.path.exists(PRODUCTS_CSV)),
                'faq': (FAQ_CSV, os.path.exists(FAQ_CSV))
            }
            
            for table, (filename, exists) in csv_files.items():
                status = "✅" if exists else "❌"
                print(f"   {status} {table}: {filename}")
            
            # Check contact JSON file
            contact_exists = os.path.exists(CONTACT_JSON)
            contact_status = "✅" if contact_exists else "❌"
            print(f"   {contact_status} contact: {CONTACT_JSON}")
            
            print("\n📤 Upload Options:")
            print("1. Upload Collections")
            print("2. Upload Capsules") 
            print("3. Upload Products")
            print("4. Upload FAQ")
            print("5. Upload Contact Content")
            print("6. View Backup History")
            print("7. Exit")
            
            choice = input("\nSelect option (1-7): ").strip()
            
            if choice == '1':
                if csv_files['collections'][1]:
                    self.upload_single_table('collections', COLLECTIONS_CSV)
                else:
                    print(f"❌ {COLLECTIONS_CSV} not found!")
            
            elif choice == '2':
                if csv_files['capsule'][1]:
                    self.upload_single_table('capsule', CAPSULE_CSV)
                else:
                    print(f"❌ {CAPSULE_CSV} not found!")
            
            elif choice == '3':
                if csv_files['products'][1]:
                    self.upload_single_table('products', PRODUCTS_CSV)
                else:
                    print(f"❌ {PRODUCTS_CSV} not found!")
            
            elif choice == '4':
                if csv_files['faq'][1]:
                    self.upload_single_table('faq', FAQ_CSV)
                else:
                    print(f"❌ {FAQ_CSV} not found!")
            
            elif choice == '5':
                if contact_exists:
                    self.upload_contact_content()
                else:
                    print(f"❌ {CONTACT_JSON} not found!")
            
            elif choice == '6':
                self.show_backup_history()
            
            elif choice == '7':
                print("👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid option. Please select 1-7.")
    
    def show_backup_history(self):
        """Show list of backup files"""
        print("\n📁 Backup History:")
        
        if not os.path.exists(BACKUPS_FOLDER):
            print("No backups found.")
            return
        
        backup_files = [f for f in os.listdir(BACKUPS_FOLDER) if f.endswith('.csv')]
        
        if not backup_files:
            print("No backup files found.")
            return
        
        # Sort by modification time (newest first)
        backup_files.sort(key=lambda x: os.path.getmtime(os.path.join(BACKUPS_FOLDER, x)), reverse=True)
        
        for i, filename in enumerate(backup_files[:10], 1):  # Show last 10 backups
            filepath = os.path.join(BACKUPS_FOLDER, filename)
            modified_time = datetime.fromtimestamp(os.path.getmtime(filepath))
            file_size = os.path.getsize(filepath)
            
            print(f"{i:2d}. {filename}")
            print(f"     📅 {modified_time.strftime('%Y-%m-%d %H:%M:%S')} | 💾 {file_size:,} bytes")
        
        if len(backup_files) > 10:
            print(f"... and {len(backup_files) - 10} more backup files")
    
    def backup_storage_file(self, bucket_name: str, file_name: str) -> bool:
        """Download and backup current file from Supabase storage"""
        try:
            print(f"💾 Creating backup of {file_name} from {bucket_name} bucket...")
            
            # Download current file from storage
            result = self.supabase.storage.from_(bucket_name).download(file_name)
            
            if not result:
                print(f"⚠️  File {file_name} not found in {bucket_name} bucket - no backup needed")
                return True
            
            # Create backup filename with timestamp
            timestamp = self.get_timestamp()
            name_without_ext = os.path.splitext(file_name)[0]
            ext = os.path.splitext(file_name)[1]
            backup_filename = f"{BACKUPS_FOLDER}/{bucket_name}_{name_without_ext}_backup_{timestamp}{ext}"
            
            # Save backup file
            with open(backup_filename, 'wb') as file:
                file.write(result)
            
            print(f"✅ Backup saved: {backup_filename}")
            return True
        
        except Exception as e:
            print(f"❌ Error creating backup for {file_name}: {e}")
            return False
    
    def upload_storage_file(self, bucket_name: str, file_name: str, local_file_path: str) -> bool:
        """Upload file to Supabase storage bucket"""
        if not os.path.exists(local_file_path):
            print(f"❌ Local file not found: {local_file_path}")
            return False
        
        try:
            print(f"⬆️  Uploading {local_file_path} to {bucket_name}/{file_name}")
            
            # Read local file
            with open(local_file_path, 'rb') as file:
                file_data = file.read()
            
            # Delete existing file if it exists
            try:
                self.supabase.storage.from_(bucket_name).remove([file_name])
                print(f"🗑️  Removed existing {file_name}")
            except:
                pass  # File might not exist, which is fine
            
            # Upload new file
            result = self.supabase.storage.from_(bucket_name).upload(
                file_name, 
                file_data,
                file_options={"content-type": "application/json"}
            )
            
            print(f"✅ Successfully uploaded {file_name} to {bucket_name} bucket")
            return True
        
        except Exception as e:
            print(f"❌ Error uploading {file_name}: {e}")
            return False
    
    def upload_contact_content(self) -> bool:
        """Upload contact-content.json with backup"""
        if not self.supabase:
            print("❌ Supabase client not initialized")
            return False
        
        print(f"\n📞 Starting contact content upload...")
        print(f"📄 Source: {CONTACT_JSON}")
        
        if not os.path.exists(CONTACT_JSON):
            print(f"❌ {CONTACT_JSON} not found!")
            return False
        
        # Step 1: Create backup
        if not self.backup_storage_file('contact', 'contact-content.json'):
            print("❌ Backup failed for contact-content.json - aborting upload")
            return False
        
        # Step 2: Confirm upload
        print(f"\n⚠️  This will REPLACE the current contact-content.json in storage!")
        confirm = input("Proceed with contact content upload? (yes/no): ").lower().strip()
        
        if confirm not in ['yes', 'y']:
            print("Upload cancelled.")
            return False
        
        # Step 3: Upload new file
        if not self.upload_storage_file('contact', 'contact-content.json', CONTACT_JSON):
            return False
        
        print("🎉 Contact content upload completed successfully!")
        return True

def main():
    """Main function"""
    uploader = SupabaseUploader()
    
    if uploader.supabase:
        uploader.show_menu()
    else:
        print("❌ Cannot start - Supabase connection failed")

if __name__ == "__main__":
    main() 