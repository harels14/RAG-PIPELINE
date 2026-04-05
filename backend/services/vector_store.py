from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from fastapi.concurrency import run_in_threadpool
import os

class VectorStore:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        db_url = os.getenv("DATABASE_URL", "")
        self.connection_string = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        self.collection_name = "pdf_documents"

    def get_vector_store(self):
        return PGVector(
            connection=self.connection_string,
            embeddings=self.embeddings,
            collection_name=self.collection_name,
        )
    
    async def save_documents(self, chunks):
        vector_store = self.get_vector_store()
        await run_in_threadpool(vector_store.add_documents, chunks)