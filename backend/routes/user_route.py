import uuid
import psycopg2
import bcrypt
import os
from fastapi import APIRouter, Form, HTTPException
from services.vector_store import VectorStore

router = APIRouter(prefix="/users", tags=["Users"])
vector_service = VectorStore()

def get_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

@router.post("/register")
def register(password: str = Form(...)):
    user_id = str(uuid.uuid4())
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO users (user_id, password_hash) VALUES (%s, %s)", (user_id, password_hash))
        conn.commit()
    return {"user_id": user_id}

@router.post("/login")
def login(user_id: str = Form(...), password: str = Form(...)):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT password_hash FROM users WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
    if not row or not bcrypt.checkpw(password.encode(), row[0].encode()):
        raise HTTPException(status_code=401, detail="Invalid user ID or password")
    return {"user_id": user_id}

@router.get("/{user_id}/files")
async def get_files(user_id: str):
    files = await vector_service.get_user_files(user_id)
    return {"files": files}

@router.delete("/{user_id}/files/{file_name}")
async def delete_file(user_id: str, file_name: str):
    await vector_service.delete_file(user_id, file_name)
    return {"status": "deleted", "file_name": file_name}
