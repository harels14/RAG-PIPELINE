from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


class EvaluateRequest(BaseModel):
    userid: str
    questions: list[str]
    ground_truths: Optional[list[str]] = None
    retriever_type: str = "semantic"  # "semantic" | "hybrid"


class CompareRequest(BaseModel):
    userid: str
    questions: list[str]
    ground_truths: Optional[list[str]] = None


@router.post("/run")
def run_evaluation(req: EvaluateRequest):
    """
    Evaluate RAG accuracy with RAGAS metrics.

    - retriever_type="semantic": pure vector similarity (baseline)
    - retriever_type="hybrid":  vector + FTS fused with RRF

    Metrics returned: faithfulness, answer_relevancy, context_precision
    (+ context_recall, answer_correctness if ground_truths provided)
    """
    try:
        from services.evaluation import EvaluationService
        svc = EvaluationService()
        return svc.evaluate(
            userid=req.userid,
            questions=req.questions,
            ground_truths=req.ground_truths,
            retriever_type=req.retriever_type,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
def compare_retrievers(req: CompareRequest):
    """
    Run the same questions through both semantic and hybrid retrieval
    and return a side-by-side metric comparison with deltas.
    """
    try:
        from services.evaluation import EvaluationService
        svc = EvaluationService()
        return svc.compare(
            userid=req.userid,
            questions=req.questions,
            ground_truths=req.ground_truths,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
