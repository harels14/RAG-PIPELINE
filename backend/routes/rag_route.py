from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from services.rag import RAGService

router = APIRouter(prefix="/rag", tags=["RAG"])

rag_service = RAGService()

@router.get("/query")
async def query(userid: str, question: str):
    docs = await run_in_threadpool(rag_service.query, userid, question)
    return {
        "docs_found": len(docs),
        "sources": [d.metadata.get("file_name") for d in docs]
    }
