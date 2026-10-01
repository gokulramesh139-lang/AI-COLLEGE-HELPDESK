from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import shutil
import uuid

from .rag import answer_question, collection_count, ingest_pdf


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Karan Arts and Science College AI Helpdesk",
    description="AI-powered college information assistant",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://ai-college-helpdesk-ten.vercel.app",
],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# CHAT REQUEST
# ============================================================

class ChatRequest(BaseModel):

    message: str

    session_id: str | None = None


# ============================================================
# SIMPLE SESSION MEMORY
# ============================================================

sessions = {}


def get_session(session_id):

    if session_id not in sessions:

        sessions[session_id] = []

    return sessions[session_id]


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {

        "message":
            "Karan Arts and Science College AI Helpdesk is running!",

        "status":
            "online",

        "version":
            "1.0.0",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {

        "status":
            "healthy",

        "knowledge_base_documents":
            collection_count(),
    }


# ============================================================
# CHAT
# ============================================================

@app.post("/api/v1/chat")
def chat(request: ChatRequest):

    message = request.message.strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty."
        )

    # Create a session ID if the frontend
    # does not provide one.
    session_id = request.session_id

    if not session_id:
        session_id = str(uuid.uuid4())

    # Get the conversation history.
    history = get_session(session_id)

    # --------------------------------------------------------
    # BUILD SEARCH QUERY
    # --------------------------------------------------------

    # Send only the current question to the RAG system.
    # This prevents previous answers from affecting retrieval.
    context_question = message

    # --------------------------------------------------------
    # SAVE STUDENT MESSAGE
    # --------------------------------------------------------

    history.append(
        {
            "role": "student",
            "message": message
        }
    )

    # --------------------------------------------------------
    # SEARCH KNOWLEDGE BASE
    # --------------------------------------------------------

    result = answer_question(
        context_question
    )

    # --------------------------------------------------------
    # SAVE AI RESPONSE
    # --------------------------------------------------------

    history.append(
        {
            "role": "assistant",
            "message": result["answer"]
        }
    )

    # Keep only the latest 10 messages.
    if len(history) > 10:

        sessions[session_id] = history[-10:]

    # --------------------------------------------------------
    # RETURN RESPONSE TO FRONTEND
    # --------------------------------------------------------
    return {

        "session_id": session_id,
        "answer": result["answer"],
        "sources": result["sources"],
        "confidence": result["confidence"],
        "fallback": result["fallback"],
        "conversation_length": len(
            sessions[session_id]
        )
    }


# ============================================================
# GET CONVERSATION HISTORY
# ============================================================

@app.get("/api/v1/chat/{session_id}")
def get_chat_history(
    session_id: str
):

    history = sessions.get(
        session_id,
        []
    )

    return {

        "session_id":
            session_id,

        "messages":
            history,
    }


# ============================================================
# ADMIN — UPLOAD PDF
# ============================================================

@app.post("/api/v1/admin/documents")
async def upload_document(
    file: UploadFile = File(...)
):

    if not file.filename.lower().endswith(
        ".pdf"
    ):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )


    filename = Path(
        file.filename
    ).name

    destination = (
        DATA_DIR / filename
    )


    with destination.open(
        "wb"
    ) as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )


    try:

        chunks = ingest_pdf(
            destination
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"PDF processing failed: {error}",
        )


    return {

        "message":
            "Document uploaded and indexed successfully.",

        "filename":
            filename,

        "chunks_indexed":
            chunks,
    }


# ============================================================
# ADMIN — KNOWLEDGE BASE STATUS
# ============================================================

@app.get(
    "/api/v1/admin/knowledge-base"
)
def knowledge_base_status():

    return {

        "documents_indexed":
            collection_count(),

        "status":
            "ready",
    }