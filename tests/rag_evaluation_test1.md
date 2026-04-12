# RAG Evaluation Test 1 — Semantic vs Hybrid Search

**Date:** 2026-04-12  
**Documents:** מצגות קורס מודלים חישוביים  
**Tool:** RAGAS v0.2  
**LLM:** gpt-4o-mini  
**Embeddings:** text-embedding-3-small  
**Retrieval k:** 5  

---

## Questions Used

1. מהם הנושאים הנלמדים בקורס?
2. מהן דרישות הקורס ואיך מחושב הציון הסופי?
3. מה ההבדל בין אוטומט סופי דטרמיניסטי לאוטומט לא דטרמיניסטי?
4. מה זה מכונת טיורינג ומה היא מסוגלת לחשב?
5. אילו בעיות הן בלתי כריעות?
6. מה ההבדל בין מחלקות הסיבוכיות P ו-NP?
7. מתי יש להגיש את העבודות ומה מדיניות האיחורים?

*No ground truths provided — 3 metrics only.*

---

## Results

| Metric | Semantic | Hybrid | Delta | Winner |
|--------|----------|--------|-------|--------|
| faithfulness | 0.6772 | 0.8592 | +0.182 | **Hybrid** |
| answer_relevancy | 0.3948 | 0.2959 | -0.099 | Semantic |
| llm_context_precision_without_reference | 0.5087 | 0.4143 | -0.094 | Semantic |

---

## Analysis

### Faithfulness (+0.182 for Hybrid)
The most important metric. Hybrid retrieval (pgvector + PostgreSQL FTS fused with RRF k=60)
grounds the LLM's answers significantly better in the retrieved context.
This means fewer hallucinations in production when using hybrid search.

### Answer Relevancy (low across both — 0.39 / 0.30)
Both scores are below acceptable threshold (~0.7). Root cause is **not** the retrieval method —
it's the prompt. The strict "answer based only on the context below" instruction causes the model
to produce evasive or incomplete answers when the retrieved chunks are only partially relevant.
Also, k=5 may be too few chunks for multi-part questions like "what are the course topics?".

### Context Precision (semantic slightly better)
BM25/FTS introduces keyword-relevant but topically noisy chunks. These lower-quality chunks
push down the precision score even though RRF deprioritises them. Increasing k gives RRF
more room to push noise to the bottom.

---

## Identified Issues & Fixes

| Issue | Fix | Status |
|-------|-----|--------|
| Prompt too restrictive → low answer_relevancy | Allow model to say what it knows and what's missing | Applied in Test 2 |
| k=5 too low → noisy hybrid results | Increase k to 7 | Applied in Test 2 |

---

## Stack at Time of Test

- Retrieval: `langchain_postgres.PGVector` (semantic) + PostgreSQL `tsvector` FTS (hybrid)
- Fusion: Reciprocal Rank Fusion, rrf_k=60
- Chunking: `RecursiveCharacterTextSplitter`, chunk_size=1000, overlap=100
- Prompt: `"Answer the question based only on the context below."`
