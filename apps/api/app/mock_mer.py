import asyncio
import math

def create_mock_tier3_event(session_id: str, sequence: int, audio_time_ms: int):
    # Deterministic mock signal based on sequence
    valence = math.sin(sequence * 0.5)
    arousal = math.cos(sequence * 0.7)
    
    return {
        "schema_version": "1.1",
        "event_type": "mer.tier3",
        "session_id": session_id,
        "sequence": sequence,
        "audio_time_ms": audio_time_ms,
        "emotion": {
            "valence": round(valence, 4),
            "arousal": round(arousal, 4),
            "confidence": None
        }
    }

async def generate_mock_tier3_stream(websocket, session_id: str):
    sequence = 0
    audio_time_ms = 0
    
    while True:
        event = create_mock_tier3_event(session_id, sequence, audio_time_ms)
        await websocket.send_json(event)
        
        sequence += 1
        audio_time_ms += 1000
        await asyncio.sleep(1.0)
