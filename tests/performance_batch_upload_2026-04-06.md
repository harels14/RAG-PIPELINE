# Performance Test — Batch Upload
**Date:** 2026-04-06  
**Endpoint:** `POST /documents/upload-batch`  
**Files:** 4 PDFs uploaded simultaneously

---

## Raw Results

| File | Size | Pages | Chunks | PyPDFLoader | pdfplumber (table pages) | text split | total parse | PGVector init | embeddings+DB | total save | Grand Total |
|------|------|-------|--------|-------------|--------------------------|------------|-------------|---------------|---------------|------------|-------------|
| יחידה 0 - מושגים בסיסיים.pdf | 379.8 KB | 7 | 19 | 6.83s | 9.91s (0) | 0.00s | 16.76s | 4.54s | 8.27s | 12.82s | ~29.6s |
| יחידה 3 - טיורינג.pdf | 5374.3 KB | 16 | 27 | 14.97s | 10.67s (1) | 0.00s | 25.71s | 4.19s | 4.01s | 8.20s | ~33.9s |
| יחידה 2 - שפות חופשיות הקשר.pdf | 6469.3 KB | 24 | 41 | 22.02s | 11.90s (6) | 0.00s | 33.97s | 4.16s | 3.20s | 7.36s | ~41.3s |
| יחידה 1 - שפות רגולריות.pdf | 6206.1 KB | 48 | 112 | 35.44s | 6.60s (8) | 0.01s | 42.09s | 3.85s | 3.01s | 6.86s | ~49.0s |

**Wall time (parallel):** ~49s  
**Estimated sequential time:** ~154s  
**Parallelism speedup:** 3.1x

---

## Bottleneck Analysis

### 1. PyPDFLoader — ~0.87s/page (dominant bottleneck)
- Accounts for **70–84%** of total parse time
- Scales linearly with page count: 7 pages → 6.83s, 48 pages → 35.44s
- Pure CPU-bound, blocking

### 2. pdfplumber — flat ~6–12s overhead per file
- **יחידה 0: 9.91s with 0 tables found** — full scan with no gain
- Not proportional to table count (8 table pages took 6.6s, 0 table pages took 9.9s)
- Opens the PDF a second time independently of PyPDFLoader

### 3. PGVector init — ~4s per file (unnecessary repetition)
- `_get_store()` called once per file = ~16s wasted across 4 files
- Should be initialized once and reused (singleton)

### 4. Embeddings API — efficient, no action needed
- 112 chunks embedded in 3.01s — good batching
- OpenAI API latency is acceptable

---

## Cost Breakdown (% of grand total, worst case — יחידה 1)

| Stage | Time | % |
|-------|------|---|
| PyPDFLoader | 35.44s | 72% |
| pdfplumber | 6.60s | 13% |
| PGVector init | 3.85s | 8% |
| embeddings+DB | 3.01s | 6% |
| text split + read | 0.05s | <1% |
