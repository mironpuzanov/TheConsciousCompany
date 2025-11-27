import FFT from 'fft.js';

// EEG frequency bands (in Hz)
export const BANDS = {
  delta: { min: 0.5, max: 4, name: 'Delta', color: '#8b5cf6' },    // Deep sleep
  theta: { min: 4, max: 8, name: 'Theta', color: '#3b82f6' },      // Meditation, creativity
  alpha: { min: 8, max: 13, name: 'Alpha', color: '#10b981' },     // Relaxed, calm
  beta: { min: 13, max: 30, name: 'Beta', color: '#f59e0b' },      // Active thinking
  gamma: { min: 30, max: 50, name: 'Gamma', color: '#ef4444' },    // Peak focus
} as const;

export interface BandPowers {
  delta: number;
  theta: number;
  alpha: number;
  beta: number;
  gamma: number;
}

/**
 * Calculate power in specific frequency band using FFT
 * @param samples - Array of EEG samples (should be 256 for 1 second at 256 Hz)
 * @param sampleRate - Sampling rate in Hz (256 for Muse)
 * @returns Band powers as percentages (0-100)
 */
export function calculateBandPowers(samples: number[], sampleRate: number = 256): BandPowers {
  if (samples.length < 256) {
    // Not enough data yet
    return { delta: 0, theta: 0, alpha: 0, beta: 0, gamma: 0 };
  }

  // Use last 256 samples (1 second of data)
  const window = samples.slice(-256);

  // Apply Hanning window to reduce spectral leakage
  const windowed = applyHanningWindow(window);

  // Perform FFT
  const fftSize = 256;
  const fft = new FFT(fftSize);
  const out = fft.createComplexArray();
  fft.realTransform(out, windowed);

  // Calculate power spectrum
  const powerSpectrum: number[] = [];
  for (let i = 0; i < fftSize / 2; i++) {
    const real = out[2 * i];
    const imag = out[2 * i + 1];
    powerSpectrum[i] = Math.sqrt(real * real + imag * imag);
  }

  // Calculate frequency resolution
  const freqResolution = sampleRate / fftSize;

  // Calculate power in each band
  const bandPowers: BandPowers = {
    delta: getBandPower(powerSpectrum, BANDS.delta.min, BANDS.delta.max, freqResolution),
    theta: getBandPower(powerSpectrum, BANDS.theta.min, BANDS.theta.max, freqResolution),
    alpha: getBandPower(powerSpectrum, BANDS.alpha.min, BANDS.alpha.max, freqResolution),
    beta: getBandPower(powerSpectrum, BANDS.beta.min, BANDS.beta.max, freqResolution),
    gamma: getBandPower(powerSpectrum, BANDS.gamma.min, BANDS.gamma.max, freqResolution),
  };

  // Normalize to percentages
  const total = Object.values(bandPowers).reduce((sum, val) => sum + val, 0);
  if (total > 0) {
    return {
      delta: (bandPowers.delta / total) * 100,
      theta: (bandPowers.theta / total) * 100,
      alpha: (bandPowers.alpha / total) * 100,
      beta: (bandPowers.beta / total) * 100,
      gamma: (bandPowers.gamma / total) * 100,
    };
  }

  return { delta: 0, theta: 0, alpha: 0, beta: 0, gamma: 0 };
}

/**
 * Apply Hanning window to reduce spectral leakage
 */
function applyHanningWindow(samples: number[]): number[] {
  const n = samples.length;
  return samples.map((sample, i) => {
    const multiplier = 0.5 * (1 - Math.cos((2 * Math.PI * i) / (n - 1)));
    return sample * multiplier;
  });
}

/**
 * Get total power in a specific frequency band
 */
function getBandPower(
  powerSpectrum: number[],
  minFreq: number,
  maxFreq: number,
  freqResolution: number
): number {
  const minBin = Math.floor(minFreq / freqResolution);
  const maxBin = Math.ceil(maxFreq / freqResolution);

  let power = 0;
  for (let i = minBin; i <= maxBin && i < powerSpectrum.length; i++) {
    power += powerSpectrum[i] * powerSpectrum[i]; // Square for power
  }

  return power;
}

/**
 * Simple moving average filter for noise reduction
 */
export function movingAverage(data: number[], windowSize: number = 5): number[] {
  const result: number[] = [];
  for (let i = 0; i < data.length; i++) {
    const start = Math.max(0, i - Math.floor(windowSize / 2));
    const end = Math.min(data.length, i + Math.ceil(windowSize / 2));
    const slice = data.slice(start, end);
    const avg = slice.reduce((sum, val) => sum + val, 0) / slice.length;
    result.push(avg);
  }
  return result;
}
