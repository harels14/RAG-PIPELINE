"""
RAG Evaluation Service using RAGAS v0.2+.

Metrics (no ground_truth needed):
  - faithfulness:                              Is the answer grounded in the retrieved context?
  - answer_relevancy:                          Is the answer relevant to the question?
  - llm_context_precision_without_reference:   Are the retrieved chunks actually relevant?

Additional metrics (ground_truth required):
  - llm_context_precision_with_reference:  Context precision compared to reference
  - llm_context_recall:                    Were all relevant chunks retrieved?
  - answer_correctness:                    Is the answer factually correct?
"""

import logging
from typing import Optional

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from services.rag import RAGService

logger = logging.getLogger(__name__)

EVAL_PROMPT = ChatPromptTemplate.from_template(
    "Answer the question based only on the context below.\n\n"
    "Context:\n{context}\n\n"
    "Question: {question}"
)

_eval_llm = ChatOpenAI(model="gpt-4o-mini", streaming=False)
_eval_chain = EVAL_PROMPT | _eval_llm | StrOutputParser()


class EvaluationService:
    def __init__(self):
        self.rag = RAGService()

    def _generate_answer(self, docs, question: str) -> str:
        context = "\n\n".join(d.page_content for d in docs)
        return _eval_chain.invoke({"context": context, "question": question})

    def evaluate(
        self,
        userid: str,
        questions: list[str],
        ground_truths: Optional[list[str]] = None,
        retriever_type: str = "semantic",
    ) -> dict:
        try:
            from ragas import evaluate, EvaluationDataset, SingleTurnSample
            from ragas.llms import LangchainLLMWrapper
            from ragas.embeddings import LangchainEmbeddingsWrapper
            from ragas.metrics import (
                Faithfulness,
                AnswerRelevancy,
                LLMContextPrecisionWithoutReference,
                LLMContextPrecisionWithReference,
                LLMContextRecall,
                AnswerCorrectness,
            )
        except ImportError as e:
            raise RuntimeError(
                "RAGAS not installed. Run: pip install ragas datasets"
            ) from e

        if ground_truths and len(ground_truths) != len(questions):
            raise ValueError("ground_truths must have the same length as questions")

        # Wrap LLM and embeddings for RAGAS
        ragas_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o-mini"))
        ragas_embeddings = LangchainEmbeddingsWrapper(
            OpenAIEmbeddings(model="text-embedding-3-small")
        )

        # Build samples
        samples = []
        for i, question in enumerate(questions):
            docs = (
                self.rag.get_relevant_docs_hybrid(userid, question)
                if retriever_type == "hybrid"
                else self.rag.get_relevant_docs(userid, question)
            )
            answer = self._generate_answer(docs, question)

            sample = SingleTurnSample(
                user_input=question,
                response=answer,
                retrieved_contexts=[d.page_content for d in docs],
                reference=ground_truths[i] if ground_truths else None,
            )
            samples.append(sample)
            logger.info("Built sample %d/%d", i + 1, len(questions))

        dataset = EvaluationDataset(samples=samples)

        # Select metrics
        if ground_truths:
            metrics = [
                Faithfulness(llm=ragas_llm),
                AnswerRelevancy(llm=ragas_llm, embeddings=ragas_embeddings),
                LLMContextPrecisionWithReference(llm=ragas_llm),
                LLMContextRecall(llm=ragas_llm),
                AnswerCorrectness(llm=ragas_llm, embeddings=ragas_embeddings),
            ]
        else:
            metrics = [
                Faithfulness(llm=ragas_llm),
                AnswerRelevancy(llm=ragas_llm, embeddings=ragas_embeddings),
                LLMContextPrecisionWithoutReference(llm=ragas_llm),
            ]

        result = evaluate(dataset, metrics=metrics)
        scores_df = result.to_pandas()
        metric_names = [m.name for m in metrics]

        aggregated = {
            name: round(float(scores_df[name].mean()), 4)
            for name in metric_names
        }

        per_question = []
        for i, sample in enumerate(samples):
            per_question.append({
                "question": sample.user_input,
                "answer": sample.response,
                "num_contexts": len(sample.retrieved_contexts),
                "scores": {
                    name: round(float(scores_df[name].iloc[i]), 4)
                    for name in metric_names
                },
            })

        return {
            "retriever": retriever_type,
            "num_questions": len(questions),
            "metrics": aggregated,
            "per_question": per_question,
        }

    def compare(
        self,
        userid: str,
        questions: list[str],
        ground_truths: Optional[list[str]] = None,
    ) -> dict:
        semantic = self.evaluate(userid, questions, ground_truths, retriever_type="semantic")
        hybrid = self.evaluate(userid, questions, ground_truths, retriever_type="hybrid")
        delta = {
            k: round(hybrid["metrics"][k] - semantic["metrics"][k], 4)
            for k in semantic["metrics"]
        }
        return {
            "semantic": semantic["metrics"],
            "hybrid": hybrid["metrics"],
            "delta": delta,
            "winner": {
                k: "hybrid" if delta[k] > 0 else ("semantic" if delta[k] < 0 else "tie")
                for k in delta
            },
        }
