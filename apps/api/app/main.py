from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.mock_mer import generate_mock_tier3_stream, generate_mock_mer_stream
from app.personalization_routes import router as personalization_router

app = FastAPI(title="Emotion-Adaptive Real-Time Music Visualization System")

import os

cors_origins_env = os.getenv("CORS_ORIGINS")
if cors_origins_env:
    allowed_origins = [orig.strip() for orig in cors_origins_env.split(",") if orig.strip()]
else:
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    personalization_router,
    prefix="/api/personalization",
    tags=["personalization"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.websocket("/ws/mock/mer-tier3")
async def websocket_mock_mer_tier3(websocket: WebSocket):
    await websocket.accept()
    session_id = "mock-session-001"
    try:
        await generate_mock_tier3_stream(websocket, session_id)
    except WebSocketDisconnect:
        print(f"Client disconnected from mock stream {session_id}")

@app.websocket("/ws/mock/mer")
async def websocket_mock_mer(websocket: WebSocket):
    await websocket.accept()
    session_id = "mock-session-001"
    try:
        await generate_mock_mer_stream(websocket, session_id)
    except WebSocketDisconnect:
        print(f"Client disconnected from multiplexed mock MER stream {session_id}")
