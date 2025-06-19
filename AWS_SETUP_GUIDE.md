# 🚀 AWS S3 Setup Guide - Finding Your Credentials

## 📋 What You Need to Find:
1. **AWS Access Key ID** (looks like: `AKIAIOSFODNN7EXAMPLE`)
2. **AWS Secret Access Key** (looks like: `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`)
3. **AWS Region** (looks like: `us-east-1` or `us-west-2`)
4. **S3 Bucket Name** (looks like: `my-timelinemx-images`)

---

## 🔑 Step 1: Find Your Access Keys

### Method A: If you already have them
- Look for a file or document where you saved them when you created your AWS account
- They might be in a downloaded `.csv` file from AWS

### Method B: Create new ones (if you don't have them)
1. **Go to AWS Console**: https://aws.amazon.com/console/
2. **Sign in** to your AWS account
3. **Click on your name** (top right corner)
4. **Select "Security credentials"**
5. **Scroll down** to "Access keys"
6. **Click "Create access key"**
7. **Download the CSV file** or copy the keys immediately
   - ⚠️ **IMPORTANT**: You can only see the secret key ONCE!

---

## 🌍 Step 2: Find Your AWS Region

### Easy Way:
1. **Go to AWS S3 Console**: https://s3.console.aws.amazon.com/
2. **Look at the URL** in your browser
   - If you see: `https://s3.console.aws.amazon.com/s3/buckets?region=us-east-1`
   - Your region is: `us-east-1`
3. **Or look at the top-right corner** of the AWS console
   - You'll see something like "N. Virginia" or "Oregon"
   - N. Virginia = `us-east-1`
   - Oregon = `us-west-2`
   - Ireland = `eu-west-1`

### Common Regions:
| Location | Region Code |
|----------|-------------|
| N. Virginia (US East) | `us-east-1` |
| Oregon (US West) | `us-west-2` |
| Ireland (Europe) | `eu-west-1` |
| London (Europe) | `eu-west-2` |
| Sydney (Asia Pacific) | `ap-southeast-2` |

---

## 🪣 Step 3: Find Your S3 Bucket Name

### Method A: Through AWS Console
1. **Go to S3 Console**: https://s3.console.aws.amazon.com/
2. **You'll see a list of buckets** (if you have any)
3. **Copy the bucket name** you want to use
   - Example: `timelinemx-images-2024`
   - Example: `my-company-photos`

### Method B: If you don't have a bucket yet
1. **Click "Create bucket"** in the S3 console
2. **Choose a name** (must be globally unique)
   - Good examples: `timelinemx-images-yourname`
   - Good examples: `yourcompany-photos-2024`
3. **Select your region** (same as Step 2)
4. **Click "Create bucket"**

---

## 📝 Step 4: Fill in Your .env File

Create a file called `.env` in your `timelinemx-admin` folder:

```
# AWS Credentials
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=timelinemx-images-2024

# Your existing Supabase credentials (don't change these)
SUPABASE_URL=your_existing_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_existing_supabase_key
```

---

## ✅ Step 5: Test Your Setup

Run the test script:
```bash
python aws_s3_test.py
```

### If it works, you'll see:
```
✅ AWS S3 client created successfully
   Region: us-east-1

📋 Listing all available buckets:
   1. timelinemx-images-2024 (Created: 2024-01-20)
```

### If it doesn't work, you might see:
- ❌ Missing AWS credentials → Check your .env file
- ❌ Invalid Access Key → Double-check your access key
- ❌ Access denied → Check your secret key
- ❌ Bucket not found → Check your bucket name spelling

---

## 🆘 Troubleshooting

### "InvalidAccessKeyId" Error
- Your Access Key ID is wrong
- Copy it again from AWS console

### "SignatureDoesNotMatch" Error  
- Your Secret Access Key is wrong
- You might need to create a new access key

### "AccessDenied" Error
- Your AWS user doesn't have S3 permissions
- Contact your AWS administrator

### "NoSuchBucket" Error
- Your bucket name is wrong
- Check the spelling in S3 console

---

## 🔒 Security Tips

1. **Never share your credentials** in chat, email, or code
2. **Keep your .env file private** (it's in .gitignore)
3. **Only give S3 permissions** to your AWS user (not full admin)
4. **Regenerate keys** if you think they're compromised

---

## 📞 Need Help?

If you get stuck:
1. Take a screenshot of the error message
2. Check that your .env file has all 4 AWS values
3. Try creating a new access key pair
4. Make sure your bucket name is spelled exactly right

That's it! Once you have all 4 values, the connection test should work perfectly! 🎉 