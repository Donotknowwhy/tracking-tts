@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

cd /d "%~dp0"
echo.
echo ============================================================
echo  TikTok Shop Tracking - Cài đặt môi trường (Windows)
echo ============================================================
echo.

REM Tìm Python: python hoặc py -3 (Python Launcher)
set "PY="
where python >nul 2>&1 && set "PY=python"
if not defined PY (
  where py >nul 2>&1 && set "PY=py -3"
)
if not defined PY (
  echo [LỖI] Không tìm thấy Python.
  echo.
  echo Cài Python 3.10 trở lên từ: https://www.python.org/downloads/
  echo Khi cài, tick "Add python.exe to PATH".
  echo.
  pause
  exit /b 1
)

echo Đang dùng: %PY%
%PY% --version
echo.

echo [1/4] Tạo thư mục ảo venv...
%PY% -m venv venv
if errorlevel 1 (
  echo [LỖI] Không tạo được venv.
  pause
  exit /b 1
)

call "%~dp0venv\Scripts\activate.bat"
if errorlevel 1 (
  echo [LỖI] Không kích hoạt được venv.
  pause
  exit /b 1
)

echo [2/4] Nâng cấp pip...
python -m pip install --upgrade pip
if errorlevel 1 (
  echo [LỖI] pip upgrade thất bại.
  pause
  exit /b 1
)

echo [3/4] Cài package từ requirements.txt...
pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
  echo [LỖI] pip install thất bại.
  pause
  exit /b 1
)

echo [4/4] Cài Chromium cho Playwright (có thể vài phút)...
playwright install chromium
if errorlevel 1 (
  echo [LỖI] playwright install thất bại.
  pause
  exit /b 1
)

echo.
echo ============================================================
echo  Hoàn tất cài đặt.
echo ============================================================
echo.
echo  Các bước tiếp theo:
echo    1. Mở CMD hoặc PowerShell trong thư mục này
echo    2. Chạy:  venv\Scripts\activate.bat
echo    3. Chạy:  python auto_track.py product_urls.txt
echo.
echo  (Tùy chọn) Đăng nhập TikTok một lần:  python setup_login.py
echo.
pause
exit /b 0
