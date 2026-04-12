import asyncio
import time
import logging
from concurrent.futures import ProcessPoolExecutor
from fastapi import UploadFile
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import fitz

logger = logging.getLogger(__name__)

_executor = ProcessPoolExecutor(max_workers=4)


def _parse_pdf_worker(content: bytes, userid: str, file_name: str):
    splitter = RecursiveCharacterTextSplitter(chunk_size=450, chunk_overlap=50)
    pages = []
    with fitz.open(stream=content, filetype="pdf") as doc:
        for i, page in enumerate(doc):
            text = page.get_text()
            for table in page.find_tables().tables:
                text += "\n" + "\n".join(" | ".join(str(c or "") for c in row) for row in table.extract())
            pages.append(Document(page_content=text, metadata={"page": i, "source": file_name}))
    chunks = splitter.split_documents(pages)
    for chunk in chunks:
        chunk.metadata["user_id"] = userid
        chunk.metadata["file_name"] = file_name
    return chunks


class PDFProcessor:
    async def process_upload(self, file: UploadFile, userid: str):
        t0 = time.perf_counter()
        content = await file.read()
        file_name = file.filename
        logger.info(f"[{file_name}] read file: {time.perf_counter() - t0:.2f}s ({len(content) / 1024:.1f} KB)")

        loop = asyncio.get_running_loop()
        chunks = await loop.run_in_executor(_executor, _parse_pdf_worker, content, userid, file_name)
        logger.info(f"[{file_name}] total parse: {time.perf_counter() - t0:.2f}s → {len(chunks)} chunks")
        return chunks
