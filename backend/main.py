from fastapi import FastAPI, File, UploadFile
import uvicorn
import logging
from routes import document_route, user_route, rag_route

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


# https://rag-pipeline-production-b0b8.up.railway.app/docs


app = FastAPI(title = "RAG Pipeline API")

@app.get("/health")
def health_check():
    return {"status" : "Healthy"}


app.include_router(document_route.router)
app.include_router(user_route.router)
app.include_router(rag_route.router)






if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

