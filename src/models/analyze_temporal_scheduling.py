
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = ROOT / "outputs/results"

INPUT_PATTERN = "EXP_TEMPORAL_001_schedule_song_*.csv"

SUMMARY_PATH = (
    RESULTS_DIR / "EXP_TEMPORAL_001_multisong_summary.csv"
)
PER_SONG_PATH = (
    RESULTS_DIR / "EXP_TEMPORAL_001_multisong_per_song.csv"
)

EXPECTED_SONGS = {1637, 1287, 1237, 1205, 1484}
EXPECTED_HOPS = {0.5, 1.0, 2.0}


def simulate_serial_deadlines(group, hop_seconds):
    """
    Simulate a single serial inference worker.

    Jobs arrive at their scheduled audio timestamps.
    Each job starts after both its arrival and the
    previous job's completion.

    Deadline = arrival time + hop_seconds.

    This is an offline scheduling simulation,
    not a real-time execution test.
    """
    group = group.sort_values(
        "audio_time_seconds"
    )

    previous_finish = None
    deadline_misses = 0
    max_completion_delay_ms = 0.0
    max_queue_wait_ms = 0.0

    for row in group.itertuples(index=False):
        arrival = float(row.audio_time_seconds)
        service = float(row.latency_ms) / 1000.0

        start = (
            arrival
            if previous_finish is None
            else max(arrival, previous_finish)
        )

        finish = start + service
        deadline = arrival + hop_seconds

        queue_wait = start - arrival
        completion_delay = finish - arrival

        if finish > deadline + 1e-9:
            deadline_misses += 1

        max_queue_wait_ms = max(
            max_queue_wait_ms,
            queue_wait * 1000.0,
        )

        max_completion_delay_ms = max(
            max_completion_delay_ms,
            completion_delay * 1000.0,
        )

        previous_finish = finish

    return {
        "completion_deadline_misses": deadline_misses,
        "max_queue_wait_ms": max_queue_wait_ms,
        "max_completion_delay_ms": max_completion_delay_ms,
    }


def main():
    files = sorted(
        RESULTS_DIR.glob(INPUT_PATTERN)
    )

    if len(files) != len(EXPECTED_SONGS):
        raise ValueError(
            f"Expected 5 files, found {len(files)}"
        )

    frames = []

    for path in files:
        df = pd.read_csv(path)

        required = {
            "song_id",
            "hop_seconds",
            "audio_time_seconds",
            "latency_ms",
        }

        if not required.issubset(df.columns):
            raise ValueError(
                f"Missing columns in {path.name}"
            )

        song_ids = set(
            df["song_id"].astype(int).unique()
        )

        if len(song_ids) != 1:
            raise ValueError(
                f"Expected one song per file: {path.name}"
            )

        song_id = next(iter(song_ids))

        if song_id not in EXPECTED_SONGS:
            raise ValueError(
                f"Unexpected song ID: {song_id}"
            )

        if not path.stem.endswith(
            f"song_{song_id}"
        ):
            raise ValueError(
                f"Filename/song mismatch: {path.name}"
            )

        frames.append(df)

    data = pd.concat(
        frames,
        ignore_index=True,
    )

    if set(data["song_id"].astype(int)) != EXPECTED_SONGS:
        raise ValueError("Song set mismatch")

    if set(data["hop_seconds"].astype(float)) != EXPECTED_HOPS:
        raise ValueError("Hop set mismatch")

    if (
        not np.isfinite(data["latency_ms"]).all()
        or (data["latency_ms"] <= 0).any()
    ):
        raise ValueError("Invalid latency values")

    if data.duplicated(
        ["song_id", "hop_seconds", "audio_time_seconds"]
    ).any():
        raise ValueError("Duplicate scheduled jobs")

    per_song_rows = []

    for (song_id, hop), group in data.groupby(
        ["song_id", "hop_seconds"]
    ):
        times = group["latency_ms"].to_numpy()

        simulation = simulate_serial_deadlines(
            group,
            float(hop),
        )

        per_song_rows.append({
            "song_id": int(song_id),
            "hop_seconds": float(hop),
            "predictions": len(group),
            "mean_latency_ms": float(np.mean(times)),
            "p95_latency_ms": float(
                np.percentile(times, 95)
            ),
            "max_latency_ms": float(np.max(times)),
            "total_inference_seconds": float(
                np.sum(times) / 1000.0
            ),
            **simulation,
        })

    per_song = pd.DataFrame(per_song_rows)

    summary_rows = []

    for hop, group in data.groupby("hop_seconds"):
        times = group["latency_ms"].to_numpy()

        song_group = per_song.loc[
            per_song["hop_seconds"] == hop
        ]

        total_inference = float(
            np.sum(times) / 1000.0
        )

        # Nominal workload for a continuously running
        # schedule at this hop, ignoring audio capture,
        # decoding, other tiers, and system overhead.
        workload_seconds_per_audio_minute = (
            float(np.mean(times)) / 1000.0
        ) * (60.0 / float(hop))

        summary_rows.append({
            "hop_seconds": float(hop),
            "songs": int(group["song_id"].nunique()),
            "predictions": len(group),
            "mean_latency_ms": float(np.mean(times)),
            "p95_latency_ms": float(
                np.percentile(times, 95)
            ),
            "max_latency_ms": float(np.max(times)),
            "total_inference_seconds": total_inference,
            "nominal_inference_seconds_per_audio_minute":
                workload_seconds_per_audio_minute,
            "completion_deadline_misses": int(
                song_group["completion_deadline_misses"].sum()
            ),
            "max_queue_wait_ms": float(
                song_group["max_queue_wait_ms"].max()
            ),
            "max_completion_delay_ms": float(
                song_group["max_completion_delay_ms"].max()
            ),
        })

    summary = pd.DataFrame(summary_rows)

    per_song.to_csv(
        PER_SONG_PATH,
        index=False,
    )

    summary.to_csv(
        SUMMARY_PATH,
        index=False,
    )

    print("===== MULTI-SONG SCHEDULING SUMMARY =====")
    print(summary.to_string(index=False))

    print("\n===== PER-SONG RESULTS =====")
    print(per_song.to_string(index=False))

    print("\nSaved:", PER_SONG_PATH)
    print("Saved:", SUMMARY_PATH)
    print("TEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
