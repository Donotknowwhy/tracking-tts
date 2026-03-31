# 🖥️ TOOL CHẠY NHƯ THẾ NÀO?

## 📋 Giải thích cho seller hiểu rõ

---

## 🎯 Tool này là gì?

**Đây là một Python application chạy trên máy của họ (local)**

**KHÔNG phải:**
- ❌ Web service
- ❌ Chrome extension
- ❌ Cloud service
- ❌ Phải upload lên server

**MÀ LÀ:**
- ✅ Command-line tool (terminal)
- ✅ Chạy local trên máy Mac/Windows/Linux
- ✅ Tự động mở browser khi cần
- ✅ Lưu data trong máy (SQLite)

---

## 🔧 Cách hoạt động:

### Architecture:

```
┌────────────────────────────────────────┐
│  MÁY CỦA USER (Local Machine)         │
│                                        │
│  ┌──────────────────────────────┐     │
│  │  Terminal / Command Line     │     │
│  │  $ python auto_track.py ...  │     │
│  └───────────┬──────────────────┘     │
│              │                         │
│              ↓                         │
│  ┌──────────────────────────────┐     │
│  │  Python Script               │     │
│  │  - Load URLs                 │     │
│  │  - Control browser           │     │
│  │  - Save to database          │     │
│  └───────────┬──────────────────┘     │
│              │                         │
│              ↓                         │
│  ┌──────────────────────────────┐     │
│  │  Chrome Browser              │◄────┼─── Browser tự động mở
│  │  (Playwright controls it)    │     │     trên màn hình
│  │  - Opens TikTok Shop         │     │
│  │  - Fetches product pages     │     │
│  └───────────┬──────────────────┘     │
│              │                         │
│              ↓                         │
│  ┌──────────────────────────────┐     │
│  │  Data Storage (SQLite)       │     │
│  │  data/tracking.db            │     │
│  └──────────────────────────────┘     │
│              │                         │
│              ↓                         │
│  ┌──────────────────────────────┐     │
│  │  CSV Output                  │     │
│  │  data/output/*.csv           │     │
│  └──────────────────────────────┘     │
└────────────────────────────────────────┘
               │
               │ Via Proxy
               ↓
     ┌──────────────────┐
     │  SOCKS5 Proxy    │
     │  US Server       │
     └────────┬─────────┘
              │
              ↓
     ┌──────────────────┐
     │  TikTok Shop US  │
     │  (Website)       │
     └──────────────────┘
```

---

## 🖥️ Browser: Visible hay Hidden?

### Default mode: **VISIBLE Browser** (Recommended)

**Khi chạy tool, sẽ có:**
1. ✅ Chrome window tự động mở trên màn hình
2. ✅ User thấy được browser đang làm gì
3. ✅ Có thể login TikTok trong browser này
4. ✅ Browser chạy tự động, không cần user click

**Giống như:**
- Selenium automation bạn thấy trên YouTube
- Browser "ma" tự động click, scroll, fetch data
- Nhưng bạn vẫn thấy được nó trên màn hình

**Có thể minimize window** để không làm phiền công việc.

---

## 👤 User cần làm gì?

### Lần đầu tiên (ONE TIME - 5 phút):

```
Step 1: Install tool
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
$ playwright install chromium

Step 2: Login TikTok
$ python test_login.py

→ Chrome window mở
→ User thấy tiktok.com
→ Click "Login" trong browser
→ Nhập username/password
→ Đợi homepage load
→ Script tự động lưu session
→ Done! Browser đóng

Thời gian: 2 phút
```

### Mỗi lần chạy tracking (0 phút manual):

```
$ python auto_track.py product_urls.txt

→ Chrome window mở (tự động)
→ Tool fetch 200 products (tự động)
→ User thấy browser đang navigate pages
→ User KHÔNG cần click gì cả
→ Có thể minimize window
→ Đợi 3 giờ (tự động)
→ Tool fetch lại 200 products (tự động)
→ Browser đóng (tự động)
→ CSV ready!

User chỉ việc: Chạy lệnh → Đợi → Lấy CSV
```

---

## 🎬 Visual Timeline:

### Khi user chạy tool:

```
T=0:00  User: python auto_track.py urls.txt
        ↓
T=0:05  Chrome window xuất hiện trên màn hình
        Browser tự navigate đến TikTok Shop
        ↓
T=0:10  Browser tự động:
        - Open product page 1
        - Wait 2 seconds
        - Scroll, extract data
        - Close page
        - Open product page 2
        - ... repeat 200 times
        ↓
T=15:00 Snapshot 1 done
        Browser minimize/hide
        Terminal show: "Waiting 3 hours..."
        ↓
        (User có thể làm việc khác)
        ↓
T=3:15  Browser tự động mở lại
        Repeat: fetch 200 products
        ↓
T=3:30  Analysis running
        CSV export
        ↓
T=3:31  DONE! 
        Terminal show: "Results in data/output/"
        Browser đóng
```

---

## 🤖 Browser Automation Details:

### Browser được control như thế nào?

**Playwright library:**
- Industry-standard automation tool (by Microsoft)
- Giống Selenium nhưng modern hơn
- Control browser qua code:

```python
# Example code:
browser = await playwright.chromium.launch()
page = await browser.new_page()

# Tự động navigate
await page.goto('https://tiktok.com/shop/product/...')

# Tự động scroll
await page.evaluate('window.scrollTo(0, 500)')

# Tự động extract text
title = await page.inner_text('h1')
sold = await page.inner_text('[class*="sold"]')

# Tự động click (nếu cần)
await page.click('button')
```

**User không cần viết code này** - đã có sẵn trong tool!

---

## 💼 Deployment Options:

### Option 1: Run trên máy user (Recommended)

**Setup:**
- User cài tool trên laptop/desktop
- Chạy khi cần

**Pros:**
- Simple setup
- Full control
- No server costs

**Cons:**
- Máy phải bật khi chạy

---

### Option 2: Run trên VPS/Cloud

**Setup:**
- Rent VPS ($5-10/month)
- Install tool trên VPS
- Schedule với cron

**Pros:**
- Chạy 24/7
- Không depend on laptop

**Cons:**
- Extra costs
- Need VPS management

---

### Option 3: Run on Mac Mini / Always-on Computer

**Setup:**
- Có máy luôn bật (office computer)
- Install tool
- Schedule daily runs

**Pros:**
- No cloud costs
- Local data
- Reliable

---

## 📧 EXPLAIN TO SELLER:

```
Hi anh/chị,

Tool này chạy như thế nào:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 CHẠY LOCAL (trên máy anh/chị):

• Command-line tool (terminal)
• Tự động mở Chrome browser
• Browser visible (thấy trên màn hình)
• Tự động navigate + fetch data
• Lưu data local (SQLite + CSV)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👁️ USER THẤY GÌ:

Khi chạy tool:
  1. Chrome window mở
  2. Browser tự động navigate TikTok Shop
  3. User thấy pages đang load (tự động)
  4. Terminal show progress: "1/200... 2/200..."
  5. Done → CSV file ready

User chỉ cần:
  - Chạy 1 command
  - Minimize browser window
  - Làm việc khác
  - 3 giờ sau check CSV

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔒 SECURITY:

• All data local (không lên cloud)
• TikTok cookies local
• User control 100%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💻 REQUIREMENTS:

• Mac/Windows/Linux
• Python 3.8+
• 4GB RAM
• Internet
• TikTok account (free)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Simple, automated, local! 🚀
```

---

**Bạn copy message trên gửi cho họ để họ hiểu rõ! 📨**
