# Performance Test — Batch Upload
**Date:** 2026-04-06  
**Endpoint:** `POST /documents/upload-batch`  
**Files:** 4 PDFs uploaded simultaneously

---

## Before (PyPDFLoader + pdfplumber + PGVector per-file)

| File | Pages | Chunks | total parse | embeddings+DB | Grand Total |
|------|-------|--------|-------------|---------------|-------------|
| יחידה 0 - מושגים בסיסיים.pdf | 7 | 19 | 16.76s | 12.82s | ~29.6s |
| יחידה 3 - טיורינג.pdf | 16 | 27 | 25.71s | 8.20s | ~33.9s |
| יחידה 2 - שפות חופשיות הקשר.pdf | 24 | 41 | 33.97s | 7.36s | ~41.3s |
| יחידה 1 - שפות רגולריות.pdf | 48 | 112 | 42.09s | 6.86s | ~49.0s |

**Wall time:** ~49s | PGVector init: ~4s × 4 files = ~16s wasted

---

## After (pymupdf + PGVector singleton)

| File | Pages | Chunks | total parse | embeddings+DB | Grand Total |
|------|-------|--------|-------------|---------------|-------------|
| יחידה 0 - מושגים בסיסיים.pdf | 7 | 14 | 2.37s | 8.71s | ~11.1s |
| יחידה 3 - טיורינג.pdf | 16 | 29 | 5.14s | 5.44s | ~10.6s |
| יחידה 2 - שפות חופשיות הקשר.pdf | 24 | 44 | 6.77s | 4.26s | ~11.0s |
| יחידה 1 - שפות רגולריות.pdf | 48 | 98 | 8.69s | 4.18s | ~12.9s |

**Wall time:** ~13s | PGVector init: once at startup

---

## Summary

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Wall time (4 files) | ~49s | ~13s | **3.8x faster** |
| Parse — יחידה 0 (7p) | 16.76s | 2.37s | **7.1x** |
| Parse — יחידה 1 (48p) | 42.09s | 8.69s | **4.8x** |
| PGVector init overhead | ~16s total | ~0s per upload | eliminated |
| pymupdf rate | — | ~0.18s/page | vs 0.87s/page before |

---

## Changes Made

| File | Change |
|------|--------|
| `services/process.py` | Replaced `PyPDFLoader` + `pdfplumber` with `fitz.open()` (single pass, text + tables) |
| `services/vector_store.py` | `PGVector` initialized once in `__init__` instead of per `_sync_save` call |
| `requirements.txt` | Removed `pypdf`, `pdfplumber` — added `pymupdf` |
