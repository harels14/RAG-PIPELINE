from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
import os

class RAGService:
    def __init__(self):
        db_url = os.getenv("DATABASE_URL", "")
        connection_string = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        self.vector_store = PGVector(
            connection=connection_string,
            embeddings=OpenAIEmbeddings(model="text-embedding-3-small"),
            collection_name="pdf_documents",
        )

    def get_relevant_docs(self, userid: str, question: str):
        retriever = self.vector_store.as_retriever(
            search_kwargs={"filter": {"user_id": userid}, "k": 5}
        )
        return retriever.invoke(question)
