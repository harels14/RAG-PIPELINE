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
    all_chunks_per_file = await asyncio.gather(*[
        pdf_service.process_upload(f, userid) for f in files
    ])

    all_chunks = [chunk for chunks in all_chunks_per_file for chunk in chunks]
    await vector_service.save_documents(all_chunks)

    return {
        "status": "success",
        "results": [{"file": f.filename, "chunks_created": len(c)} for f, c in zip(files, all_chunks_per_file)]
    }




