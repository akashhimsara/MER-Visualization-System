# Member 2 — 50% Viva Demo Checklist

## Demonstration objective

Prove the standalone Member 2 pipeline without Member 1 integration:

`manual emotion sample -> trained mapping model -> Song Visual DNA -> live audio-reactive visual`

## Before the viva

1. Run `npm run build`.
2. Run `npm run verify:mapping-model` and keep the output as evidence.
3. Run `npm run verify:song-dna` and keep the output as evidence.
4. Start the app with `npm run dev`.
5. Prepare three different local audio files. Use files with clearly different sound/energy if possible.

## Live demo sequence

1. Click `HAPPY`. The `MODEL OUTPUT` card must change its predicted particle count, speed, bloom, and colour.
2. Upload Song A. Record the `SONG VISUAL DNA` seed, family, and palette.
3. Press Play. Confirm that `LIVE AUDIO REACTION` changes Bass/Mid/High and periodically shows `BEAT!`.
4. Stop or upload Song B while `HAPPY` remains selected. Record its different DNA seed and palette/family.
5. Repeat with Song C. This demonstrates three song-specific recipes under one emotion.
6. Click `SAD` or `ENERGETIC` and upload/play one song again. Confirm the model output and visual style change.

## Pass criteria

- Four manual emotion presets produce different predicted visual parameters.
- Three different songs under the same emotion produce distinct Visual DNA seeds and recipe values.
- Audio metrics move while a song plays, and beats visibly affect the rendered visual.
- The system remains responsive when Play/Pause is used.

## Correct viva wording

The mapping dataset is a **researcher-created controlled baseline**. The exported model is a **trained baseline mapping model**. Its held-out results measure reproduction of the controlled mapping, not human preference or music-emotion-recognition accuracy.
