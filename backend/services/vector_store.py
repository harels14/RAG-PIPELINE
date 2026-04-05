from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from fastapi.concurrency import run_in_threadpool
import os

class VectorStore:
    def __init__(self):
        db_url = os.getenv("DATABASE_URL", "")
        connection_string = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        self.vector_store = PGVector(
            connection=connection_string,
            embeddings=OpenAIEmbeddings(model="text-embedding-3-small"),
            collection_name="pdf_documents",
        )

    async def save_documents(self, chunks):
        await run_in_threadpool(self.vector_store.add_documents, chunks)
