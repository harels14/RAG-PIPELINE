from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile
from fastapi.concurrency import run_in_threadpool
import uvicorn
import logging
from routes import document_route, user_route, rag_route, evaluation_route

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


# https://rag-pipeline-production-b0b8.up.railway.app/docs

# runs ensure_fts_index in threadpool so it doesnt block the main thread
@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_in_threadpool(rag_route.rag_service.ensure_fts_index)
    yield


app = FastAPI(title="RAG Pipeline API", lifespan=lifespan)

@app.get("/health")
def health_check():
    return {"status" : "Healthy"}


app.include_router(document_route.router)
app.include_router(user_route.router)
app.include_router(rag_route.router)
app.include_router(evaluation_route.router)






if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

