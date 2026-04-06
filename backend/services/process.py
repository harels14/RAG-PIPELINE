import tempfile
import os
import time
import logging
from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pdfplumber

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

    def _extract_tables(self, file_path: str, file_name: str) -> dict[int, str]:
        t0 = time.perf_counter()
        tables_by_page = {}
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                if tables:
                    table_text = ""
                    for table in tables:
                        for row in table:
                            table_text += " | ".join(cell or "" for cell in row) + "\n"
                    tables_by_page[i] = table_text
        logger.info(f"[{file_name}] pdfplumber table extraction: {time.perf_counter() - t0:.2f}s ({len(tables_by_page)} pages with tables)")
        return tables_by_page

    def _parse_pdf(self, file_path: str, userid: str, file_name: str):
        t0 = time.perf_counter()
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        logger.info(f"[{file_name}] PyPDFLoader: {time.perf_counter() - t0:.2f}s ({len(pages)} pages)")

        tables_by_page = self._extract_tables(file_path, file_name)

        for i, page in enumerate(pages):
            if i in tables_by_page:
                page.page_content += "\n" + tables_by_page[i]

        t1 = time.perf_counter()
        chunks = self.splitter.split_documents(pages)
        logger.info(f"[{file_name}] text splitting: {time.perf_counter() - t1:.2f}s → {len(chunks)} chunks")

        for chunk in chunks:
            chunk.metadata["user_id"] = userid
            chunk.metadata["file_name"] = file_name

        return chunks
