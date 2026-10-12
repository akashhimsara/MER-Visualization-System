import asyncio
import math
from typing import Any, Dict, List, Optional


def create_mock_tier1_event(session_id: str, sequence: int, audio_time_ms: int) -> Dict[str, Any]:
    """
    Generate a deterministic MER Tier 1 event conforming to Contract v1.1.
    Cadence: ~100 ms
    """
    rms = round(0.25 + 0.15 * math.sin(sequence * 0.1), 4)
    spectral_centroid = round(1500.0 + 500.0 * math.cos(sequence * 0.05), 2)
    
    is_onset = (sequence % 5 == 0)
    onset_strength = round(0.5 + 0.3 * math.sin(sequence * 0.2), 3) if is_onset else 0.0
    
    is_beat = (sequence % 10 == 0)
    beat_data = {
        "detected": is_beat,
        "strength": round(0.7 + 0.2 * math.cos(sequence * 0.1), 3) if is_beat else None,
    }
    
    return {
        "schema_version": "1.1",
        "event_type": "mer.tier1",
        "session_id": session_id,
        "sequence": sequence,
        "audio_time_ms": audio_time_ms,
        "rms": rms,
        "spectral_centroid_hz": spectral_centroid,
        "onset": {
            "detected": is_onset,
            "strength": onset_strength,
        },
        "beat": beat_data,
    }


def create_mock_tier2_event(session_id: str, sequence: int, audio_time_ms: int) -> Dict[str, Any]:
    """
    Generate a deterministic MER Tier 2 event conforming to Contract v1.1.
    Cadence: ~3000 ms
    """
    tempo_bpm = round(120.0 + 8.0 * math.sin(sequence * 0.25), 1)
    tempo_confidence = round(0.85 + 0.10 * math.cos(sequence * 0.25), 2)
    
    return {
        "schema_version": "1.1",
        "event_type": "mer.tier2",
        "session_id": session_id,
        "sequence": sequence,
        "audio_time_ms": audio_time_ms,
        "tempo_bpm": tempo_bpm,
        "tempo_confidence": tempo_confidence,
    }


def create_mock_tier3_event(session_id: str, sequence: int, audio_time_ms: int) -> Dict[str, Any]:
    """
    Generate a deterministic MER Tier 3 event conforming to Contract v1.1.
    Cadence: ~1000 ms
    """
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
            "confidence": None,
        },
    }


class MockMERScheduler:
    """
    Manages deterministic cadence and per-tier sequence counters for multi-tier MER events.
    Cadence:
    - Tier 1: every 100 ms (every tick)
    - Tier 3: every 1000 ms (every 10 ticks)
    - Tier 2: every 3000 ms (every 30 ticks)
    """

    def __init__(self, session_id: str, step_interval_ms: int = 100):
        self.session_id = session_id
        self.step_interval_ms = step_interval_ms
        self.current_time_ms = 0
        self.step_index = 0
        
        self.tier1_seq = 0
        self.tier2_seq = 0
        self.tier3_seq = 0

    def tick(self) -> List[Dict[str, Any]]:
        events = []
        now_ms = self.current_time_ms
        
        # Tier 1 (~100 ms)
        events.append(create_mock_tier1_event(self.session_id, self.tier1_seq, now_ms))
        self.tier1_seq += 1
        
        # Tier 3 (~1000 ms)
        if self.step_index % 10 == 0:
            events.append(create_mock_tier3_event(self.session_id, self.tier3_seq, now_ms))
            self.tier3_seq += 1
            
        # Tier 2 (~3000 ms)
        if self.step_index % 30 == 0:
            events.append(create_mock_tier2_event(self.session_id, self.tier2_seq, now_ms))
            self.tier2_seq += 1
            
        self.step_index += 1
        self.current_time_ms += self.step_interval_ms
        return events


async def generate_mock_tier3_stream(websocket, session_id: str):
    """
    Legacy standalone Tier 3 generator endpoint helper.
    """
    sequence = 0
    audio_time_ms = 0
    
    while True:
        event = create_mock_tier3_event(session_id, sequence, audio_time_ms)
        await websocket.send_json(event)
        
        sequence += 1
        audio_time_ms += 1000
        await asyncio.sleep(1.0)


async def generate_mock_mer_stream(websocket, session_id: str, interval_s: float = 0.1):
    """
    Multiplexed generator for Tier 1, Tier 2, and Tier 3 over a single WebSocket.
    """
    scheduler = MockMERScheduler(session_id=session_id)
    try:
        while True:
            events = scheduler.tick()
            for event in events:
                await websocket.send_json(event)
            await asyncio.sleep(interval_s)
    except asyncio.CancelledError:
        pass
