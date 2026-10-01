import './style.css';
import { VisualizationEngine } from './index.js';

// Instantiate and start the Emotion-Aware Visualization Engine when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('app');
  if (container) {
    const vizEngine = new VisualizationEngine(container);
    vizEngine.start();

    // Attach to global window object for easy browser console debugging & testing
    window.vizEngine = vizEngine;
  }
});
