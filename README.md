# College AI Helpdesk

A campus-ready undergraduate AI helpdesk prototype using FastAPI, ChromaDB, Sentence Transformers, and a React frontend.

## Features
- Student chat interface
- PDF knowledge-base ingestion
- Vector search with ChromaDB
- Source citations
- Safe fallback when evidence is insufficient
- Admin document upload endpoint
- Mock knowledge-base data for immediate testing

## Requirements
- Python 3.10+
- Node.js 18+
- npm

## Backend
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend: http://127.0.0.1:8000
API docs: http://127.0.0.1:8000/docs

## Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173

## AI model
The default prototype uses retrieval plus a deterministic grounded response so it works without an API key. To connect an LLM later, implement `generate_answer()` in `backend/app/rag.py`.

## Add documents
Use the Swagger UI `/docs` and POST `/api/v1/admin/documents`, or place PDFs in `backend/data/` and call the ingestion endpoint.

## Project flow
Student -> React -> FastAPI -> ChromaDB retrieval -> grounded response -> sources -> student.
