# 📦 Công Cụ Theo Dõi Sản Phẩm TikTok Shop

Công cụ dùng để theo dõi sản phẩm TikTok Shop US theo thời gian, tìm sản phẩm tăng nhanh theo số lượng đã bán, và xuất báo cáo dễ đọc cho seller.

## 🚀 Bắt Đầu Nhanh

### Cách 1: Tự động hoàn toàn (Khuyến nghị) ⚡

Chỉ cần **1 lệnh**, tool tự chạy toàn bộ:

```bash
# Kích hoạt môi trường ảo
source venv/bin/activate

# Chạy auto (mặc định 3 giờ giữa snapshot 1 và 2)
python auto_track.py product_urls.txt

# Chạy với proxy truyền trực tiếp lúc runtime (không cần sửa config.py)
python auto_track.py product_urls.txt 3 --proxy "http://5.181.164.86:56789:mcilhz1g8m:iLhZ1g8m"
```

Tool sẽ:
1. Chạy snapshot 1 (t1)
2. Chờ theo interval (mặc định 3 giờ)
3. Chạy snapshot 2 (t2)
4. So sánh t1/t2
5. Xuất CSV + Excel vào `data/output/`

**Lưu ý:** Giữ terminal mở trong suốt quá trình.

---

### Cách 2: Chạy thủ công 2 bước 🔧

Phù hợp khi bạn muốn chủ động thời gian:

```bash
# Bước 1: Chụp snapshot đầu
python main.py start --input product_urls.txt

# Bước 2: Sau X giờ, chạy snapshot 2 + phân tích
python main.py snapshot2 --session-id 1
```

Ưu điểm:
- Có thể tắt terminal giữa 2 lần snapshot
- Chủ động chạy nhiều session khác nhau

## 1) Cài Đặt Môi Trường

### Windows (khuyến nghị cho seller)

1. Cài [Python 3.10+](https://www.python.org/downloads/) — khi cài nhớ tick **Add python.exe to PATH**.
2. Giải nén hoặc clone project vào một thư mục (ví dụ `C:\tts-tracking`).
3. **Double-click** `setup_windows.bat` hoặc mở **Command Prompt** trong thư mục project và chạy:

```bat
setup_windows.bat
```

Script sẽ tự: tạo `venv`, cài `requirements.txt`, cài Chromium cho Playwright. Chỉ cần chạy **một lần** (trừ khi đổi máy hoặc xóa `venv`).

Sau đó mỗi lần dùng tool:

```bat
cd C:\đường\dẫn\tts-tracking
venv\Scripts\activate.bat
python auto_track.py product_urls.txt
```

### Mac / Linux (cài tay)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## 2) Đăng Nhập TikTok Một Lần (Rất Quan Trọng)

Để giảm CAPTCHA, hãy login 1 lần:

```bash
python setup_login.py
```

Sau khi login thành công, session được lưu vào `browser_data/` và các lần chạy sau ổn định hơn.

## 3) Chuẩn Bị File URL Sản Phẩm

Tạo file `product_urls.txt`, mỗi dòng 1 URL:

```text
https://www.tiktok.com/view/product/1732275855990363066
https://www.tiktok.com/view/product/1729502354982213419
https://www.tiktok.com/view/product/1729507120960083553
```

## 4) Chạy Tool

### Chạy auto

```bash
python auto_track.py product_urls.txt
```

### Chạy auto với interval tùy chỉnh

```bash
python auto_track.py product_urls.txt 0.0833
```

### Chạy auto với proxy khác ngay lúc chạy

```bash
python auto_track.py product_urls.txt 3 --proxy "http://host:port:user:pass"
```

Hỗ trợ các định dạng proxy:
- `http://host:port:user:pass`
- `http://user:pass@host:port`
- `host:port:user:pass`

Ngoài ra có thể set biến môi trường:

```bash
export TTS_PROXY="http://host:port:user:pass"
python auto_track.py product_urls.txt 3
```

## 5) File Kết Quả

Kết quả nằm trong `data/output/`:

- `products_session_<id>_<timestamp>.csv`: dữ liệu tăng trưởng sản phẩm
- `keywords_session_<id>_<timestamp>.csv`: top keyword từ nhóm sản phẩm tăng tốt
- `report_session_<id>_<timestamp>.xlsx`: báo cáo Excel dễ đọc cho seller

## 📊 Ý Nghĩa Các Chỉ Số

- `sold_t1`: số sold ở snapshot 1
- `sold_t2`: số sold ở snapshot 2
- `delta`: tăng tuyệt đối (`sold_t2 - sold_t1`)
- `growth_rate_percent`: tăng trưởng %
- `rank`: thứ hạng theo mức tăng

## ⚙️ Cấu Hình Quan Trọng

Trong `config.py`:

```python
SCRAPING_CONFIG = {
    "headless": True,   # True: chạy ngầm, không bật cửa sổ browser
}
```

Khuyến nghị:
- `headless=True`: chạy nền, không giật focus màn hình
- `headless=False`: chỉ bật khi cần debug hoặc xử lý CAPTCHA thủ công

## ⚠️ Xử Lý CAPTCHA

Nếu bị CAPTCHA khi chạy headless:
1. Tạm đổi `headless=False`
2. Chạy `python launch_browser.py` để login/verify thủ công
3. Khi session ổn lại, đổi về `headless=True` và chạy tiếp

## 🔍 Lệnh Hữu Ích

```bash
# Test 1 URL
python main.py test --url "https://www.tiktok.com/view/product/1732275855990363066"

# Xuất dữ liệu snapshot 1
python export_snapshot1.py
```

## 🐛 Troubleshooting

### Lỗi thiếu browser Playwright
```bash
playwright install chromium
```

### Tất cả URL đều fail
- Kiểm tra internet
- Kiểm tra proxy
- Test với danh sách URL ngắn trước

### Không lấy được sold count
- Một số sản phẩm ẩn sold count
- Dòng đó vẫn lưu nhưng có thể không dùng để tính keyword

## 📁 Cấu Trúc Thư Mục

```text
tts-tracking/
├── auto_track.py
├── main.py
├── config.py
├── requirements.txt
├── src/
│   ├── scraper.py
│   ├── parser.py
│   ├── database.py
│   ├── analyzer.py
│   └── exporter.py
├── data/
│   ├── tracking.db
│   └── output/
└── browser_data/
```
# tracking-tts
