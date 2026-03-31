# 📌 TikTok Shop Product Tracking Tool – Base Version Spec

## 🎯 Objective
Build a lightweight tool to:
- Track selected TikTok Shop products over a short time window (1–2 hours)
- Detect which products are increasing in sold count the fastest
- Extract keywords from top-performing products

---

# 🧩 BASE VERSION (MVP)

## 1. Input

- List of TikTok Shop product URLs
- Recommended size:
  - 50 – 300 products per run

---

## 2. Core Flow

### Step 1: Snapshot at t1
- Fetch product page
- Extract:
  - product_id (or URL)
  - product_title
  - sold_count (s1)
- Store data in database

---

### Step 2: Delayed Re-check (t2)
- After X time (1–2 hours):
  - Re-fetch same product list
  - Extract sold_count again (s2)

---

### Step 3: Compute Growth
- For each product:
  - delta = s2 - s1
  - growth_rate = delta / max(s1, 1)

---

### Step 4: Ranking
- Sort products by:
  - delta DESC
- Optional:
  - filter delta > threshold (e.g. > 5)

---

### Step 5: Keyword Extraction
- Input:
  - product_title
- Process:
  - lowercase
  - remove stopwords
  - split into:
    - 1-word
    - 2-word
    - 3–4 word phrases
- Output:
  - keyword frequency count

---

### Step 6: Output

#### CSV format:
Columns:
- product_url
- product_title
- sold_t1
- sold_t2
- delta
- growth_rate

#### Keyword file:
- keyword
- frequency

Optional:
- Telegram notification:
  - Top N products (e.g. Top 10)

---

## 3. Tech Stack (Suggested)

- Language:
  - Python (recommended)
- Crawling:
  - Playwright / Requests + parsing
- Storage:
  - SQLite (simple, local)
- Scheduler:
  - cron / background job

---

## 4. System Constraints

- No login required (public data only)
- No proxy in base version
- Limit request rate:
  - add delay (1–3s per request)

---

## 5. Error Handling

- Retry failed requests (max 2–3 times)
- Skip product if:
  - cannot fetch sold_count
- Log errors for debugging

---

## 6. Performance Target

- 100–300 products:
  - complete within reasonable time (<10–15 minutes per batch)

---

## ⚠️ LIMITATIONS (BASE)

- Depends on input quality (user-selected products)
- No automatic product discovery
- Only compares 2 timestamps (no long-term tracking)
- Not real-time (<1h)

---

# 🚀 PRO VERSION (SCALING ROADMAP)

## Phase 2 – Enhanced Tracking

### Features:
- Multi-time tracking:
  - t1 → t2 → t3 → t4
- Historical storage:
  - track trends over time
- Growth curve analysis

---

## Phase 3 – Smart Filtering

### Add:
- Threshold alerts:
  - notify if delta > X
- Auto-ranking:
  - top trending per batch
- Keyword trend comparison:
  - rising vs stable keywords

---

## Phase 4 – Product Discovery

### New capabilities:
- Crawl product listing pages
- Detect:
  - new products
  - fast-growing products
- Combine with tracking system

---

## Phase 5 – Shop Intelligence

### Advanced:
- Track selected shops
- Detect:
  - newly published products
- Monitor:
  - early sales velocity

---

## Phase 6 – Scaling System

### Required upgrades:
- Queue system (Celery / Redis)
- Batch processing
- Proxy pool (if needed)
- Parallel crawling

---

## Phase 7 – SaaS Model

### Add:
- Multi-user support
- Dashboard (optional)
- API layer
- Subscription system

---

# 💡 OPTIMIZATION IDEAS

## 1. Reduce Risk of Blocking
- Random delay between requests
- Rotate headers
- Limit batch size

---

## 2. Improve Data Quality
- Normalize sold_count format
- Handle edge cases:
  - hidden sold
  - range values (e.g. "1k+")

---

## 3. Keyword Quality
- Remove generic words:
  - "shirt", "gift", "cotton"
- Focus on:
  - niche keywords
  - names / events / trends

---

## 4. Smart Metrics (Optional)
- velocity_score = delta / time_window
- weighted_score:
  - combine delta + keyword frequency

---

# 🧾 FINAL GOAL

Base version should:
- Work reliably
- Produce usable insights
- Be simple and fast to iterate

Pro version should:
- Expand coverage
- Improve accuracy
- Enable early trend detection at scale

---

# 🎯 TARGET MARKET

- **Platform:** TikTok Shop US
- **Language:** English
- **Market:** United States
- **Use case:** Track trending products, identify fast-growing items, extract keyword patterns
