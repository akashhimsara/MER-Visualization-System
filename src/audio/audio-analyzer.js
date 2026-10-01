/**
 * Web Audio API Analyzer for extracting real-time audio frequency energy, 
 * bass kick detection, and amplitude levels from audio files or audio elements.
 */
export class AudioAnalyzer {
  constructor() {
    this.audioContext = null;
    this.analyser = null;
    this.source = null;
    this.audioElement = null;
    this.frequencyData = null;
    this.isInitialized = false;
    this.isPlaying = false;

    // Audio Analysis Parameters
    this.bassEnergy = 0;
    this.midEnergy = 0;
    this.highEnergy = 0;
    this.beatThreshold = 0.65; // Threshold for bass kick detection
    this.lastBeatTime = 0;
  }

  /**
   * Initializes Web Audio Context with an HTML Audio Element.
   * @param {HTMLAudioElement} audioElement 
   */
  init(audioElement) {
    if (this.isInitialized) return;

    this.audioElement = audioElement;
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    this.audioContext = new AudioContextClass();
    this.analyser = this.audioContext.createAnalyser();

    this.analyser.fftSize = 256;
    this.analyser.smoothingTimeConstant = 0.45; // Fast, snappy response to drum beats & bass hits
    this.frequencyData = new Uint8Array(this.analyser.frequencyBinCount);

    this.source = this.audioContext.createMediaElementSource(this.audioElement);
    this.source.connect(this.analyser);
    this.analyser.connect(this.audioContext.destination);

    this.isInitialized = true;
  }

  /**
   * Loads an audio File object from a file input into the audio element.
   * @param {File} file 
   */
  loadAudioFile(file) {
    if (!this.audioElement) return;

    const fileURL = URL.createObjectURL(file);
    this.audioElement.src = fileURL;
    this.audioElement.load();
  }

  /**
   * Plays the current loaded audio.
   */
  async play() {
    if (!this.audioElement) return;
    if (this.audioContext && this.audioContext.state === 'suspended') {
      await this.audioContext.resume();
    }
    await this.audioElement.play();
    this.isPlaying = true;
  }

  /**
   * Pauses the audio.
   */
  pause() {
    if (!this.audioElement) return;
    this.audioElement.pause();
    this.isPlaying = false;
  }

  /**
   * Analyzes current audio frequencies and calculates Bass/Mid/High energy levels + Kick Beat hits.
   * @param {number} currentTime 
   * @returns {{ bass: number, mid: number, high: number, isBeat: boolean }}
   */
  update(currentTime = 0) {
    if (!this.isInitialized || !this.isPlaying || !this.analyser) {
      return { bass: 0, mid: 0, high: 0, isBeat: false };
    }

    this.analyser.getByteFrequencyData(this.frequencyData);

    const binCount = this.frequencyData.length;
    // Bass frequency range (Bins 0 to ~6: ~20Hz - 150Hz)
    let bassSum = 0;
    const bassBins = Math.min(8, binCount);
    for (let i = 0; i < bassBins; i++) {
      bassSum += this.frequencyData[i];
    }
    this.bassEnergy = (bassSum / bassBins) / 255.0;

    // Mid frequency range
    let midSum = 0;
    const midBins = Math.min(32, binCount);
    for (let i = bassBins; i < midBins; i++) {
      midSum += this.frequencyData[i];
    }
    this.midEnergy = (midSum / (midBins - bassBins)) / 255.0;

    // High frequency range
    let highSum = 0;
    for (let i = midBins; i < binCount; i++) {
      highSum += this.frequencyData[i];
    }
    this.highEnergy = (highSum / (binCount - midBins)) / 255.0;

    // Bass Kick Detection (Triggers beat pulse when bass energy spikes above threshold)
    let isBeat = false;
    const minBeatInterval = 0.25; // Limit kick triggers to max 4 beats per sec (~240 BPM max)
    if (this.bassEnergy > this.beatThreshold && (currentTime - this.lastBeatTime) > minBeatInterval) {
      isBeat = true;
      this.lastBeatTime = currentTime;
    }

    return {
      bass: this.bassEnergy,
      mid: this.midEnergy,
      high: this.highEnergy,
      isBeat
    };
  }
}
