# Batch Upload Test 3 — Single Batch Embed + Async Engine
**Date:** 2026-04-06  
**Time:** 14:23:32  
**Endpoint:** `POST /documents/upload-batch`  
**Files:** 4 PDFs uploaded simultaneously  
**Wall time:** ~11s

---

## Results

| File | Size | Pages | Chunks | total parse | Grand Total |
|------|------|-------|--------|-------------|-------------|
| יחידה 0 - מושגים בסיסיים.pdf | 379.8 KB | 7 | 13 | 1.91s | — |
| יחידה 3 - טיורינג.pdf | 5374.3 KB | 16 | 28 | 4.16s | — |
| יחידה 2 - שפות חופשיות הקשר.pdf | 6469.3 KB | 24 | 44 | 4.82s | — |
| יחידה 1 - שפות רגולריות.pdf | 6206.1 KB | 48 | 96 | 6.45s | — |

**Total chunks embedded:** 181 — קריאה אחת ל-OpenAI לכל ה-batch

---

## שיפורים מהרצה הקודמת

| מדד | Test 2 | Test 3 | שיפור |
|-----|--------|--------|-------|
| Wall time | ~13s | ~11s | **1.2x** |
| Parse — יחידה 1 (48p) | 8.69s | 6.45s | **1.3x** |
| Parse — יחידה 0 (7p) | 2.37s | 1.91s | **1.2x** |
| OpenAI API calls | 4 | **1** | **4x פחות round trips** |
| DB connections | psycopg2 pool | SQLAlchemy async engine | async native |

---

## Stack

| Component | Solution |
|-----------|----------|
| PDF parsing | `pymupdf` (fitz) — טקסט + טבלאות בפתיחה אחת |
| DB driver | `psycopg` v3 (async, הdriver הרשמי של langchain-postgres) |
| ORM | SQLAlchemy `create_async_engine` — pool_size=5, max_overflow=10 |
| Vector store | `PGVector(use_jsonb=True)` — engine משותף, aadd_documents |
| Embeddings | `OpenAIEmbeddings` — קריאה אחת לכל ה-batch יחד |
| OpenAI calls | 1 |
