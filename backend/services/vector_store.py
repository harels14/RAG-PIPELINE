from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
import os

class VectorStore:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        self.connection_string = os.getenv("DATABASE_URL")
        self.collection_name = "pdf_documents"

    def get_vector_store(self):
        return PGVector(
            connection=self.connection_string,
            embeddings=self.embeddings,
            collection_name=self.collection_name,
            use_jsonb=True 
        )
    
    async def save_documents(self, chunks):
        vector_store = self.get_vector_store()
        await vector_store.add_documents(chunks)