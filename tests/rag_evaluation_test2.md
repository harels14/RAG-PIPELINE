# RAG Evaluation Test 2 — Token Chunking + k=7 + Improved Prompt

**Date:** 2026-04-12  
**Documents:** מצגות קורס מודלים חישוביים  
**Tool:** RAGAS v0.2  
**LLM:** gpt-4o-mini  
**Embeddings:** text-embedding-3-small  
**Retrieval k:** 7 (was 5)  
**Chunking:** TokenTextSplitter 256 tokens / overlap 30 (was RecursiveCharacterTextSplitter 450 chars / overlap 50)  
**Prompt:** Updated — model allowed to share partial knowledge instead of being restricted to context only  

---

## Changes Since Test 1

| Change | Reason |
|--------|--------|
| `RecursiveCharacterTextSplitter(450 chars)` → `TokenTextSplitter(256 tokens)` | Character-based splitting is inconsistent — tokens map directly to model context and ensure one idea per chunk |
| k=5 → k=7 | Gives RRF more candidates to rank, pushing FTS noise lower |
| Prompt: "based only on context" → "using context, state what's missing" | Prevent evasive answers when context is partial |

---

## Results

| Metric | Semantic | Hybrid | Delta | Winner |
|--------|----------|--------|-------|--------|
| faithfulness | 0.9076 | 0.9821 | +0.0745 | **Hybrid** |
| answer_relevancy | 0.4310 | 0.2320 | -0.1990 | Semantic |
| llm_context_precision_without_reference | 0.4629 | 0.5502 | +0.0873 | **Hybrid** |

---

## Comparison with Test 1

| Metric | Test 1 Semantic | Test 2 Semantic | Test 1 Hybrid | Test 2 Hybrid |
|--------|----------------|----------------|--------------|--------------|
| faithfulness | 0.677 | **0.908** (+0.230) | 0.859 | **0.982** (+0.123) |
| answer_relevancy | 0.395 | 0.431 (+0.036) | 0.296 | 0.232 (-0.064) |
| context_precision | 0.509 | 0.463 (-0.046) | 0.414 | **0.550** (+0.136) |

---

## Analysis

### Faithfulness — major improvement
TokenTextSplitter produces semantically cleaner chunks (one idea per chunk). The LLM receives
focused context and hallucinates significantly less. Hybrid reaches 0.982 — near perfect.
This is the most important metric for production RAG correctness.

### Context Precision — hybrid now wins
With k=7 and smaller chunks, RRF has enough candidates to rank accurately. Hybrid now outperforms
semantic on precision as well, meaning the top retrieved chunks are more relevant to the question.

### Answer Relevancy — low across both tests, likely a measurement artifact

> **Note — Hebrew documents limitation:**
>
> The `answer_relevancy` metric in RAGAS works by:
> 1. Taking the generated answer (in Hebrew)
> 2. Using an LLM to reverse-engineer what questions that answer would address (generates in English)
> 3. Computing cosine similarity between those generated questions and the original question (in Hebrew)
>
> This cross-language comparison (Hebrew question vs. English-generated questions) produces
> artificially low similarity scores. The metric is not reliable for Hebrew content.
>
> **What can be done:**
> - Supply `ground_truths` in Hebrew — this enables `answer_correctness` instead, which compares
>   the answer directly to a reference answer in the same language (much more reliable for Hebrew)
> - Or pass a custom `llm` to RAGAS configured to respond in Hebrew, so the reverse-engineered
>   questions are also generated in Hebrew
> - There is no way to fully fix `answer_relevancy` for Hebrew without one of these two approaches

---

## Stack at Time of Test

- Retrieval: `langchain_postgres.PGVector` (semantic) + PostgreSQL `tsvector` FTS (hybrid)
- Fusion: Reciprocal Rank Fusion, rrf_k=60, k=7
- Chunking: `TokenTextSplitter`, chunk_size=256 tokens, overlap=30, encoding=cl100k_base
- Prompt: `"Answer the question using the context below. If the context doesn't contain enough information, share what you do know from it and state clearly what's missing."`

---

## Next Steps

| Improvement | Expected Impact | Priority |
|-------------|----------------|----------|
| Add `ground_truths` in Hebrew → unlock `answer_correctness` | Reliable accuracy metric for Hebrew | High |
| Parent Document Retriever (embed 64t, retrieve 256t) | Better context precision | Medium |
| Cross-encoder Reranker (FlashRank) | Better precision, especially for hybrid | Medium |
