import tempfile
import os
import time
import logging
from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import fitz

logger = logging.getLogger(__name__)

class PDFProcessor():
    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

    async def process_upload(self, file: UploadFile, userid: str):
        t0 = time.perf_counter()
        content = await file.read()
        file_name = file.filename
        logger.info(f"[{file_name}] read file: {time.perf_counter() - t0:.2f}s ({len(content) / 1024:.1f} KB)")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(content)
            temp_path = temp_pdf.name

        try:
            chunks = await run_in_threadpool(self._parse_pdf, temp_path, userid, file_name)
            logger.info(f"[{file_name}] total parse: {time.perf_counter() - t0:.2f}s → {len(chunks)} chunks")
            return chunks
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def _parse_pdf(self, file_path: str, userid: str, file_name: str):
        t0 = time.perf_counter()
        pages = []
        with fitz.open(file_path) as doc:
            for i, page in enumerate(doc):
                text = page.get_text()
                for table in page.find_tables().tables:
                    text += "\n" + "\n".join(" | ".join(str(c or "") for c in row) for row in table.extract())
                pages.append(Document(page_content=text, metadata={"page": i, "source": file_path}))
        logger.info(f"[{file_name}] pymupdf parse: {time.perf_counter() - t0:.2f}s ({len(pages)} pages)")

        t1 = time.perf_counter()
        chunks = self.splitter.split_documents(pages)
        logger.info(f"[{file_name}] text splitting: {time.perf_counter() - t1:.2f}s → {len(chunks)} chunks")

        for chunk in chunks:
            chunk.metadata["user_id"] = userid
            chunk.metadata["file_name"] = file_name

        return chunks
