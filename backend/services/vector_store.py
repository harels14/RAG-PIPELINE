from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import asyncio
import os

_db_url = os.getenv("DATABASE_URL", "").replace("postgresql://", "postgresql+psycopg://", 1)
_engine = create_async_engine(_db_url, pool_size=5, max_overflow=10)

class VectorStore:
    def __init__(self):
        self._store = PGVector(
            connection=_engine,
            embeddings=OpenAIEmbeddings(model="text-embedding-3-small"),
            collection_name="pdf_documents",
            use_jsonb=True,
        )

    async def save_documents(self, chunks, embed_batch_size: int = 200, db_batch_size: int = 50, max_concurrent: int = 4):
        # embed_batch_size: how many chunks per OpenAI API call (large = fewer calls)
        # db_batch_size: how many rows per INSERT statement (small = avoids query size errors)
        batches = [chunks[i:i + embed_batch_size] for i in range(0, len(chunks), embed_batch_size)]
        semaphore = asyncio.Semaphore(max_concurrent)

        async def save_batch(batch):
            async with semaphore:
                await self._store.aadd_documents(batch, batch_size=db_batch_size)

        await asyncio.gather(*[save_batch(b) for b in batches])

    async def delete_file(self, userid: str, file_name: str):
        async with _engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM langchain_pg_embedding WHERE cmetadata->>'user_id' = :uid AND cmetadata->>'file_name' = :fname"),
                {"uid": userid, "fname": file_name},
            )

    async def delete_all_files(self, userid: str):
        async with _engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM langchain_pg_embedding WHERE cmetadata->>'user_id' = :uid"),
                {"uid": userid},
            )

    async def get_user_files(self, userid: str) -> list[str]:
        async with _engine.connect() as conn:
            result = await conn.execute(
                text("SELECT DISTINCT cmetadata->>'file_name' FROM langchain_pg_embedding WHERE cmetadata->>'user_id' = :uid"),
                {"uid": userid},
            )
            return [row[0] for row in result]
