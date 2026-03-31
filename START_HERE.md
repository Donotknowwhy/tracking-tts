# 🚀 START HERE - Quick Setup Guide

## ⚡ 3-Minute Setup

### Step 1: Install (1 minute)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### Step 2: Login to TikTok (2 minutes - ONE TIME ONLY)
```bash
python setup_login.py
```

**In the browser that opens:**
1. Click "Log in"
2. Login with your TikTok account
3. Press Enter in terminal when done

**✅ Session saved!** You won't need to login again for 2-4 weeks.

---

## 🎯 Usage

### Prepare your product URLs

Create `product_urls.txt`:
```
https://www.tiktok.com/shop/pdp/1732128313499292514
https://www.tiktok.com/shop/pdp/another-product/1234567890123456789
...
(50-300 URLs)
```

### Run tracking (ONE COMMAND)

```bash
python auto_track.py product_urls.txt
```

**Tool will:**
1. ✅ Fetch 200 products (~15 min)
2. ✅ Wait 3 hours (automatic countdown)
3. ✅ Fetch again (~15 min)
4. ✅ Analyze growth + extract keywords
5. ✅ Export CSV to `data/output/`

**Done!** Just run once and wait.

---

## 📊 Check Results

**Open these files:**
- `data/output/products_session_X_TIMESTAMP.csv` → Rankings
- `data/output/keywords_session_X_TIMESTAMP.csv` → Top 10 keywords

**Open with:** Excel, Google Sheets, Numbers

---

## 🔧 Maintenance

**Re-login (every 2-4 weeks when cookies expire):**
```bash
rm -rf browser_data/
python setup_login.py
```

---

## 📖 Full Documentation

- **README.md** - Complete guide
- **HUONG_DAN_SU_DUNG.md** - Vietnamese guide
- **USAGE.md** - Detailed usage examples

---

## 🆘 Troubleshooting

**Problem:** "No module found"
```bash
source venv/bin/activate
```

**Problem:** CAPTCHAs appearing
```bash
# Re-login:
python setup_login.py
```

**Problem:** Proxy connection failed
```bash
python test_proxy.py  # Test proxy
```

---

## ✅ That's it!

**3 minutes setup → Unlimited tracking! 🎉**
