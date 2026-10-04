from src.simulator.structure_stream_simulator import (
    generate_structure_frame,
    simulate_structure_stream
)


frame = generate_structure_frame(
    timestamp=0.0,
    bpm=120
)

assert frame["beat"] is True
assert frame["downbeat"] is True
assert frame["onset"] is True
assert frame["energy_change"] is True


frame = generate_structure_frame(
    timestamp=0.25,
    bpm=120
)

assert isinstance(frame["beat"], bool)
assert isinstance(frame["downbeat"], bool)
assert isinstance(frame["onset"], bool)
assert isinstance(frame["energy_change"], bool)


timestamps = [0.0, 0.25, 0.5, 0.75, 1.0]

stream = simulate_structure_stream(
    timestamps,
    bpm=120
)

assert len(stream) == len(timestamps)

for item in stream:
    assert "beat" in item
    assert "downbeat" in item
    assert "onset" in item
    assert "energy_change" in item


print("Structure stream simulator test passed!")