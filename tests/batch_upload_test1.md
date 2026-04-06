# Batch Upload Test 1 — Baseline
**Date:** 2026-04-06  
**Time:** 13:53:09  
**Endpoint:** `POST /documents/upload-batch`  
**Files:** 4 PDFs uploaded simultaneously  
**Wall time:** ~49s

---

## Results

| File | Size | Pages | Chunks | total parse | embeddings+DB | Grand Total |
|------|------|-------|--------|-------------|---------------|-------------|
| יחידה 0 - מושגים בסיסיים.pdf | 379.8 KB | 7 | 19 | 16.76s | 12.82s | ~29.6s |
| יחידה 3 - טיורינג.pdf | 5374.3 KB | 16 | 27 | 25.71s | 8.20s | ~33.9s |
| יחידה 2 - שפות חופשיות הקשר.pdf | 6469.3 KB | 24 | 41 | 33.97s | 7.36s | ~41.3s |
| יחידה 1 - שפות רגולריות.pdf | 6206.1 KB | 48 | 112 | 42.09s | 6.86s | ~49.0s |

---

## שיפורים מהרצה הקודמת

בדיקת baseline — אין השוואה קודמת.

---

## Stack

| Component | Solution |
|-----------|----------|
| PDF parsing | `PyPDFLoader` + `pdfplumber` (שתי פתיחות נפרדות של הקובץ) |
| DB driver | `psycopg2` |
| Vector store | `PGVector` — מאותחל מחדש בכל שמירה (~4s × 4 קבצים = ~16s בזבוז) |
| Embeddings | `OpenAIEmbeddings` — 4 קריאות נפרדות ל-OpenAI |
| OpenAI calls | 4 |
