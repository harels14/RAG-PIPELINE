import tempfile
import os
from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

class PDFProcessor():
    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

    async def process_upload(self, file: UploadFile, userid: str):
        content = await file.read()
        file_name = file.filename

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(content)
            temp_path = temp_pdf.name

        try:
            chunks = await run_in_threadpool(self._parse_pdf, temp_path, userid, file_name)
            return chunks
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def _parse_pdf(self, file_path: str, userid: str, file_name: str):
        loader = PyPDFLoader(file_path)
        pages = loader.load()

        chunks = self.splitter.split_documents(pages)

        for chunk in chunks:
            chunk.metadata["user_id"] = userid
            chunk.metadata["file_name"] = file_name

        return chunks