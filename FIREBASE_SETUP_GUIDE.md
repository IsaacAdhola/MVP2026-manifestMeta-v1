# 🔥 Firebase Setup Guide for MetaMarkAgency

**Purpose:** Set up Firebase as your staging environment (AI agents will write here, NEVER to production)

**Time Required:** ~10 minutes

---

## Step 1: Create Firebase Project

1. **Go to Firebase Console**
   - Open: https://console.firebase.google.com/
   - Sign in with your Google account (or create one)

2. **Create New Project**
   - Click **"Add project"** or **"Create a project"**
   - Enter project name: `metamark-agency-staging`
   - Click **Continue**

3. **Google Analytics (Optional)**
   - Choose: **"Enable Google Analytics"** (recommended for metrics)
   - Or: **"Not right now"** (you can add later)
   - Click **Continue** or **Create project**

4. **Wait for Setup**
   - Takes ~30 seconds
   - Click **Continue** when ready

---

## Step 2: Enable Firestore Database

1. **Navigate to Firestore**
   - In left sidebar, click **"Build"** → **"Firestore Database"**
   - Click **"Create database"**

2. **Choose Location**
   - **Recommended:** Select location closest to you
     - `us-central1` (Iowa) - Good for US
     - `europe-west1` (Belgium) - Good for Europe
     - `asia-southeast1` (Singapore) - Good for Asia
   - Click **Next**

3. **Security Rules**
   - Choose **"Start in test mode"** (for staging)
   - This allows all reads/writes (safe for staging only!)
   - Click **Enable**

4. **Wait for Database Creation**
   - Takes ~1 minute
   - You'll see an empty database when ready

---

## Step 3: Get Service Account Credentials

1. **Go to Project Settings**
   - Click the ⚙️ gear icon in left sidebar
   - Click **"Project settings"**

2. **Navigate to Service Accounts**
   - Click the **"Service accounts"** tab
   - You should see "Firebase Admin SDK"

3. **Generate Private Key**
   - Click **"Generate new private key"** button
   - Confirm by clicking **"Generate key"** in popup
   - A JSON file will download (e.g., `metamark-agency-staging-firebase-adminsdk-xxxxx.json`)

4. **Important:** 
   - ⚠️ This file contains secrets - NEVER commit to git!
   - ⚠️ Keep it safe and private
   - ⚠️ If lost, generate a new one (old one won't work)

---

## Step 4: Save Credentials to Your Project

1. **Rename the Downloaded File**
   - Original: `metamark-agency-staging-firebase-adminsdk-xxxxx.json`
   - Rename to: `firebase-staging-key.json`

2. **Move to Your Project Folder**
   - Copy `firebase-staging-key.json` to your MetaMarkAgency root folder
   - Same folder as your `.env` file

3. **Verify Location**
   ```
   MVP2026-manifestMeta-master/
   ├── .env                          ← Your config file
   ├── firebase-staging-key.json     ← Your credentials (NEW)
   ├── agency.py
   ├── requirements.txt
   └── ...
   ```

4. **Check .gitignore**
   - Make sure `.gitignore` includes:
     ```
     firebase-staging-key.json
     *.json
     .env
     ```
   - This prevents accidentally committing secrets

---

## Step 5: Update Your .env File

**I've already updated your `.env.example` - now copy values to your actual `.env`:**

Open your `.env` file and add these lines:

```bash
# ========================================
# ENVIRONMENT
# ========================================
ENVIRONMENT=staging

# ========================================
# FIREBASE STAGING (AI agents write here)
# ========================================
FIREBASE_PROJECT_ID=metamark-agency-staging
FIREBASE_CREDENTIALS_PATH=./firebase-staging-key.json

# ⚠️ IMPORTANT: Replace "metamark-agency-staging" above with YOUR actual Firebase project ID
# To find it: Go to Firebase Console → Project Settings → Project ID
```

---

## Step 6: Get Your Exact Firebase Project ID

**Important:** The project ID might be different from the name!

1. **Go to Firebase Console**
   - https://console.firebase.google.com/
   - Click on your `metamark-agency-staging` project

2. **Open Project Settings**
   - Click ⚙️ gear icon → **"Project settings"**

3. **Copy Project ID**
   - In the "General" tab
   - Under "Your apps" section
   - Look for **"Project ID"**: `metamark-agency-staging` (or similar)
   - Copy the EXACT value

4. **Update .env**
   - Replace the `FIREBASE_PROJECT_ID` value in your `.env` with the exact ID

---

## Step 7: Verify Setup

**Run this test to confirm everything works:**

```bash
# Navigate to your project folder
cd /path/to/MVP2026-manifestMeta-master

# Test Firebase connection
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

print('✅ Environment:', os.getenv('ENVIRONMENT'))
print('✅ Firebase Project ID:', os.getenv('FIREBASE_PROJECT_ID'))
print('✅ Credentials Path:', os.getenv('FIREBASE_CREDENTIALS_PATH'))

import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate(os.getenv('FIREBASE_CREDENTIALS_PATH'))
firebase_admin.initialize_app(cred)
db = firestore.client()

print('✅ Firebase connected successfully!')
print('✅ Ready to use staging environment!')
"
```

**Expected Output:**
```
✅ Environment: staging
✅ Firebase Project ID: metamark-agency-staging
✅ Credentials Path: ./firebase-staging-key.json
✅ Firebase connected successfully!
✅ Ready to use staging environment!
```

**If you see errors:**
- Check file path: `firebase-staging-key.json` is in the right folder?
- Check `.env` file: Variables set correctly?
- Install firebase-admin: `pip install firebase-admin`

---

## Complete .env File (All Keys)

**Here's your complete `.env` configuration:**

```bash
# ========================================
# OPENAI API (for AI agents)
# ========================================
OPENAI_API_KEY=sk-proj-your-key-here

# ========================================
# FACEBOOK API (for ad posting)
# ========================================
FACEBOOK_APP_ID=your-app-id
FACEBOOK_APP_SECRET=your-app-secret
FACEBOOK_ACCESS_TOKEN=your-access-token
FACEBOOK_AD_ACCOUNT_ID=act_your-account-id
FACEBOOK_PAGE_ID=your-page-id

# ========================================
# ENVIRONMENT
# ========================================
ENVIRONMENT=staging

# ========================================
# FIREBASE STAGING (AI agents write here)
# ========================================
FIREBASE_PROJECT_ID=metamark-agency-staging
FIREBASE_CREDENTIALS_PATH=./firebase-staging-key.json

# ========================================
# OPTIONAL: Testing & Development
# ========================================
# TEST_MODE=true  # Uncomment to run without Facebook API
```

---

## Security Checklist ✅

Before you proceed, verify:

- [ ] `firebase-staging-key.json` is in project root
- [ ] `firebase-staging-key.json` is in `.gitignore`
- [ ] `.env` is in `.gitignore`
- [ ] `FIREBASE_PROJECT_ID` matches your actual project ID
- [ ] `FIREBASE_CREDENTIALS_PATH` points to the correct file
- [ ] You've tested the connection (Step 7)
- [ ] You understand: This is STAGING only, NOT production

---

## Cost Estimate 💰

**Firebase Free Tier (Spark Plan):**
- ✅ 1 GB storage
- ✅ 50,000 reads/day
- ✅ 20,000 writes/day
- ✅ 10 GB network egress/month

**Expected Usage (Staging):**
- ~100 test campaigns/month = ~10 MB
- ~1,000 agent executions/month = ~500 KB
- **Well within free tier! $0/month**

**If you exceed free tier:**
- Automatic upgrade to Blaze plan (pay-as-you-go)
- Estimated cost: $0-5/month for staging
- You can set budget alerts in Firebase Console

---

## What's Next?

After Firebase is set up, I'll:

1. ✅ Create `firebase_adapter.py` to connect agents to staging
2. ✅ Update `agent_tracking_system.py` to write to Firebase
3. ✅ Update `client_guidance_system.py` to write to Firebase
4. ✅ Keep governed memory working locally (for development)
5. ✅ Test full workflow with Firebase staging

**But I'll ASK you first before implementing!** (per our rules)

---

## Troubleshooting

### Error: "Default app already exists"
**Solution:** You've already initialized Firebase. Restart your Python script.

### Error: "Permission denied"
**Solution:** 
1. Check Firestore security rules (should be in "test mode")
2. Verify credentials file is correct
3. Make sure you downloaded the right JSON file

### Error: "Project not found"
**Solution:** 
1. Verify `FIREBASE_PROJECT_ID` exactly matches Firebase Console
2. Check for typos
3. Make sure you created the project successfully

### Error: "Cannot find firebase-staging-key.json"
**Solution:**
1. Check file is in project root folder
2. Check file name is exactly: `firebase-staging-key.json`
3. Try absolute path: `/full/path/to/firebase-staging-key.json`

---

## Support

**Need help?**
- Firebase Docs: https://firebase.google.com/docs
- Firestore Docs: https://firebase.google.com/docs/firestore
- Python Admin SDK: https://firebase.google.com/docs/admin/setup

**Questions for me?**
- Just ask! I'm here to help.
- I'll wait for you to complete setup before implementing the adapter.

---

**🎉 Once you complete these steps, let me know and I'll implement the Firebase adapter!**
