import uuid
from fastapi import APIRouter
from services.vector_store import VectorStore

router = APIRouter(prefix="/users", tags=["Users"])

vector_service = VectorStore()

@router.post("/register")
def register():
    return {"user_id": str(uuid.uuid4())}

@router.get("/{user_id}/files")
async def get_files(user_id: str):
    files = await vector_service.get_user_files(user_id)
    return {"files": files}

@router.delete("/{user_id}/files/{file_name}")
async def delete_file(user_id: str, file_name: str):
    await vector_service.delete_file(user_id, file_name)
    return {"status": "deleted", "file_name": file_name}
