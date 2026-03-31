#!/bin/bash

# Package TikTok Shop Tracking Tool for delivery

echo "📦 Packaging TikTok Shop Tracking Tool..."
echo ""

# Create clean package directory
rm -rf package
mkdir -p package/tts-tracking

# Copy source files
echo "Copying source files..."
cp -r src package/tts-tracking/
cp main.py package/tts-tracking/
cp config.py package/tts-tracking/
cp requirements.txt package/tts-tracking/
cp test_proxy.py package/tts-tracking/

# Copy documentation
echo "Copying documentation..."
cp README.md package/tts-tracking/
cp USAGE.md package/tts-tracking/
cp HUONG_DAN_SU_DUNG.md package/tts-tracking/
cp REQUIREMENTS.md package/tts-tracking/
cp PROXY_SETUP.md package/tts-tracking/

# Copy example files
echo "Copying examples..."
cp test_urls.txt package/tts-tracking/

# Create .gitignore
cp .gitignore package/tts-tracking/

# Create data directory structure
mkdir -p package/tts-tracking/data/output

# Create empty __init__.py files
touch package/tts-tracking/src/__init__.py

# Create delivery README
cat > package/tts-tracking/START_HERE.md << 'EOF'
# 🚀 START HERE - Quick Setup

## Step 1: Setup (chỉ làm 1 lần)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Step 2: Test proxy
```bash
python test_proxy.py
```
Should show US IP (Los Angeles)

## Step 3: Prepare your product URLs
Edit `product_urls.txt` with your URLs (one per line)

## Step 4: Run first snapshot
```bash
python main.py start --input product_urls.txt
```
Note the Session ID!

## Step 5: Wait 3 hours, then run:
```bash
python main.py snapshot2 --session-id [YOUR_SESSION_ID]
```

## Step 6: Check results
CSV files in `data/output/` folder

---

📖 **Read full guide:**
- English: `USAGE.md`
- Tiếng Việt: `HUONG_DAN_SU_DUNG.md`

🔧 **Technical details:**
- Requirements: `REQUIREMENTS.md`
- Proxy setup: `PROXY_SETUP.md`
EOF

# Create archive
echo "Creating zip archive..."
cd package
zip -r ../tts-tracking-delivery.zip tts-tracking/ \
  --exclude "*.pyc" \
  --exclude "__pycache__/*" \
  --exclude ".DS_Store"

cd ..

# Show result
echo ""
echo "✅ Package created: tts-tracking-delivery.zip"
echo "📦 Size: $(du -h tts-tracking-delivery.zip | cut -f1)"
echo ""
echo "Contents:"
unzip -l tts-tracking-delivery.zip | head -20

echo ""
echo "🎁 Ready to deliver!"
echo "   File: tts-tracking-delivery.zip"
echo "   Send to client with START_HERE.md instructions"
