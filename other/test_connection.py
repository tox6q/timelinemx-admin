import os
import cloudinary
import cloudinary.api
from dotenv import load_dotenv

load_dotenv()

print("🔍 Cloudinary Connection Test")
print("=" * 40)

# Try both configuration methods
print("Method 1: Individual variables")
cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
api_key = os.getenv('CLOUDINARY_API_KEY')
api_secret = os.getenv('CLOUDINARY_API_SECRET')

if cloud_name and api_key and api_secret:
    try:
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )
        print("✅ Individual variables config successful")
    except Exception as e:
        print(f"❌ Individual variables config failed: {e}")
else:
    print("❌ Individual variables missing")

print("\nMethod 2: CLOUDINARY_URL")
cloudinary_url = os.getenv('CLOUDINARY_URL')
if cloudinary_url:
    try:
        cloudinary.config()  # Auto-detects CLOUDINARY_URL
        print("✅ CLOUDINARY_URL config successful")
    except Exception as e:
        print(f"❌ CLOUDINARY_URL config failed: {e}")
else:
    print("❌ CLOUDINARY_URL missing")

# Test API connection
print("\n🌐 Testing API Connection...")
try:
    # Get basic account info
    result = cloudinary.api.ping()
    print("✅ API ping successful!")
    print(f"Status: {result}")
except Exception as e:
    print(f"❌ API ping failed: {e}")

# Test listing root folders
print("\n📁 Testing folder listing...")
try:
    result = cloudinary.api.root_folders()
    folders = result.get('folders', [])
    print(f"✅ Found {len(folders)} root folders:")
    for folder in folders:
        print(f"  - {folder['name']}")
except Exception as e:
    print(f"❌ Failed to list folders: {e}")

# Test specific folder
print("\n🎯 Testing specific folder access...")
test_folders = ['TimelineMX/jerseys', 'TimelineMX', 'jerseys', 'test']

for folder in test_folders:
    try:
        result = cloudinary.api.resources(
            type="upload",
            prefix=f"{folder}/",
            max_results=5
        )
        images = result.get('resources', [])
        print(f"✅ {folder}: Found {len(images)} images")
        if images:
            print(f"   Sample: {images[0]['public_id']}")
    except Exception as e:
        print(f"❌ {folder}: {e}")

print("\n🔍 Environment variables:")
print(f"CLOUDINARY_CLOUD_NAME: {os.getenv('CLOUDINARY_CLOUD_NAME', 'Not set')}")
print(f"CLOUDINARY_API_KEY: {os.getenv('CLOUDINARY_API_KEY', 'Not set')[:10] + '...' if os.getenv('CLOUDINARY_API_KEY') else 'Not set'}")
print(f"CLOUDINARY_URL: {'Set' if os.getenv('CLOUDINARY_URL') else 'Not set'}") 