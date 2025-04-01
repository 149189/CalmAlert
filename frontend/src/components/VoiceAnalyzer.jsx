// VoiceAnalyzer.jsx
import { useState, useEffect, useRef } from 'react';
import * as tf from '@tensorflow/tfjs';
import '@tensorflow/tfjs-backend-webgl';

export default function VoiceAnalyzer() {
  const [status, setStatus] = useState('calibration');
  const [baseline, setBaseline] = useState(null);
  const [panicDetected, setPanicDetected] = useState(false);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const modelRef = useRef(null);

  // Load TF.js model on mount
  useEffect(() => {
    async function loadModel() {
      try {
        modelRef.current = await tf.loadLayersModel('/model/model.json');
      } catch (err) {
        console.error('Failed to load model:', err);
      }
    }
    loadModel();
  }, []);

  // Initialize audio context
  const initAudio = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      analyserRef.current = audioContextRef.current.createAnalyser();
      
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);
      
      analyserRef.current.fftSize = 2048;
      return true;
    } catch (err) {
      console.error('Error accessing microphone:', err);
      return false;
    }
  };

  // Clean up audio on component unmount
  useEffect(() => {
    return () => {
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  const average = (arr) =>
    arr.reduce((a, b) => a + b, 0) / (arr.length || 1);

  // Capture baseline during calibration (5 seconds)
  const captureBaseline = async () => {
    const audioInitialized = await initAudio();
    if (!audioInitialized) return;
    
    // Capture baseline for 5 seconds (5000ms)
    const capturedBaseline = await analyzeAudio(5000);
    setBaseline(capturedBaseline);
    setStatus('monitoring');
  };

  // Analyze audio over a given duration and extract features
  const analyzeAudio = (durationMs) => {
    return new Promise((resolve) => {
      const bufferLength = analyserRef.current.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      const features = { pitch: [], speechRate: [] };
      const startTime = Date.now();

      const collectData = () => {
        analyserRef.current.getByteTimeDomainData(dataArray);
        const currentFeatures = extractFeatures(dataArray);
        
        features.pitch.push(currentFeatures.pitch);
        features.speechRate.push(currentFeatures.speechRate);

        if (Date.now() - startTime < durationMs) {
          requestAnimationFrame(collectData);
        } else {
          resolve({
            pitch: average(features.pitch),
            speechRate: average(features.speechRate)
          });
        }
      };

      requestAnimationFrame(collectData);
    });
  };

  // Start monitoring when status changes to 'monitoring'
  useEffect(() => {
    if (status === 'monitoring') {
      startMonitoring();
    }
  }, [status]);

  // Continuously analyze audio and check for panic conditions
  const startMonitoring = () => {
    if (!analyserRef.current) return;

    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    let isAnalyzing = true;

    const analyze = () => {
      if (!isAnalyzing) return;

      analyserRef.current.getByteTimeDomainData(dataArray);
      const features = extractFeatures(dataArray);
      
      if (isPanic(features)) {
        setPanicDetected(true);
        setStatus('alert');
        isAnalyzing = false;
        return;
      }

      requestAnimationFrame(analyze);
    };

    requestAnimationFrame(analyze);

    // Cleanup function in case we need to stop analysis
    return () => {
      isAnalyzing = false;
    };
  };

  // Feature extraction: Normalize data and compute pitch and speech rate
  const extractFeatures = (dataArray) => {
    // Convert 0-255 data to normalized range -1 to 1
    const buffer = new Float32Array(dataArray.length);
    for (let i = 0; i < dataArray.length; i++) {
      buffer[i] = (dataArray[i] - 128) / 128;
    }

    const pitch = detectPitch(buffer);
    const speechRate = calculateSpeechRate(buffer);
    
    return { pitch, speechRate };
  };

  // Pitch detection algorithm using autocorrelation
  const detectPitch = (buffer) => {
    const sampleRate = audioContextRef.current.sampleRate;
    const maxSamples = Math.floor(sampleRate / 30); // 30Hz minimum
    let bestR = 0, bestP = 0;

    for (let p = 20; p < maxSamples; p++) {
      let r = 0;
      for (let i = 0; i < buffer.length - p; i++) {
        r += buffer[i] * buffer[i + p];
      }
      if (r > bestR) {
        bestR = r;
        bestP = p;
      }
    }
    return bestP ? sampleRate / bestP : 0;
  };

  // Speech rate calculation based on threshold crossings
  const calculateSpeechRate = (buffer) => {
    let speechCount = 0;
    const threshold = 0.05;
    
    buffer.forEach((value) => {
      if (Math.abs(value) > threshold) speechCount++;
    });
    
    return (speechCount / buffer.length) * 100;
  };

  // Panic detection logic using rule-based thresholds and a TF.js model prediction
  const isPanic = (currentFeatures) => {
    if (!baseline || !modelRef.current) return false;
    
    // Rule-based thresholds (tweak multipliers as needed)
    const pitchThreshold = baseline.pitch * 1.3;
    const speechRateThreshold = baseline.speechRate * 1.5;
    
    // Prepare input for the ML model
    const input = tf.tensor2d([[currentFeatures.pitch, currentFeatures.speechRate]]);
    const prediction = modelRef.current.predict(input);
    const probability = prediction.dataSync()[0];
    input.dispose();
    prediction.dispose();
    
    return (
      currentFeatures.pitch > pitchThreshold &&
      currentFeatures.speechRate > speechRateThreshold &&
      probability > 0.7
    );
  };

  return (
    <div className="voice-analyzer">
      {status === 'calibration' && (
        <div className="calibration">
          <h2>Voice Calibration</h2>
          <button onClick={captureBaseline}>
            Start 5-Second Calibration
          </button>
        </div>
      )}

      {status === 'monitoring' && (
        <div className="monitoring">
          <h3>Monitoring Voice...</h3>
          <div className="status-indicator"></div>
        </div>
      )}

      {status === 'alert' && (
        <div className="alert">
          <h2>Panic Detected!</h2>
          <div className="breathing-exercise">
            {/* Add breathing animation here */}
          </div>
          <button onClick={() => setStatus('monitoring')}>
            I'm Calm Now
          </button>
        </div>
      )}
    </div>
  );
}
