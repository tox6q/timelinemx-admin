# TimelineMX Product Manager - Quick Start Guide

## 🚀 Quick Setup (5 minutes)

### Step 1: Download Python
1. Go to [python.org/downloads](https://python.org/downloads)
2. Download and install Python (make sure to check "Add Python to PATH")

### Step 2: Install Requirements
1. Open Command Prompt (Windows) or Terminal (Mac)
2. Navigate to this folder
3. Run: `pip install -r requirements.txt`

### Step 3: Create .env file
Create a file called `.env` in this folder with your Supabase credentials:
```
SUPABASE_URL=your_supabase_url_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
CLOUDINARY_CLOUD_NAME=your_cloudinary_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

### Step 4: Run the Manager
```bash
python upload.py
```

## 📋 Simple Workflow

1. **Choose what to upload** from the menu:
   - Collections (team/league groupings)
   - Capsules (special jersey collections) 
   - Products (individual jerseys)
   - FAQ (frequently asked questions)
   - Contact Info

2. **Everything is backed up automatically** before changes

3. **Confirm each upload** - you have full control

## 🔒 Safety Features
- ✅ Automatic backups before every change
- ✅ Manual confirmation required
- ✅ Easy to undo changes
- ✅ No accidental data loss

## 🆘 Need Help?
- All your data is automatically backed up
- Check the `backups/` folder to see previous versions
- Contact [your name] if you need assistance

## 📁 Important Files
- `upload.py` - Main program to run
- `requirements.txt` - Python dependencies 
- `.env` - Your private credentials (create this)
- `backups/` - All your data backups
- CSV files - Your product data

That's it! The system is designed to be safe and simple to use. 