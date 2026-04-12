from fastapi import APIRouter, UploadFile, File, Form
from services.process import PDFProcessor
from services.vector_store import VectorStore
import asyncio

router = APIRouter(prefix="/documents", tags=["Documents"])

pdf_service = PDFProcessor()
vector_service = VectorStore()

async def _process_and_save(file: UploadFile, userid: str) -> dict:
    """Pipelined: parse next page-batch in subprocess while saving current batch."""
    total_chunks = 0
    file_name = file.filename
    save_task = None

    async for chunks in pdf_service.iter_chunks(file, userid):
        if save_task:
            await save_task
        save_task = asyncio.create_task(vector_service.save_documents(chunks))
        total_chunks += len(chunks)

    if save_task:
        await save_task

    return {"file": file_name, "chunks_created": total_chunks}


@router.post("/upload")
async def add_document(userid: str = Form(...), file: UploadFile = File(...)):
    result = await _process_and_save(file, userid)
    return {"status": "success", **result}

@router.post("/upload-batch")
async def upload_batch(userid: str = Form(...), files: list[UploadFile] = File(...)):
    results = await asyncio.gather(*[_process_and_save(f, userid) for f in files])
    return {"status": "success", "results": list(results)}
