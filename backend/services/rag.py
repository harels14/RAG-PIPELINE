import os
import logging
import psycopg2

from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

_DB_URL = os.getenv("DATABASE_URL", "")


class RAGService:
    def __init__(self):
        connection_string = _DB_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
        self.vector_store = PGVector(
            connection=connection_string,
            embeddings=OpenAIEmbeddings(model="text-embedding-3-small"),
            collection_name="pdf_documents",
        )
        self._ensure_fts_index()

    # ------------------------------------------------------------------
    # Semantic search (original)
    # ------------------------------------------------------------------

    def get_relevant_docs(self, userid: str, question: str, k: int = 7) -> list[Document]:
        """Pure vector similarity search."""
        retriever = self.vector_store.as_retriever(
            search_kwargs={"filter": {"user_id": userid}, "k": k}
        )
        return retriever.invoke(question)

    # ------------------------------------------------------------------
    # Hybrid search: vector + PostgreSQL FTS fused with RRF
    # ------------------------------------------------------------------

    def get_relevant_docs_hybrid(
        self, userid: str, question: str, k: int = 7
    ) -> list[Document]:
        """
        Hybrid retrieval combining:
          1. Dense vector similarity (PGVector)
          2. Sparse full-text search (PostgreSQL tsvector / BM25-style ts_rank)

        Results are merged with Reciprocal Rank Fusion (RRF, k=60).
        Falls back to pure semantic if FTS returns no matches.
        """
        semantic_docs = self.get_relevant_docs(userid, question, k=k)
        fts_docs = self._get_fts_docs(userid, question, k=k)

        if not fts_docs:
            logger.debug("FTS returned no results - using semantic only")
            return semantic_docs

        return self._reciprocal_rank_fusion([semantic_docs, fts_docs], top_k=k)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_fts_docs(self, userid: str, query: str, k: int = 5) -> list[Document]:
        """
        Full-text search using PostgreSQL tsvector.
        Uses ts_rank for scoring (BM25-style relevance).
        """
        sql = """
            SELECT document, cmetadata,
                   ts_rank(
                       to_tsvector('english', document),
                       plainto_tsquery('english', %(query)s)
                   ) AS rank
            FROM langchain_pg_embedding
            WHERE cmetadata->>'user_id' = %(uid)s
              AND to_tsvector('english', document) @@ plainto_tsquery('english', %(query)s)
            ORDER BY rank DESC
            LIMIT %(k)s
        """
        conn = psycopg2.connect(_DB_URL)
        try:
            with conn.cursor() as cur:
                cur.execute(sql, {"query": query, "uid": userid, "k": k})
                rows = cur.fetchall()
        except Exception as e:
            logger.warning("FTS query failed: %s", e)
            return []
        finally:
            conn.close()

        return [Document(page_content=row[0], metadata=row[1]) for row in rows]

    @staticmethod
    def _reciprocal_rank_fusion(
        result_lists: list[list[Document]], top_k: int = 5, rrf_k: int = 60
    ) -> list[Document]:
        """
        Merge multiple ranked result lists using Reciprocal Rank Fusion.

        Score(d) = Σ  1 / (rrf_k + rank_i(d))

        rrf_k=60 is the standard value from the original RRF paper.
        """
        scores: dict[str, dict] = {}

        for result_list in result_lists:
            for rank, doc in enumerate(result_list):
                # Use content hash as a stable dedup key
                doc_key = hash(doc.page_content)
                if doc_key not in scores:
                    scores[doc_key] = {"doc": doc, "score": 0.0}
                scores[doc_key]["score"] += 1.0 / (rrf_k + rank + 1)

        sorted_docs = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
        return [entry["doc"] for entry in sorted_docs[:top_k]]

    def _ensure_fts_index(self) -> None:
        """
        Create a GIN index on the document column for fast full-text search.
        Runs once at startup; safe to call multiple times (IF NOT EXISTS).
        """
        sql = """
            CREATE INDEX IF NOT EXISTS idx_langchain_pg_embedding_fts
            ON langchain_pg_embedding
            USING gin(to_tsvector('english', document))
        """
        try:
            conn = psycopg2.connect(_DB_URL)
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.close()
            logger.info("FTS GIN index ensured on langchain_pg_embedding")
        except Exception as e:
            logger.warning("Could not create FTS index (non-fatal): %s", e)
