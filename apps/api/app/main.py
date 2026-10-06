from fastapi import FastAPI

app = FastAPI(title="Emotion-Adaptive Real-Time Music Visualization System")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
