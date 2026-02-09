import os
import uuid
import threading
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.manager import FullContextManager

load_dotenv()

app = FastAPI(title="Belediye Chatbot API")

sessions: dict[str, FullContextManager] = {}
sessions_lock = threading.Lock()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    session_id: str
    response: str
    completed: bool


class SessionResponse(BaseModel):
    session_id: str
    data: dict
    next_question: str | None


@app.post("/sessions", response_model=SessionResponse)
def create_session():
    session_id = uuid.uuid4().hex[:8]
    filename = f"data/session_{session_id}.json"

    manager = FullContextManager(filename=filename, reset=True)
    with sessions_lock:
        sessions[session_id] = manager

    return SessionResponse(
        session_id=session_id,
        data=manager.data,
        next_question=manager.last_question,
    )


@app.post("/sessions/{session_id}/chat", response_model=ChatResponse)
def chat(session_id: str, req: ChatRequest):
    with sessions_lock:
        manager = sessions.get(session_id)
    if not manager:
        raise HTTPException(status_code=404, detail="Session not found")

    response = manager.chat(req.message)

    completed = response == "SESSION_COMPLETED_SUCCESSFULLY"

    return ChatResponse(
        session_id=session_id,
        response=response,
        completed=completed,
    )


@app.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: str):
    with sessions_lock:
        manager = sessions.get(session_id)
    if not manager:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse(
        session_id=session_id,
        data=manager.data,
        next_question=manager.last_question,
    )


@app.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    with sessions_lock:
        manager = sessions.pop(session_id, None)
    if not manager:
        raise HTTPException(status_code=404, detail="Session not found")

    if os.path.exists(manager.filename):
        os.remove(manager.filename)

    return {"detail": "Session deleted"}
