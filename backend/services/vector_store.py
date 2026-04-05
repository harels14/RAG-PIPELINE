from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from fastapi.concurrency import run_in_threadpool
import os

class VectorStore:
    def __init__(self):
        db_url = os.getenv("DATABASE_URL", "")
        self.connection_string = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    def _get_store(self):
        return PGVector(
            connection=self.connection_string,
            embeddings=self.embeddings,
            collection_name="pdf_documents",
        )

    def _sync_save(self, chunks):
        self._get_store().add_documents(chunks)

    def _sync_delete(self, userid: str, file_name: str):
        self._get_store().delete(filter={"user_id": userid, "file_name": file_name})

    async def save_documents(self, chunks):
        await run_in_threadpool(self._sync_save, chunks)

    async def delete_file(self, userid: str, file_name: str):
        await run_in_threadpool(self._sync_delete, userid, file_name)
