# Deploy & Git workflow

## 1. Máy local — đẩy code lên GitHub

```bash
cd /path/to/tts-tracking

# Xem thay đổi
git status
git diff

# Gom commit
git add -A
git commit -m "Mô tả ngắn: ví dụ Web UI, rank by delta, Excel màu theo sold delta"

# Đẩy lên repo đã tạo sẵn (nhánh main)
git push origin main
```

**Lần đầu** nếu chưa có remote:

```bash
git remote add origin https://github.com/<user>/<repo>.git
git branch -M main
git push -u origin main
```

## 2. Server — kéo code và chạy lại

SSH vào VPS, trong thư mục project:

```bash
cd /path/to/tts-tracking
git pull origin main
```

Cập nhật dependency nếu `requirements.txt` đổi:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Giao diện web (React + Ant Design):** build ra `frontend/dist` trước khi chạy uvicorn (cần Node/npm trên server hoặc build trên máy rồi copy `dist/`):

```bash
cd frontend
npm ci
npm run build
cd ..
```

Nếu chưa build, mở `http://...:8000/` sẽ báo 503; API vẫn dùng được tại `/api/...` và `/docs`.

**Dev local (hot reload UI):** terminal 1: `uvicorn web_app:app --reload --port 8000`; terminal 2: `cd frontend && npm run dev` (Vite proxy `/api` và `/files` sang port 8000).

Chạy web (chọn một cách):

```bash
# Trực tiếp (thử nhanh)
uvicorn web_app:app --host 0.0.0.0 --port 8000

# Hoặc script có sẵn
chmod +x scripts/start_web.sh
./scripts/start_web.sh
```

Nên chạy trong **tmux**/**screen** hoặc **systemd** để process không tắt khi thoát SSH.

### Ví dụ systemd (tùy chỉnh path/user)

Tạo `/etc/systemd/system/tts-web.service`:

```ini
[Unit]
Description=TikTok tracking web (uvicorn)
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/path/to/tts-tracking
Environment=PATH=/path/to/tts-tracking/venv/bin
ExecStart=/path/to/tts-tracking/venv/bin/uvicorn web_app:app --host 0.0.0.0 --port 8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Sau đó:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now tts-web
sudo systemctl restart tts-web
```

## 3. File không đưa lên Git (đã có trong `.gitignore`)

- `venv/`, `.env`, `cookies.json`, `data/output/`, `*.db`, `browser_data/`

Trên server: copy `.env` / `cookies.json` thủ công hoặc biến môi trường riêng, **không** commit secret.

## 4. Sau mỗi lần sửa code

Local: `commit` → `push` → Server: `git pull` → `restart` service (hoặc kill + chạy lại uvicorn).
