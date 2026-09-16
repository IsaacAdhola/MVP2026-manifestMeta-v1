# 🚀 Quick Start Guide for SMB Owners

**Welcome! You're 15 minutes away from your first AI-powered marketing campaign.**

No technical degree required. No $5,000 agency fees. Just results.

---

## 👋 First Things First

### You're Not Replacing Your Team
MetaMarkAgency is your **marketing assistant**, not a replacement. Think of it like hiring:
- A researcher who never sleeps
- A copywriter who works in seconds
- A designer who generates unlimited variations
- A compliance expert who catches mistakes

**You're still the boss.** Every campaign gets your approval before it goes live.

---

## 💰 What You'll Save

### Traditional Marketing Agency
- Setup fee: **$2,000**
- Monthly retainer: **$5,000**
- **Total for 1 campaign:** ~$7,000

### MetaMarkAgency
- Setup: **FREE** (15 minutes of your time)
- Per campaign: **$499-$999**
- **Total for 1 campaign:** $499 ✅

**You save: $6,500 on your first campaign**

---

## 🎯 Step 1: Get Your API Keys (10 minutes)

### OpenAI API Key ($5-20/campaign)
1. Go to https://platform.openai.com/
2. Sign up (if new) or log in
3. Click "API Keys" in left sidebar
4. Click "Create new secret key"
5. Copy it somewhere safe (you'll paste it in Step 3)

**Cost:** ~$0.01-0.06 per API call. Budget $5-20 per campaign.

### Facebook API Access (FREE)
1. Go to https://developers.facebook.com/
2. Log in with your Facebook account
3. Click "My Apps" → "Create App"
4. Choose "Business" type
5. Fill in app name (e.g., "MyCompanyMarketing")
6. Get your:
   - App ID
   - App Secret
   - Go to "Tools" → "Graph API Explorer" → Get "Access Token"
   - Get your Ad Account ID from https://business.facebook.com/

**Cost:** FREE (you only pay for actual ad spend)

---

## 🔧 Step 2: Install MetaMarkAgency (2 minutes)

### Option A: Using Terminal (Recommended)
```bash
# Download the code
git clone https://github.com/YourRepo/MetaMarkAgency.git
cd MetaMarkAgency

# Install dependencies
pip install -r requirements.txt
```

### Option B: Download ZIP (No Git Required)
1. Go to https://github.com/YourRepo/MetaMarkAgency
2. Click green "Code" button → "Download ZIP"
3. Extract the ZIP file
4. Open terminal/command prompt
5. Navigate to extracted folder
6. Run: `pip install -r requirements.txt`

**Stuck?** Watch our 2-minute video: https://youtube.com/metamark-install

---

## 🔑 Step 3: Add Your API Keys (2 minutes)

1. Open the `.env.example` file
2. Copy it and rename to `.env`
3. Fill in your keys:

```bash
# OpenAI (for AI generation)
OPENAI_API_KEY=sk-your-key-here

# Facebook (for posting ads)
FACEBOOK_APP_ID=your-app-id
FACEBOOK_APP_SECRET=your-app-secret
FACEBOOK_ACCESS_TOKEN=your-access-token
FACEBOOK_AD_ACCOUNT_ID=act_your-account-id
FACEBOOK_PAGE_ID=your-page-id
```

**Don't have all Facebook IDs yet?** Run in test mode:
```bash
# Test mode (no Facebook required)
OPENAI_API_KEY=sk-your-key-here
TEST_MODE=true
```

---

## 🎬 Step 4: Run Your First Campaign (1 minute)

```bash
python agency.py
```

The terminal will prompt you:
```
MetaMarkAgency initialized.
What would you like to work on?
> Launch a new summer sale campaign for my coffee shop
```

### What Happens Next?
1. **Research** (2-3 min) - Analyzes competitor ads, finds trending keywords
2. **Ad Copy** (1-2 min) - Writes 3 variations for you to choose from
3. **Images** (1-2 min) - Generates eye-catching visuals
4. **Policy Check** (30 sec) - Ensures compliance with Facebook rules
5. **Your Approval** - You review and approve/reject/revise
6. **Go Live** - Posts to Facebook (or saves draft if in test mode)

**Total time:** ~10 minutes from start to live campaign

---

## 🛡️ You're Always in Control

### Nothing Goes Live Without Your Approval
```
[ClientApprovalAgent]
Campaign ready for review:
- Ad Copy: "☕ Summer Sale! 20% off all iced coffee..."
- Image: [preview link]
- Budget: $50/day
- Audience: 25-45, coffee lovers, 10-mile radius

Approve? (y/n/revise):
```

Type:
- **y** - Approve and post
- **n** - Reject and start over
- **revise** - Make changes (it'll ask what to change)

### Set Budget Limits
```bash
# In your campaign setup
Campaign budget: $500
Daily budget: $50
```

The system will **automatically stop** if you hit your budget. No surprises.

---

## 💡 Common Questions from SMB Owners

### "I'm not technical. Will I understand this?"
If you can send an email, you can use MetaMarkAgency. The terminal prompts you with plain English questions. No coding required.

### "What if I mess something up?"
You can't break anything! The worst that happens:
- Bad ad copy → You reject it, ask for revision
- API error → System tells you exactly what to fix
- Budget concern → Set limits upfront, system enforces them

### "How long until I see results?"
- **First campaign:** 15 minutes to go live
- **First data:** Facebook shows results within 24-48 hours
- **Optimization:** After 3-4 campaigns, the AI learns your brand voice

### "Is my data secure?"
Yes! Your data stays on your computer. The only things sent to the cloud:
- OpenAI: Your prompts (for content generation)
- Facebook: Your approved ads (to post)

We never see your customer data, financials, or confidential info.

### "Can I cancel anytime?"
There's no subscription! You pay per campaign. Run 1 campaign or 100. Your choice.

---

## 🎓 Learn as You Go

### First Campaign: Follow the Template
Use our starter template:
```
"Create a [product] campaign targeting [audience] with [goal]"

Examples:
- "Create a summer sale campaign targeting coffee lovers with 20% off"
- "Create a grand opening campaign targeting local families with free samples"
- "Create a product launch campaign targeting tech enthusiasts with early access"
```

### Second Campaign: Customize
After your first campaign, you'll understand the flow. Then:
- Adjust your target audience
- Tweak the copy style
- Set different budgets
- Try different images

### Third Campaign: Advanced
By campaign 3, you're ready to:
- A/B test different approaches
- Use competitor insights
- Fine-tune for better ROI

**Pro tip:** Run campaigns 1-2 weeks apart so you can measure results and improve.

---

## 📊 Measuring Success

### After Your Campaign Goes Live:
1. Go to Facebook Ads Manager
2. Check your campaign performance:
   - **Reach:** How many people saw your ad
   - **Clicks:** How many clicked through
   - **CTR (Click-Through Rate):** Industry average is 1-2%, aim for 2%+
   - **Cost per Click:** Varies by industry, track it to optimize

### MetaMarkAgency Advantage:
Unlike traditional agencies, you can run **10 campaigns** for the price of 1 agency month. Test more, learn faster, optimize quicker.

---

## 🆘 Need Help?

### Documentation
- Full guide: `/workspace/INTEGRATION_GUIDE.md`
- Technical details: `/workspace/README.md`

### Community
- Discord: https://discord.gg/metamarkagency (coming soon)
- Forum: https://forum.metamarkagency.com (coming soon)

### Support
- Email: support@metamarkagency.com
- Response time: Within 24 hours
- Emergency? Check our troubleshooting guide: `/workspace/TROUBLESHOOTING.md`

---

## ✅ Onboarding Checklist

- [ ] Got OpenAI API key
- [ ] Got Facebook API credentials (or using test mode)
- [ ] Installed dependencies (`pip install -r requirements.txt`)
- [ ] Created `.env` file with credentials
- [ ] Ran first test: `python agency.py`
- [ ] Reviewed sample campaign output
- [ ] Set campaign budget limits
- [ ] Understand approval workflow
- [ ] Know how to request revisions
- [ ] Bookmarked documentation

---

## 🎉 You're Ready!

**You've successfully onboarded to MetaMarkAgency.**

Run your first campaign now:
```bash
python agency.py
```

Remember:
- **You're in control** - Nothing posts without your approval
- **Start small** - Run a $50 test campaign first
- **Learn fast** - Each campaign teaches you more
- **Scale up** - When confident, increase budgets

**Welcome to the future of affordable, human-controlled AI marketing!** 🚀

---

*Questions? Email: onboarding@metamarkagency.com*
