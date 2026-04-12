# RAG Evaluation Test 3 — English Ground Truths + Full RAGAS 5-Metric Suite

**Date:** 2026-04-12  
**Documents:** computional models 700 pages book 
**Tool:** RAGAS v0.2  
**LLM:** gpt-4o-mini  
**Embeddings:** text-embedding-3-small  
**Retrieval k:** 7  
**Chunking:** TokenTextSplitter 256 tokens / overlap 30  
**Prompt:** Updated — model allowed to share partial knowledge instead of being restricted to context only  

---

## Changes Since Test 2

| Change | Reason |
|--------|--------|
| Hebrew questions → English questions | Enable reliable `answer_relevancy` metric (avoids cross-language cosine similarity degradation) |
| Added `ground_truths` | Unlocks `answer_correctness` and `context_recall` — the two most meaningful accuracy metrics |
| 5 metrics instead of 3 | Full RAGAS suite: faithfulness, answer_relevancy, context_precision, context_recall, answer_correctness |

---

## Questions Used

1. What is the formal definition of a deterministic finite automaton (DFA)?
2. What is the difference between a DFA and an NFA, and are they equivalent in power?
3. What languages are recognized by finite automata?
4. State the pumping lemma for regular languages and explain how it is used.
5. What is a context-free grammar and what languages does it generate?
6. What is the Church-Turing thesis?
7. What is the halting problem and why is it undecidable?
8. What is the difference between the complexity classes P and NP?
9. What does it mean for a problem to be NP-complete?
10. What is a Turing machine and how does it compute?

---

## Results

| Metric | Semantic | Hybrid | Delta | Winner |
|--------|----------|--------|-------|--------|
| faithfulness | 0.9667 | 0.8717 | -0.0950 | **Semantic** |
| answer_relevancy | 0.7685 | 0.8783 | +0.1098 | **Hybrid** |
| llm_context_precision_with_reference | 0.8159 | 0.8084 | -0.0075 | **Semantic** |
| context_recall | 0.8167 | 0.8167 | 0 | **Tie** |
| answer_correctness | 0.5874 | 0.6794 | +0.0920 | **Hybrid** |

---

## Comparison with Test 2

| Metric | Test 2 Semantic | Test 3 Semantic | Test 2 Hybrid | Test 3 Hybrid |
|--------|----------------|----------------|--------------|--------------|
| faithfulness | 0.908 | **0.967** (+0.059) | 0.982 | 0.872 (-0.110) |
| answer_relevancy | 0.431 | **0.769** (+0.338) | 0.232 | **0.878** (+0.646) |
| context_precision | 0.463 | **0.816** (+0.353) | 0.550 | 0.808 (+0.258) |

> Note: Test 2 used `llm_context_precision_without_reference`; Test 3 uses `llm_context_precision_with_reference` (ground truths available). Both measure relevance of retrieved context, but the reference-based variant is more reliable.

---

## Analysis

### Answer Relevancy — dramatic improvement
Switching to English questions eliminates the cross-language cosine similarity problem identified in
Test 2. Both scores are now well above the 0.7 threshold. This confirms the Test 1–2 low scores
were a measurement artifact, not a real retrieval problem.

### Answer Correctness — Hybrid wins the metric that matters most
With ground truths available, `answer_correctness` is the most meaningful accuracy signal.
Hybrid (+0.092 over semantic) produces more factually correct answers. This aligns with Hybrid's
higher `answer_relevancy` — it retrieves a broader set of relevant passages that better cover
the question's requirements.

### Faithfulness — Semantic wins, but interpretation is nuanced
Semantic's faithfulness (0.967) is higher than Hybrid's (0.872), yet Hybrid scores better on
correctness and relevancy. This suggests Semantic is faithfully grounding answers in a *narrower*
context, while Hybrid retrieves a richer (slightly noisier) context that leads to better answers
even with a small faithfulness cost. The trade-off favours Hybrid for production use.

### Context Recall — Tie (0.8167)
Both methods retrieve the same proportion of ground-truth-relevant information. The FTS layer
in Hybrid adds keyword precision without increasing recall beyond what vector search already covers.

### Context Precision — near-identical, Semantic marginally better
The 0.0075 gap is negligible. Both methods rank relevant chunks with similar quality.

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
| Parent Document Retriever (embed 64t, retrieve 256t) | Better context precision without losing recall | Medium |
| Cross-encoder Reranker (FlashRank) | Improve faithfulness of Hybrid without sacrificing correctness | Medium |
| Increase ground truth set beyond 10 questions | More statistically reliable metric estimates | Low |
