import random
import time


EMOTIONS = ["Happy", "Sad", "Calm", "Excited"]


def generate_emotion():
    return random.choice(EMOTIONS)


def generate_confidence():
    return round(random.uniform(0.70, 0.99), 2)


def simulate_stream(number_of_frames=10, interval=1.0):
    for i in range(number_of_frames):
        emotion = generate_emotion()
        confidence = generate_confidence()

        frame = {
            "timestamp": round(time.time(), 2),
            "emotion": emotion,
            "confidence": confidence
        }

        print(frame)

        time.sleep(interval)


if __name__ == "__main__":
    simulate_stream()