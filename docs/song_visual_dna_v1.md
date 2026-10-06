# Song Visual DNA v1

## Goal

Avoid showing one fixed preset for every song with the same detected emotion.
Song Visual DNA is a deterministic variation layer above the trained
Valence-Arousal-to-visual-parameters model.

## Flow

```text
song file metadata + detected emotion + trained base palette
  -> deterministic seed
  -> visual family, palette variation, camera variation, energy profile
  -> real-time Three.js visual world
```

The same uploaded file with the same emotion receives the same recipe. A
different file can receive a different compatible family or parameter
variation. The file metadata fingerprint is an engineering seed, not an audio
embedding or an emotion-recognition feature.

## Current compatible families

| Emotion | Candidate worlds |
| --- | --- |
| CALM | Holographic Core, Cosmic Bloom, Liquid Chrome Galaxy, Neon Mandala, Particle Aurora |
| HAPPY | Neon Mandala, Equalizer Ring, Cosmic Bloom, Liquid Chrome Galaxy, Particle Aurora |
| ENERGETIC | Void Portal, Neon Mandala, Particle Aurora, Liquid Chrome Galaxy |
| SAD | Horizon Grid, Liquid Chrome Galaxy, Holographic Core, Cosmic Bloom, Particle Aurora |

## Boundary

The trained regression model still determines the continuous mood parameters
(colour, density, speed, lighting, bloom). Song Visual DNA chooses a distinct
but compatible rendering identity. It does not replace Member 1's MER model.
