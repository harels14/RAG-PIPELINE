from fastapi import APIRouter, UploadFile, File, Form
from services.process import PDFProcessor
from services.vector_store import VectorStore
import asyncio

router = APIRouter(prefix="/documents", tags=["Documents"])

pdf_service = PDFProcessor()
vector_service = VectorStore()

@router.post("/upload")
async def add_document(userid: str = Form(...), file: UploadFile = File(...)):
    chunks = await pdf_service.process_upload(file, userid)
    await vector_service.save_documents(chunks)
    return {"status": "success", "file": file.filename, "chunks_created": len(chunks)}

@router.post("/upload-batch")
async def upload_batch(userid: str = Form(...), files: list[UploadFile] = File(...)):
    async def process_one(file: UploadFile):
        chunks = await pdf_service.process_upload(file, userid)
        await vector_service.save_documents(chunks)
        return {"file": file.filename, "chunks_created": len(chunks)}

    results = await asyncio.gather(*[process_one(f) for f in files])
    return {"status": "success", "results": list(results)}
