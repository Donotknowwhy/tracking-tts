# 🔐 AUTO-LOGIN SETUP GUIDE

## 3 CÁCH LOGIN TO TIKTOK

---

## ⚡ METHOD 1: AUTO-LOGIN (Fully Automated - BEST)

### Nếu seller cung cấp TikTok account credentials:

**Setup (1 lần - 2 phút):**

```bash
# Option A: Dùng .env file (Recommended - Secure)
cp .env.example .env
nano .env  # or open with any editor

# Fill in:
TIKTOK_EMAIL=user@example.com
TIKTOK_PASSWORD=your_password_here
```

**Option B: Edit config.py trực tiếp**
```python
# config.py
TIKTOK_EMAIL = "user@example.com"
TIKTOK_PASSWORD = "your_password_here"
```

**Usage:**
```bash
python auto_track.py product_urls.txt

# Tool sẽ:
# 1. ✅ Tự động detect chưa login
# 2. ✅ Tự động login với credentials
# 3. ✅ Lưu session
# 4. ✅ Chạy tracking
# 
# 100% AUTOMATED! User không cần làm gì!
```

**Pros:**
- ✅ Hoàn toàn tự động
- ✅ Không cần manual step
- ✅ Có thể schedule cron jobs
- ✅ Perfect cho production

**Cons:**
- ⚠️ Nếu account có 2FA → không work, phải dùng Method 2
- ⚠️ Phải store credentials (dùng .env để secure hơn)

---

## 🖱️ METHOD 2: MANUAL LOGIN (Semi-automated)

### Không có credentials hoặc account có 2FA:

**Setup (1 lần - 2 phút):**
```bash
python setup_login.py

# Browser mở
# User login manually
# Session được lưu
```

**Usage:**
```bash
python auto_track.py product_urls.txt

# Tool dùng session đã lưu
# Không cần login lại
```

**Pros:**
- ✅ Works với 2FA accounts
- ✅ Works với any login method (Google, Apple, etc.)
- ✅ Không cần store credentials
- ✅ Secure

**Cons:**
- ⚠️ Cần manual login lần đầu (2 phút)
- ⚠️ Cần re-login khi cookies expire (2-4 tuần)

---

## 🔧 METHOD 3: COMMAND-LINE AUTO-LOGIN

### Nếu không muốn config file:

```bash
# Direct auto-login:
python auto_login.py user@example.com password123

# Then run tracking:
python auto_track.py product_urls.txt
```

**Pros:**
- ✅ Không cần edit config files
- ✅ One-time command

**Cons:**
- ⚠️ Password visible in terminal history
- ⚠️ Less secure

---

## 📊 COMPARISON:

| Method | Setup Time | User Involvement | 2FA Support | Security | Automation |
|--------|------------|------------------|-------------|----------|------------|
| **1. Auto (.env)** | 2 min | 0% | ❌ | ⭐⭐⭐⭐ | 100% |
| **2. Manual** | 2 min | 1 time | ✅ | ⭐⭐⭐⭐⭐ | 99% |
| **3. CLI Auto** | 0 min | 0% | ❌ | ⭐⭐ | 100% |

---

## 🎯 RECOMMENDATION:

### Nếu seller cung cấp email + password:

**Use Method 1 (.env file):**

```bash
# 1. Create .env
cat > .env << EOF
TIKTOK_EMAIL=seller_account@example.com
TIKTOK_PASSWORD=seller_password_123
EOF

# 2. Run tool (100% automated!)
python auto_track.py product_urls.txt

# Tool tự động:
# - Check login status
# - Auto-login if needed
# - Run tracking
# - Export CSV
# 
# ZERO MANUAL STEPS! 🎉
```

---

## 🔒 SECURITY BEST PRACTICES:

### Using .env file (Recommended):

```bash
# .env file
TIKTOK_EMAIL=your_email@example.com
TIKTOK_PASSWORD=your_password

# .env is in .gitignore → won't be committed
# Only exists on user's machine
```

### File permissions:
```bash
# Make .env readable only by user
chmod 600 .env
```

### For production/team use:
```bash
# Each user has their own .env
# Never commit credentials to git
# Use different accounts for different users
```

---

## 🎬 COMPLETE WORKFLOWS:

### Workflow A: With Credentials (100% Automated)

```bash
# One-time setup:
cp .env.example .env
# Edit .env with credentials

# Daily usage:
python auto_track.py urls.txt
# → Done! No manual steps!
```

---

### Workflow B: Without Credentials (99% Automated)

```bash
# One-time setup:
python setup_login.py
# Login manually once (2 min)

# Daily usage:
python auto_track.py urls.txt
# → Done! Uses saved session!
```

---

## 🆘 TROUBLESHOOTING:

### Auto-login fails:

**Error: "Incorrect credentials"**
→ Check email/password in .env

**Error: "2FA verification required"**
→ Account has 2FA enabled
→ Use Method 2 (manual login) instead

**Error: "Login button not found"**
→ TikTok changed login page structure
→ Use Method 2 (manual login) as fallback

---

## 📧 FOR SELLER:

### If they provide credentials:

```
Anh/chị ơi,

Nếu cung cấp TikTok account (email + password),
tool có thể 100% TỰ ĐỘNG!

Setup (1 lần):
1. Tạo file .env:
   TIKTOK_EMAIL=account@example.com
   TIKTOK_PASSWORD=password123

2. Done!

Usage:
python auto_track.py urls.txt

→ Tool tự động:
  • Check login
  • Auto-login if needed
  • Run tracking
  • Export CSV

ZERO manual steps! 🎉

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hoặc nếu không muốn share credentials:
→ Dùng manual login (1 lần, 2 phút)
→ Vẫn 99% automated

Anh/chị prefer cách nào?
```

---

## ✅ BOTH OPTIONS IMPLEMENTED!

**With credentials:** 100% automated ⚡
**Without credentials:** 99% automated (login once) ⚡

**Tool ready for both scenarios!** 🎉
