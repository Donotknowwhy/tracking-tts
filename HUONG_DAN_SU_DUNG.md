# 🇻🇳 Hướng dẫn sử dụng - TikTok Shop Product Tracking

## 📦 Bước 1: Cài đặt

### 1.1. Kiểm tra Python
```bash
python3 --version
# Cần Python 3.8 trở lên
```

### 1.2. Giải nén và vào thư mục
```bash
unzip tts-tracking.zip
cd tts-tracking
```

### 1.3. Cài đặt dependencies
```bash
# Tạo môi trường ảo (virtual environment)
python3 -m venv venv

# Kích hoạt môi trường
source venv/bin/activate        # Mac/Linux
# HOẶC
venv\Scripts\activate           # Windows

# Cài đặt packages
pip install -r requirements.txt

# Cài Playwright browser
playwright install chromium
```

**Lưu ý:** Chỉ cần làm bước này 1 lần duy nhất.

---

## 🚀 Bước 2: Chuẩn bị danh sách sản phẩm

Tạo file `product_urls.txt` chứa URL sản phẩm (1 URL/dòng):

```
https://www.tiktok.com/shop/pdp/1732128313499292514
https://www.tiktok.com/shop/pdp/vintage-tee/1732128311479866210
https://www.tiktok.com/shop/pdp/wireless-headphones/1234567890123456789
...
(200 URLs total)
```

**Tips:**
- Dùng 50-300 URLs / lần chạy
- 200 URLs là số lượng tối ưu (balance giữa thời gian và insights)
- URL phải từ TikTok Shop US (không phải video TikTok)

---

## ▶️ Bước 3: Chạy lần đầu (Snapshot 1)

```bash
python main.py start --input product_urls.txt
```

### Kết quả mong đợi:

```
2026-03-31 10:00:00 - INFO - Starting browser with persistent context
2026-03-31 10:00:05 - INFO - Progress: 1/200
2026-03-31 10:00:12 - INFO - Progress: 2/200
...
2026-03-31 10:15:30 - INFO - Processed 200/200 - Success: 195

================================================================================
✅ FIRST SNAPSHOT COMPLETED
================================================================================
Session ID: 1
Products fetched: 195/200 successful
Errors: 5

⏰ Run second snapshot at: 2026-03-31 13:00:00

Command:
  python main.py snapshot2 --session-id 1
================================================================================
```

**Quan trọng:** 
- Lưu lại **Session ID** (ví dụ: 1)
- Lưu lại thời gian chạy snapshot 2 (ví dụ: 13:00:00)

---

## ⏰ Bước 4: Chờ 3 giờ

Đặt reminder/alarm để chạy lại đúng 3 giờ sau.

**Tại sao 3 giờ?**
- Đủ dài để thấy tín hiệu tăng trưởng rõ ràng
- Không quá lâu → không bỏ lỡ trends
- Configurable: có thể đổi thành 1h, 2h, 4h

---

## 📊 Bước 5: Chạy lần 2 và nhận kết quả

```bash
python main.py snapshot2 --session-id 1
```

### Output:

```
2026-03-31 13:00:00 - INFO - Running second snapshot for session 1
2026-03-31 13:00:00 - INFO - Re-fetching 200 products
...
2026-03-31 13:15:00 - INFO - Second snapshot completed: 198 success, 2 errors
2026-03-31 13:15:05 - INFO - Analysis completed: 193 products compared
2026-03-31 13:15:06 - INFO - Extracted 10 keywords

✅ Products CSV: data/output/products_session_1_20260331_130506.csv
✅ Keywords CSV: data/output/keywords_session_1_20260331_130506.csv

================================================================================
📊 ANALYSIS SUMMARY
================================================================================

🏆 TOP 10 PRODUCTS BY GROWTH (Delta):

1. Wireless Bluetooth Earbuds Noise Cancelling Premium Sound
   Sold: 2345 → 2789 (+444, 18.9% growth)
   URL: https://www.tiktok.com/shop/pdp/...

2. LED Strip Lights RGB Color Changing 50ft Smart App Control
   Sold: 1567 → 1923 (+356, 22.7% growth)
   URL: https://www.tiktok.com/shop/pdp/...

...

--------------------------------------------------------------------------------

🔑 TOP 10 KEYWORDS:

1. wireless (unigram) - 15 occurrences
2. bluetooth (unigram) - 14 occurrences
3. led strip (bigram) - 12 occurrences
4. noise cancelling (bigram) - 10 occurrences
5. rgb lights (bigram) - 9 occurrences
...

================================================================================
```

---

## 📁 Tìm file kết quả

File CSV được lưu trong:
```
tts-tracking/
  └── data/
      └── output/
          ├── products_session_1_20260331_130506.csv  ← Mở file này
          └── keywords_session_1_20260331_130506.csv  ← Mở file này
```

**Mở bằng:**
- Excel
- Google Sheets
- Numbers (Mac)
- Hoặc text editor

---

## 🎯 Cách phân tích kết quả

### A. Tìm sản phẩm đáng chú ý

**Sort by delta (cột 6):**
- Top 10-20 → đây là products đang BÁN CHẠY nhất
- Action: Research sâu hơn về products này
  - Xem reviews
  - Xem video TikTok về product
  - Tìm supplier

**Sort by growth_rate (cột 7):**
- Top 10-20 → products đang TĂNG TRƯỞNG NHANH
- Action: Có thể là trend mới nổi
  - Xem có sustainable không
  - Check competitors có stock không

### B. Phân tích keywords

**High frequency keywords:**
- Cho biết niche nào đang hot
- Dùng để tìm thêm products tương tự
- Optimize listing title của mình

**Example insights:**
```
Keywords: "wireless", "bluetooth", "noise cancelling"
→ Audio products với wireless + noise cancelling đang trending
→ Search thêm products với keywords này
```

---

## 🔄 Quy trình hàng ngày (Recommended)

### Sáng (9:00 AM):
1. Collect 200 product URLs (từ research/categories)
2. Chạy: `python main.py start --input today_urls.txt`
3. Note session ID

### Trưa (12:00 PM):
1. Chạy: `python main.py snapshot2 --session-id [ID]`
2. Download CSV files
3. Analyze trong Excel/Sheets
4. Identify top products và keywords

### Chiều:
1. Research sâu top 10-20 products
2. Find suppliers
3. Make sourcing decisions

---

## ⚙️ Tùy chỉnh (Optional)

### Thay đổi timeframe

Mở file `config.py`, tìm dòng:
```python
"check_interval_hours": 3,
```

Đổi thành:
```python
"check_interval_hours": 2,  # 2 giờ
```

### Thay đổi threshold

```python
"min_delta_threshold": 5,  # Chỉ show products tăng >5 units
```

Đổi thành 10, 20 nếu muốn filter ketat hơn.

### Thay đổi số keywords

```python
"top_n_keywords": 10,
```

Đổi thành 20, 30 nếu muốn nhiều keywords hơn.

---

## 🆘 Xử lý lỗi

### Lỗi: "No module named 'src'"
```bash
# Check bạn đang ở đúng thư mục
pwd
# Should show: .../tts-tracking

# Nếu không, cd vào:
cd /path/to/tts-tracking
```

### Lỗi: "playwright not found"
```bash
# Activate virtual environment trước
source venv/bin/activate
playwright install chromium
```

### Lỗi: "Session not found"
```bash
# Check session ID có đúng không
# List tất cả sessions:
sqlite3 data/tracking.db "SELECT * FROM sessions;"
```

### Tất cả products failed:
```bash
# Test proxy trước:
python test_proxy.py

# Nếu proxy OK, test 1 URL:
python main.py test --url "[URL]"
```

---

## 📞 Contact & Support

Nếu gặp vấn đề:
1. Check file log/error messages
2. Test proxy: `python test_proxy.py`
3. Test single URL: `python main.py test --url "[URL]"`
4. Contact với error message cụ thể

---

## 🎁 Bonus: Script automation (Advanced)

Nếu muốn tự động chạy mỗi ngày:

### Mac/Linux - Cron job:
```bash
# Edit crontab
crontab -e

# Add lines:
0 9 * * * cd /path/to/tts-tracking && ./venv/bin/python main.py start --input daily_urls.txt
0 12 * * * cd /path/to/tts-tracking && ./venv/bin/python main.py snapshot2 --session-id [CALCULATE_FROM_DATE]
```

### Windows - Task Scheduler:
- Tạo 2 scheduled tasks
- Task 1: Run at 9:00 AM
- Task 2: Run at 12:00 PM

---

**🎉 Chúc bạn tracking thành công!**
