# Batch Upload Test 4 — ProcessPoolExecutor + Pipeline + fitz In-Memory
**Date:** 2026-04-06  
**Time:** 14:43:58  
**Endpoint:** `POST /documents/upload-batch`  
**Files:** 4 PDFs uploaded simultaneously  
**Wall time:** ~5s

---

## Results

| File | Size | Pages | Chunks | total parse |
|------|------|-------|--------|-------------|
| יחידה 0 - מושגים בסיסיים.pdf | 379.8 KB | 7 | 13 | 0.45s |
| יחידה 3 - טיורינג.pdf | 5374.3 KB | 16 | 27 | 1.23s |
| יחידה 2 - שפות חופשיות הקשר.pdf | 6469.3 KB | 24 | 44 | 2.26s |
| יחידה 1 - שפות רגולריות.pdf | 6206.1 KB | 48 | 95 | 3.90s |

**OpenAI calls:** 4 במקביל — סיימו ב-14:44:03.120 / 03.141 / 03.255 / 03.844

---

## שיפורים מהרצה הקודמת

| מדד | Test 3 | Test 4 | שיפור |
|-----|--------|--------|-------|
| Wall time | ~11s | ~5s | **2.2x** |
| Parse — יחידה 0 (7p) | 1.91s | 0.45s | **4.2x** |
| Parse — יחידה 3 (16p) | 4.16s | 1.23s | **3.4x** |
| Parse — יחידה 2 (24p) | 4.82s | 2.26s | **2.1x** |
| Parse — יחידה 1 (48p) | 6.45s | 3.90s | **1.7x** |
| OpenAI calls | 1 (אחרי כל הפרסור) | 4 (במקביל לפרסור) | pipeline פעיל |

---

## Stack

| Component | Solution |
|-----------|----------|
| PDF parsing | `pymupdf` (fitz) — `ProcessPoolExecutor(max_workers=4)`, ללא temp file |
| fitz input | `fitz.open(stream=content, filetype="pdf")` — ישירות מזיכרון |
| DB driver | `psycopg` v3 (async) |
| ORM | SQLAlchemy `create_async_engine` — pool_size=5, max_overflow=10 |
| Vector store | `PGVector(use_jsonb=True)` |
| Embeddings | `aadd_documents` — קריאה לכל קובץ מיד עם סיום הפרסור שלו |
| OpenAI calls | 4 במקביל |
