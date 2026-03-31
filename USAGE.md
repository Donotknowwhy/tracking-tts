# 📖 Hướng dẫn sử dụng TikTok Shop Tracking Tool

## 🎯 Quy trình sử dụng (Workflow)

```
┌────────────────────────────────────────────────┐
│  1. Chuẩn bị danh sách 200 product URLs       │
│     (từ kinh nghiệm/research của bạn)         │
└────────────────┬───────────────────────────────┘
                 ↓
┌────────────────────────────────────────────────┐
│  2. Chạy snapshot đầu tiên (t1)               │
│     python main.py start --input urls.txt     │
│     → Lưu session ID: ví dụ session_id = 1    │
└────────────────┬───────────────────────────────┘
                 ↓
┌────────────────────────────────────────────────┐
│  3. Đợi 3 giờ (hoặc config khác)              │
│     Đặt timer/reminder                         │
└────────────────┬───────────────────────────────┘
                 ↓
┌────────────────────────────────────────────────┐
│  4. Chạy snapshot thứ 2 + analysis (t2)       │
│     python main.py snapshot2 --session-id 1   │
└────────────────┬───────────────────────────────┘
                 ↓
┌────────────────────────────────────────────────┐
│  5. Nhận kết quả                               │
│     - CSV file với ranking                     │
│     - Top 10 keywords                          │
└────────────────────────────────────────────────┘
```

---

## 💼 Kịch bản sử dụng thực tế

### Scenario 1: Research trending products (mỗi ngày)

**Morning (9:00 AM):**
```bash
# Có sẵn file products_today.txt với 200 URLs
python main.py start --input products_today.txt --interval 3

# Output: Session ID = 5
```

**Lunch break (12:00 PM) - Đúng 3 giờ sau:**
```bash
python main.py snapshot2 --session-id 5

# Ngay lập tức nhận được:
# ✅ products_session_5_20260331_120000.csv
# ✅ keywords_session_5_20260331_120000.csv
```

**Phân tích kết quả:**
- Xem top 10-20 products có delta cao nhất
- Xem keywords nào đang trending
- Quyết định stock/promote products nào

---

### Scenario 2: Monitor competitor products

**Setup:**
```bash
# File: competitor_products.txt
# Chứa 50-100 URLs của competitor shop

python main.py start --input competitor_products.txt --interval 2
```

**2 giờ sau:**
```bash
python main.py snapshot2 --session-id [ID]

# Xem competitor nào đang grow nhanh
# Học keywords họ đang dùng
```

---

### Scenario 3: Track multiple batches cùng lúc

```bash
# Morning
python main.py start --input electronics.txt --interval 3  # Session 1
python main.py start --input fashion.txt --interval 3      # Session 2
python main.py start --input beauty.txt --interval 3       # Session 3

# 3 hours later
python main.py snapshot2 --session-id 1
python main.py snapshot2 --session-id 2
python main.py snapshot2 --session-id 3

# So sánh category nào đang hot nhất
```

---

## 📊 Đọc kết quả CSV

### File: `products_session_X.csv`

```csv
rank_by_delta,product_url,product_title,sold_t1,sold_t2,delta,growth_rate,rank_by_growth
1,https://...,Wireless Earbuds Bluetooth,2345,2789,444,18.94%,3
2,https://...,LED Strip Lights RGB,1567,1923,356,22.71%,1
3,https://...,Phone Stand Adjustable,890,1201,311,34.94%,2
...
```

**Giải thích:**
- **Rank 1**: Sản phẩm bán thêm được nhiều nhất (444 units trong 3 giờ)
- **Rank 2**: Bán thêm 356 units
- **growth_rate**: Phần trăm tăng trưởng
- **rank_by_growth**: Rank theo %, products với base nhỏ có thể có % cao

**Action items:**
- Top 10 by delta → Products đang "HOT" ngay bây giờ
- Top 10 by growth_rate → Products "mới nổi" có tiềm năng

---

### File: `keywords_session_X.csv`

```csv
rank,keyword,keyword_type,frequency
1,wireless,unigram,15
2,bluetooth earbuds,bigram,12
3,noise cancelling,bigram,10
4,rgb led strip,trigram,8
...
```

**Insights:**
- "wireless" xuất hiện 15 lần trong top products
- "bluetooth earbuds" là phrase phổ biến
- Có thể dùng để:
  - Tìm products tương tự
  - Optimize product titles của mình
  - Research niche keywords

---

## 🔧 Các tùy chọn nâng cao

### Thay đổi timeframe

```bash
# 1 giờ
python main.py start --input urls.txt --interval 1

# 2 giờ
python main.py start --input urls.txt --interval 2

# 4 giờ (cho products ít volatile)
python main.py start --input urls.txt --interval 4
```

**Khuyến nghị:**
- 1h: cho flash sales, trending nhanh
- 3h: balanced (default)
- 4-6h: cho products ổn định

---

### Test trước khi chạy full batch

```bash
# Test 1 URL để xem scraper hoạt động không
python main.py test --url "https://www.tiktok.com/shop/pdp/1732128313499292514"

# Output:
# Product ID: 1732128313499292514
# Title: ...
# Sold Count: 1234
# Price: $19.99
```

---

### Chạy nhiều sessions

```bash
# Không cần đợi session 1 kết thúc
# Có thể chạy nhiều sessions parallel

python main.py start --input batch1.txt  # Session 1
python main.py start --input batch2.txt  # Session 2

# 3 giờ sau:
python main.py snapshot2 --session-id 1
python main.py snapshot2 --session-id 2
```

---

## 📋 Checklist trước khi gửi cho user

### Prerequisites:
- [ ] Python 3.8+ installed
- [ ] Internet connection
- [ ] Proxy credentials (already configured)

### Files cần có:
- [ ] `product_urls.txt` với 50-300 URLs
- [ ] URLs phải là TikTok Shop US format:
  - ✅ `https://www.tiktok.com/shop/pdp/[product-id]`
  - ✅ `https://www.tiktok.com/shop/pdp/[slug]/[product-id]`
  - ❌ KHÔNG phải TikTok video URLs

### Test checklist:
```bash
# 1. Test proxy
python test_proxy.py
# → Should show US IP

# 2. Test single URL
python main.py test --url "[THEIR_PRODUCT_URL]"
# → Should return title + sold count

# 3. Test small batch (10 URLs)
python main.py start --input test_batch.txt --interval 0.5
# Wait 30 minutes
python main.py snapshot2 --session-id [ID]
# → Should generate CSV
```

---

## 🚨 Known Issues & Solutions

### Issue 1: CAPTCHA Challenge

**Symptom:** Browser shows "Security Check"

**Solution:**
- Browser sẽ mở visible window (not headless)
- Solve CAPTCHA manually 1 lần
- Cookies được lưu → lần sau không cần solve nữa

---

### Issue 2: Some products return "no_sold_count"

**Reason:** 
- Shop ẩn sold count
- Product page format khác

**Solution:**
- Products này sẽ bị skip trong analysis
- Normal behavior, không phải bug

---

### Issue 3: Proxy connection timeout

**Check:**
```bash
python test_proxy.py
```

**If fails:**
- Verify proxy credentials
- Check proxy server status
- Contact proxy provider

---

## 📈 Expected Performance

### Time estimates:

| Products | Time per snapshot | Total for 2 snapshots + 3h wait |
|----------|-------------------|----------------------------------|
| 50       | ~3-5 minutes      | 3h 10m                          |
| 100      | ~6-10 minutes     | 3h 20m                          |
| 200      | ~12-20 minutes    | 3h 40m                          |
| 300      | ~18-30 minutes    | 3h 60m                          |

### Success rate:
- Expected: 90-95% success rate
- 5-10% errors are normal (network issues, product deleted, etc.)

---

## 💡 Tips for best results

1. **Product selection:**
   - Mix categories (electronics, fashion, home, etc.)
   - Mix price ranges (low, mid, high)
   - Include some established + some new products

2. **Timing:**
   - Run during peak TikTok hours (evening US time)
   - Avoid midnight-early morning (low activity)

3. **URL quality:**
   - Verify URLs still work before adding
   - Remove duplicates
   - Clean list = better results

4. **Analysis:**
   - Look at BOTH delta and growth_rate
   - High delta = already popular
   - High growth_rate = emerging trend

---

## 🔄 Workflow tối ưu hàng ngày

```
Day 1:
09:00 → Collect 200 URLs (from research/competitors)
10:00 → Run snapshot 1
13:00 → Run snapshot 2 + get results
13:30 → Analyze results, make decisions

Day 2:
09:00 → Update URL list based on yesterday's insights
10:00 → Run snapshot 1
... repeat
```

---

## 📞 Support Commands

### Check database
```bash
sqlite3 data/tracking.db "SELECT * FROM sessions;"
sqlite3 data/tracking.db "SELECT * FROM analysis WHERE session_id = 1 LIMIT 10;"
```

### Re-export CSV from existing session
```python
# If you lost CSV files, can regenerate from database
from src.database import Database
from src.exporter import export_to_csv

db = Database()
analysis = db.get_analysis(session_id=1)
keywords = db.get_keywords(session_id=1)
export_to_csv(analysis, keywords, session_id=1)
```

---

## ✅ Delivery Checklist

When sending to client:

1. **Zip project:**
```bash
zip -r tts-tracking.zip tts-tracking/ \
  --exclude "*.pyc" \
  --exclude "__pycache__" \
  --exclude "venv/*" \
  --exclude ".git/*" \
  --exclude "data/*" \
  --exclude "browser_data/*"
```

2. **Include:**
   - [ ] All source code
   - [ ] README.md (this file)
   - [ ] USAGE.md (Vietnamese guide)
   - [ ] requirements.txt
   - [ ] Example: test_urls.txt with 2-3 URLs
   - [ ] Config with proxy pre-configured

3. **Document:**
   - [ ] Setup instructions
   - [ ] Example workflow
   - [ ] Expected outputs
   - [ ] Troubleshooting guide

4. **Test before delivery:**
   - [ ] Fresh install in clean directory
   - [ ] Run with test URLs
   - [ ] Verify CSV outputs
   - [ ] Check all commands work
