import asyncio
import time
import logging
from concurrent.futures import ProcessPoolExecutor
from fastapi import UploadFile
from langchain_text_splitters import TokenTextSplitter
from langchain_core.documents import Document
import fitz

logger = logging.getLogger(__name__)

_executor = ProcessPoolExecutor(max_workers=4)


def _parse_pdf_page_batch(content: bytes, userid: str, file_name: str, start: int, end: int):
    splitter = TokenTextSplitter(chunk_size=256, chunk_overlap=30, encoding_name="cl100k_base")
    pages = []
    with fitz.open(stream=content, filetype="pdf") as doc:
        for i in range(start, min(end, len(doc))):
            text = doc[i].get_text().replace('\x00', '')
            for table in doc[i].find_tables().tables:
                text += "\n" + "\n".join(" | ".join(str(c or "").replace('\x00', '') for c in row) for row in table.extract())
            pages.append(Document(page_content=text, metadata={"page": i, "source": file_name}))
    chunks = splitter.split_documents(pages)
    for chunk in chunks:
        chunk.metadata["user_id"] = userid
        chunk.metadata["file_name"] = file_name
    return chunks


def _get_page_count(content: bytes) -> int:
    with fitz.open(stream=content, filetype="pdf") as doc:
        return len(doc)


class PDFProcessor:
    async def iter_chunks(self, file: UploadFile, userid: str, page_batch: int = 100):
        """Yields chunk batches as pages are parsed, enabling pipelined save."""
        t0 = time.perf_counter()
        content = await file.read()
        file_name = file.filename
        logger.info(f"[{file_name}] read file: {time.perf_counter() - t0:.2f}s ({len(content) / 1024:.1f} KB)")

        loop = asyncio.get_running_loop()
        total_pages = await loop.run_in_executor(_executor, _get_page_count, content)
        ranges = [(i, i + page_batch) for i in range(0, total_pages, page_batch)]

        for start, end in ranges:
            chunks = await loop.run_in_executor(
                _executor, _parse_pdf_page_batch, content, userid, file_name, start, end
            )
            if chunks:
                yield chunks
