from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any

from ingestion import process_and_index_file
from retrieval import answer_query

app = FastAPI(title="RAG Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    question: str

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        chunks_count, filename = process_and_index_file(file)
        return {
            "message": f"Successfully processed '{filename}' into {chunks_count} chunks.",
            "filename": filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    try:
        result = answer_query(request.question)
        return result
    except Exception as e:
        error_text = str(e).lower()
        response = getattr(e, "response", None)
        status_code = getattr(response, "status_code", None)
        if status_code == 429 or "rate limit" in error_text or "rate_limited" in error_text:
            raise HTTPException(
                status_code=429,
                detail="Gemini rate limit or quota reached. Please wait and try again or check your Google AI Studio quota.",
            )
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)