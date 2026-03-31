# 🌐 HƯỚNG DẪN SETUP PROXY TRÊN CHROME THẬT

## 📋 PROXY INFO:

```
Protocol: HTTP
Server: 5.181.164.86
Port: 56789
Username: mcilhz1g8m
Password: iLhZ1g8m
```

---

## ✅ CÁCH 1: DÙNG SWITCHYOMEGA (RECOMMEND - DỄ NHẤT)

### Step 1: Cài Extension

1. Mở Chrome thật (không phải Chrome for Testing)
2. Vào: https://chromewebstore.google.com/detail/proxy-switchyomega/padekgcemlokbadohgkifijomclgjgif
3. Click **"Add to Chrome"**
4. Confirm: **"Add extension"**

### Step 2: Config Proxy

1. Click icon **SwitchyOmega** trên thanh toolbar (góc trên bên phải)
2. Click **"Options"**
3. Sidebar bên trái → Click **"New profile..."** (dấu +)
   - Name: `TikTok US`
   - Type: **Proxy Profile**
   - Click **Create**

4. Config proxy servers:

   **Row 1 (default):**
   - Scheme: `(default)`
   - Protocol: **`HTTP`** (chọn trong dropdown)
   - Server: `5.181.164.86`
   - Port: `56789`
   - 🔒 Click **lock icon** → nhập:
     - Username: `mcilhz1g8m`
     - Password: `iLhZ1g8m`

   **Row 2 (http://):**
   - Scheme: `http://`
   - Protocol: **`HTTP`**
   - Server: `5.181.164.86`
   - Port: `56789`
   - 🔒 Click **lock icon** → nhập username/password

   **Row 3 (https://):**
   - Scheme: `https://`
   - Protocol: **`HTTP`**
   - Server: `5.181.164.86`
   - Port: `56789`
   - 🔒 Click **lock icon** → nhập username/password

5. **Bypass List:**
   - Để nguyên:
     ```
     127.0.0.1
     ::1
     localhost
     ```

6. Click **"Apply changes"** (nút xanh bên trái dưới)

### Step 3: Enable Proxy

1. Click icon **SwitchyOmega** trên toolbar
2. Chọn profile **"TikTok US"**
3. Icon sẽ đổi màu (confirm đã enable)

### Step 4: Verify

1. Mở tab mới
2. Vào: **https://ipinfo.io**
3. Check:
   - **IP:** `5.181.164.86` ✅
   - **City:** Kansas City
   - **Region:** Missouri
   - **Country:** US 🇺🇸

**Nếu đúng → Proxy work! ✅**

---

## ✅ CÁCH 2: DÙNG CHROME FLAGS (NHANH HƠN)

### Close tất cả Chrome windows

### Chạy Chrome với proxy qua Terminal:

```bash
# Đóng tất cả Chrome trước
pkill "Google Chrome"

# Mở Chrome với proxy
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --proxy-server="http://5.181.164.86:56789" \
  --proxy-auth="mcilhz1g8m:iLhZ1g8m" \
  https://ipinfo.io
```

**Pros:**
- Nhanh, không cần extension
- Toàn bộ Chrome dùng proxy

**Cons:**
- Phải đóng tất cả Chrome windows
- Phải chạy từ terminal
- Không linh hoạt (on/off)

---

## ✅ CÁCH 3: DÙNG MACOS SYSTEM PROXY

### Step 1: Mở System Settings

```
Apple menu → System Settings → Network
```

### Step 2: Config Proxy

1. Chọn connection đang dùng (Wi-Fi hoặc Ethernet)
2. Click **"Details..."**
3. Tab **"Proxies"**
4. Check ✅ **"Web Proxy (HTTP)"**
5. Nhập:
   - Web Proxy Server: `5.181.164.86:56789`
   - Username: `mcilhz1g8m`
   - Password: `iLhZ1g8m`
6. Check ✅ **"Secure Web Proxy (HTTPS)"** (same config)
7. Click **"OK"**

**Pros:**
- Toàn bộ apps dùng proxy
- Chrome tự động dùng

**Cons:**
- ⚠️ TẤT CẢ apps dùng proxy (có thể chậm)
- Khó bật/tắt

---

## 🎯 RECOMMEND:

**CÁCH 1: SwitchyOmega Extension** ⭐⭐⭐⭐⭐

**Why:**
- ✅ Dễ setup (5 phút)
- ✅ Dễ bật/tắt (1 click)
- ✅ Chỉ Chrome dùng proxy (apps khác bình thường)
- ✅ Có thể tạo nhiều profiles

---

## ✅ SAU KHI SETUP PROXY:

### Test workflow:

**1. Verify proxy:**
```
https://ipinfo.io
→ Should see: 5.181.164.86, US
```

**2. Test TikTok:**
```
https://www.tiktok.com
→ Should load (may see CAPTCHA if not logged in)
```

**3. Login TikTok:**
```
Click "Log in" → login với account
```

**4. Test TikTok Shop:**
```
https://www.tiktok.com/shop/pdp/1732128313499292514
→ Should load product (if logged in)
```

**5. Export cookies (sau khi login):**
```
Install: Cookie Editor extension
Export cookies → cookies.json
```

---

## 📧 SUMMARY:

**Fastest way (5 phút):**

1. Install SwitchyOmega
2. New profile "TikTok US"
3. Protocol: HTTP
4. Server: `5.181.164.86:56789`
5. Auth: `mcilhz1g8m` / `iLhZ1g8m`
6. Apply → Enable profile
7. Test: ipinfo.io → should show US IP

---

**Start với CÁCH 1 (SwitchyOmega)!** ⭐
