from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from fastapi.concurrency import run_in_threadpool
import psycopg2
import logging
import time
import os

logger = logging.getLogger(__name__)

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
        t0 = time.perf_counter()
        store = self._get_store()
        logger.info(f"PGVector init: {time.perf_counter() - t0:.2f}s")

        t1 = time.perf_counter()
        store.add_documents(chunks)
        logger.info(f"embeddings + DB insert ({len(chunks)} chunks): {time.perf_counter() - t1:.2f}s | total save: {time.perf_counter() - t0:.2f}s")

    def _sync_delete(self, userid: str, file_name: str):
        with psycopg2.connect(os.getenv("DATABASE_URL")) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM langchain_pg_embedding
                    WHERE cmetadata->>'user_id' = %s
                    AND cmetadata->>'file_name' = %s
                """, (userid, file_name))
            conn.commit()

    def _sync_get_files(self, userid: str) -> list[str]:
        with psycopg2.connect(os.getenv("DATABASE_URL")) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT cmetadata->>'file_name'
                    FROM langchain_pg_embedding
                    WHERE cmetadata->>'user_id' = %s
                """, (userid,))
                return [row[0] for row in cur.fetchall()]

    async def save_documents(self, chunks):
        await run_in_threadpool(self._sync_save, chunks)

    async def delete_file(self, userid: str, file_name: str):
        await run_in_threadpool(self._sync_delete, userid, file_name)

    async def get_user_files(self, userid: str) -> list[str]:
        return await run_in_threadpool(self._sync_get_files, userid)
