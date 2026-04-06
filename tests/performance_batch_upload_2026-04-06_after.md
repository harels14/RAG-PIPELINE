# Performance Test — Batch Upload (After Optimization)
**Date:** 2026-04-06  
**Endpoint:** `POST /documents/upload-batch`  
**Files:** 4 PDFs uploaded simultaneously

---

## Results

| File | Size | Pages | Chunks | pymupdf parse | text split | total parse | embeddings+DB | Grand Total |
|------|------|-------|--------|---------------|------------|-------------|---------------|-------------|
| יחידה 0 - מושגים בסיסיים.pdf | 379.8 KB | 7 | 14 | 2.26s | 0.02s | 2.37s | 8.71s | ~11.1s |
| יחידה 3 - טיורינג.pdf | 5374.3 KB | 16 | 29 | 5.03s | 0.00s | 5.14s | 5.44s | ~10.6s |
| יחידה 2 - שפות חופשיות הקשר.pdf | 6469.3 KB | 24 | 44 | 6.66s | 0.00s | 6.77s | 4.26s | ~11.0s |
| יחידה 1 - שפות רגולריות.pdf | 6206.1 KB | 48 | 98 | 8.57s | 0.01s | 8.69s | 4.18s | ~12.9s |

**Wall time (parallel):** ~13s  
**PGVector init:** once at startup (not per file)

---

## vs Before

| Metric | Before | After |
|--------|--------|-------|
| Wall time | ~49s | ~13s |
| Parse rate | ~0.87s/page | ~0.18s/page |
| PGVector init overhead | ~16s (×4 files) | 0s |
| Overall speedup | — | **3.8x** |
