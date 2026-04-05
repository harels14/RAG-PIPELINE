from fastapi import APIRouter, UploadFile, File, Form
from services.process import PDFProcessor
from services.vector_store import VectorStore

router = APIRouter(prefix="/documents", tags=["Documents"])

pdf_service = PDFProcessor()
vector_service = VectorStore()

@router.post("/upload")
async def add_document(userid: str = Form(...), file: UploadFile = File(...)):
    chunks = await pdf_service.process_upload(file, userid)

    await vector_service.save_documents(chunks)

    return {
        "status": "success",
        "message": f"Document processed for user {userid}",
        "stats": {
            "chunks_created": len(chunks)
        }
    }




