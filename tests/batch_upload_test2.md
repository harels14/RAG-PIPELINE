# Batch Upload Test 2 — pymupdf + PGVector Singleton
**Date:** 2026-04-06  
**Time:** 14:02:04  
**Endpoint:** `POST /documents/upload-batch`  
**Files:** 4 PDFs uploaded simultaneously  
**Wall time:** ~13s

---

## Results

| File | Size | Pages | Chunks | total parse | embeddings+DB | Grand Total |
|------|------|-------|--------|-------------|---------------|-------------|
| יחידה 0 - מושגים בסיסיים.pdf | 379.8 KB | 7 | 14 | 2.37s | 8.71s | ~11.1s |
| יחידה 3 - טיורינג.pdf | 5374.3 KB | 16 | 29 | 5.14s | 5.44s | ~10.6s |
| יחידה 2 - שפות חופשיות הקשר.pdf | 6469.3 KB | 24 | 44 | 6.77s | 4.26s | ~11.0s |
| יחידה 1 - שפות רגולריות.pdf | 6206.1 KB | 48 | 98 | 8.69s | 4.18s | ~12.9s |

---

## שיפורים מהרצה הקודמת

| מדד | Test 1 | Test 2 | שיפור |
|-----|--------|--------|-------|
| Wall time | ~49s | ~13s | **3.8x** |
| Parse rate | ~0.87s/page | ~0.18s/page | **4.8x** |
| Parse — יחידה 1 (48p) | 42.09s | 8.69s | **4.8x** |
| Parse — יחידה 0 (7p) | 16.76s | 2.37s | **7.1x** |
| PGVector init overhead | ~16s (×4 קבצים) | 0s | מבוטל |

---

## Stack

| Component | Solution |
|-----------|----------|
| PDF parsing | `pymupdf` (fitz) — טקסט + טבלאות בפתיחה אחת |
| DB driver | `psycopg2` |
| Vector store | `PGVector` singleton — מאותחל פעם אחת בהפעלה |
| Embeddings | `OpenAIEmbeddings` — 4 קריאות נפרדות ל-OpenAI (קובץ per קובץ) |
| OpenAI calls | 4 |
