# Chatbot RAG

A lightweight Retrieval-Augmented Generation (RAG) chatbot for answering questions from uploaded documents. The app accepts PDF, DOCX, TXT, and Markdown files, indexes their content locally, and answers questions using a hybrid retrieval pipeline built with FastAPI, LangChain, ChromaDB, BM25, and Gemini.

## Features

- Upload and process PDF, DOCX, TXT, and Markdown files.
- Persist document embeddings locally in ChromaDB.
- Use hybrid retrieval with:
  - vector similarity search via Chroma
  - BM25 keyword search for lexical matching
  - reciprocal rank fusion to combine both signals
- Generate answers with Gemini using only the retrieved document context.
- Return source filenames and page numbers alongside the answer.
- Frontend built with React + Vite and Markdown rendering for bot responses.

## Tech Stack

- Frontend: React, Vite, CSS, react-markdown
- Backend: Python, FastAPI, LangChain, LangGraph, Uvicorn
- Embeddings: BAAI/bge-small-en-v1.5 via langchain-huggingface
- Vector store: ChromaDB
- Retrieval: BM25Retriever + reciprocal rank fusion
- LLM: Google Gemini via langchain-google-genai

## Project Structure

```text
chatbot rag/
├── backend/
│   ├── ingestion.py         # Parse uploaded documents and index chunks in Chroma
│   ├── main.py              # FastAPI app and API routes
│   ├── retrieval.py         # Hybrid retrieval, prompt construction, Gemini answer generation
│   ├── pyproject.toml       # Python project metadata and dependencies
│   ├── requirements.txt     # Installed Python dependencies
│   ├── .venv/               # Local virtual environment
│   ├── chroma_db/           # Persistent vector database files
│   └── .env                 # Local environment variables (created by you)
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── public/
│   └── src/
│       ├── App.jsx
│       ├── App.css
│       ├── main.jsx
│       ├── index.css
│       └── components/
│           ├── Chat.jsx
│           ├── Message.jsx
│           └── Sidebar.jsx
├── README.md
└── .gitignore
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- npm
- A Gemini API key from Google AI Studio

## Setup

### 1. Backend setup

From the project root:

```bash
cd backend
python -m venv .venv
```

Activate the environment:

- Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

- macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file inside the `backend` folder:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

> The app reads environment variables from the backend directory when you run the server there.

### 2. Frontend setup

In a new terminal:

```bash
cd frontend
npm install
```

## Run the App

### Start the backend

```bash
cd backend
.venv\Scripts\Activate.ps1
python main.py
```

The API runs at:

```text
http://localhost:8000
```

### Start the frontend

```bash
cd frontend
npm run dev
```

The app is available at:

```text
http://localhost:5173
```

## API Endpoints

### GET /health

Checks whether the backend is running.

Example response:

```json
{
  "status": "ok"
}
```

### POST /upload

Uploads a document for indexing.

Request:
- form-data field named `file`
- supported types: PDF, DOCX, TXT, MD

Example response:

```json
{
  "message": "Successfully processed 'paper.pdf' into 42 chunks.",
  "filename": "paper.pdf"
}
```

### POST /chat

Asks a question against the uploaded document set.

Request body:

```json
{
  "question": "What are the main findings of this paper?"
}
```

Response:

```json
{
  "answer": "The paper shows that...",
  "sources": [
    {
      "filename": "paper.pdf",
      "page": 4
    }
  ]
}
```

## Notes

- The backend stores the vector database in `backend/chroma_db` to keep indexed documents available across runs.
- If you upload a new file, the app indexes it into the same persistent collection.
- If Gemini rate limits or quota limits are hit, the backend returns a 429 error with a clear message.

## Common Troubleshooting

- If the backend cannot find a model or dependency, make sure the virtual environment is activated and `pip install -r requirements.txt` has been run.
- If the LLM call fails, confirm the `GEMINI_API_KEY` value is valid and the selected model is available in your Google AI Studio account.
- If the frontend cannot reach the API, ensure the FastAPI server is running on port 8000.
