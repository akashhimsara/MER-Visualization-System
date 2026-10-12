from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.mock_mer import generate_mock_tier3_stream

app = FastAPI(title="Emotion-Adaptive Real-Time Music Visualization System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
