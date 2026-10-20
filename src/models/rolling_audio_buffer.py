
import numpy as np


class RollingAudioBuffer:
    """
    Streaming audio buffer with causal window scheduling.

    Input:
        Mono float audio chunks at the configured sample rate.

    Output:
        Complete context windows at fixed hop intervals.

    No audio capture or model inference is performed here.
    """

    def __init__(
        self,
        sample_rate=24000,
        context_seconds=5.0,
        hop_seconds=1.0,
    ):
        if sample_rate <= 0:
            raise ValueError("sample_rate must be positive")

        if context_seconds <= 0 or hop_seconds <= 0:
            raise ValueError("Context and hop must be positive")

        self.sample_rate = int(sample_rate)

        context_samples = context_seconds * self.sample_rate
        hop_samples = hop_seconds * self.sample_rate

        if not context_samples.is_integer():
            raise ValueError(
                "Context must contain an integer number of samples"
            )

        if not hop_samples.is_integer():
            raise ValueError(
                "Hop must contain an integer number of samples"
            )

        self.context_samples = int(context_samples)
        self.hop_samples = int(hop_samples)

        self.buffer = np.empty(0, dtype=np.float32)

        self.total_samples = 0
        self.next_emit_sample = self.context_samples

    def push(self, chunk):
        """
        Add a new audio chunk and return zero or more ready windows.

        Returns:
            List of dictionaries:
            {
                "audio_time_seconds": float,
                "window": np.ndarray
            }
        """

        audio = np.asarray(chunk, dtype=np.float32)

        if audio.ndim != 1:
            raise ValueError("Expected mono 1D audio chunk")

        if not np.isfinite(audio).all():
            raise ValueError("Audio contains non-finite values")

        if len(audio) == 0:
            return []

        previous_total = self.total_samples

        self.buffer = np.concatenate(
            (self.buffer, audio)
        )

        self.total_samples += len(audio)

        emitted = []

        # Absolute sample index of the first sample in buffer.
        buffer_start = previous_total - (
            len(self.buffer) - len(audio)
        )

        while self.next_emit_sample <= self.total_samples:
            window_start = (
                self.next_emit_sample - self.context_samples
            )

            local_start = window_start - buffer_start
            local_end = local_start + self.context_samples

            if local_start < 0 or local_end > len(self.buffer):
                raise RuntimeError(
                    "Required audio samples are unavailable"
                )

            window = self.buffer[
                local_start:local_end
            ].copy()

            emitted.append({
                "audio_time_seconds":
                    self.next_emit_sample / self.sample_rate,
                "window": window,
            })

            self.next_emit_sample += self.hop_samples

        # Keep only the most recent context-length audio.
        if len(self.buffer) > self.context_samples:
            self.buffer = self.buffer[-self.context_samples:]

        return emitted

    def reset(self):
        """Start a new audio stream."""

        self.buffer = np.empty(0, dtype=np.float32)
        self.total_samples = 0
        self.next_emit_sample = self.context_samples
