import os
from dotenv import load_dotenv

print("🔍 Environment Debug Script")
print("=" * 30)

# Load environment variables
load_dotenv()

print(f"Current working directory: {os.getcwd()}")
print(f".env file exists: {os.path.exists('.env')}")

# Check environment variables
cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
api_key = os.getenv('CLOUDINARY_API_KEY')
api_secret = os.getenv('CLOUDINARY_API_SECRET')

print(f"\nEnvironment Variables:")
print(f"CLOUDINARY_CLOUD_NAME: {'✅ Found' if cloud_name else '❌ Missing'}")
print(f"CLOUDINARY_API_KEY: {'✅ Found' if api_key else '❌ Missing'}")
print(f"CLOUDINARY_API_SECRET: {'✅ Found' if api_secret else '❌ Missing'}")

if cloud_name:
    print(f"\nCloud Name: {cloud_name}")
if api_key:
    print(f"API Key: {api_key[:10]}...")

# List files in current directory
print(f"\nFiles in current directory:")
for file in os.listdir('.'):
    print(f"  - {file}") 