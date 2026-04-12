"""
RAG Evaluation Service using RAGAS.

Metrics (no ground_truth needed):
  - faithfulness:      Is the answer grounded in the retrieved context?
  - answer_relevancy:  Is the answer relevant to the question?
  - context_precision: Are the retrieved chunks actually relevant?

Additional metrics (ground_truth required):
  - context_recall:     Were all relevant chunks retrieved?
  - answer_correctness: Is the answer factually correct?
"""

import logging
from typing import Optional

from langchain_openai import ChatOpenAI
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
            from ragas import evaluate
            from ragas.metrics import faithfulness, answer_relevancy, context_precision
            from datasets import Dataset
        except ImportError as e:
            raise RuntimeError(
                "RAGAS or datasets not installed. Run: pip install ragas datasets"
            ) from e

        if ground_truths and len(ground_truths) != len(questions):
            raise ValueError("ground_truths must have the same length as questions")

        rows = []
        for i, question in enumerate(questions):
            docs = (
                self.rag.get_relevant_docs_hybrid(userid, question)
                if retriever_type == "hybrid"
                else self.rag.get_relevant_docs(userid, question)
            )
            answer = self._generate_answer(docs, question)
            row = {"question": question, "answer": answer, "contexts": [d.page_content for d in docs]}
            if ground_truths:
                row["ground_truth"] = ground_truths[i]
            rows.append(row)
            logger.info("Evaluated question %d/%d", i + 1, len(questions))

        dataset = Dataset.from_list(rows)
        metrics = [faithfulness, answer_relevancy, context_precision]
        if ground_truths:
            from ragas.metrics import context_recall, answer_correctness
            metrics += [context_recall, answer_correctness]

        result = evaluate(dataset, metrics=metrics)
        scores = result.to_pandas()
        metric_names = [m.name for m in metrics]
        aggregated = {name: round(float(scores[name].mean()), 4) for name in metric_names}

        per_question = []
        for i, row in enumerate(rows):
            per_question.append({
                "question": row["question"],
                "answer": row["answer"],
                "num_contexts": len(row["contexts"]),
                "scores": {name: round(float(scores[name].iloc[i]), 4) for name in metric_names},
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
        delta = {k: round(hybrid["metrics"][k] - semantic["metrics"][k], 4) for k in semantic["metrics"]}
        return {
            "semantic": semantic["metrics"],
            "hybrid": hybrid["metrics"],
            "delta": delta,
            "winner": {
                k: "hybrid" if delta[k] > 0 else ("semantic" if delta[k] < 0 else "tie")
                for k in delta
            },
        }
