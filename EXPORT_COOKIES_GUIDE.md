# 🍪 HƯỚNG DẪN EXPORT COOKIES TỪ CHROME THẬT

## ✅ BẠN ĐÃ LOGIN THÀNH CÔNG!

Giờ cần export cookies để tool dùng!

---

## 📋 BƯỚC 1: CÀI COOKIE EDITOR EXTENSION

### Option A: Cookie Editor (RECOMMEND)

1. Trong Chrome thật, vào:
   ```
   https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm
   ```

2. Click **"Add to Chrome"**

3. Click **"Add extension"**

4. Icon sẽ xuất hiện trên toolbar (góc trên phải)

---

## 📋 BƯỚC 2: EXPORT COOKIES

### Trong tab TikTok (đã login):

1. **Vào tab TikTok Shop:**
   ```
   https://www.tiktok.com/shop
   ```
   (Hoặc bất kỳ trang TikTok nào bạn đã login)

2. **Click icon Cookie Editor** trên toolbar

3. **Click "Export"** (góc dưới bên phải popup)

4. **Chọn format:** `JSON` (nếu có lựa chọn)

5. **Click "Export"** hoặc "Copy"

6. **Save as file:**
   - Paste vào text editor
   - Save as: `cookies.json`
   - Location: Desktop hoặc Downloads

---

## 📋 BƯỚC 3: COPY VÀO PROJECT FOLDER

### Chạy lệnh:

```bash
# Nếu save ở Downloads:
cp ~/Downloads/cookies.json /Users/xuankien/Desktop/personal/tts-tracking/

# Hoặc nếu save ở Desktop:
cp ~/Desktop/cookies.json /Users/xuankien/Desktop/personal/tts-tracking/

# Verify:
ls -lh /Users/xuankien/Desktop/personal/tts-tracking/cookies.json
```

**Expected output:**
```
-rw-r--r--  1 xuankien  staff   50K Mar 31 14:15 cookies.json
```

---

## 📋 BƯỚC 4: TEST TOOL VỚI COOKIES!

### Chạy test command:

```bash
cd /Users/xuankien/Desktop/personal/tts-tracking
source venv/bin/activate
python main.py test https://www.tiktok.com/view/product/1732275855990363066
```

**Expected:**
```
✅ Loaded 123 cookies from file!
Fetching: https://www.tiktok.com/view/product/...
✅ Product: [Title]
✅ Sold count: 1234
✅ Price: $19.99
```

**Nếu thấy "Loaded cookies" → SUCCESS!**

---

## 🎯 SAU ĐÓ CHẠY FULL TRACKING:

```bash
python auto_track.py test_urls_new.txt
```

Tool sẽ:
- ✅ Load cookies từ Chrome thật
- ✅ Dùng proxy US
- ✅ Bypass CAPTCHA (90%+)
- ✅ Scrape tất cả URLs
- ✅ Export CSV

---

## ⚠️ LƯU Ý:

### Cookies expire sau 2-4 tuần

Khi tool bắt đầu gặp CAPTCHA trở lại:
1. Login lại trong Chrome thật
2. Export cookies mới
3. Copy vào folder

---

## 🚀 SUMMARY:

**3 bước đơn giản:**

1. **Install Cookie Editor** (30 giây)
2. **Export cookies** từ tab TikTok (30 giây)
3. **Copy vào folder tool** (10 giây)

**Total: 1 phút!**

---

**Start với Install Cookie Editor extension! 📦**
