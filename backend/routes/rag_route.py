from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from services.rag import RAGService
from services.stream import stream_answer
import json

router = APIRouter(prefix="/rag", tags=["RAG"])

rag_service = RAGService()

@router.websocket("/ws")
async def rag_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            userid = data["userid"]
            question = data["question"]

            try:
                docs = await run_in_threadpool(rag_service.get_relevant_docs_hybrid, userid, question)
                async for message in stream_answer(docs, question):
                    await websocket.send_text(json.dumps(message))
            except Exception as e:
                await websocket.send_text(json.dumps({"type": "error", "content": str(e)}))
    except WebSocketDisconnect:
        pass
