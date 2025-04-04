import numpy as np
import onnxruntime as ort
import librosa
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class WakeWordDetector:
    def __init__(self, model_path):
        self.session = ort.InferenceSession(
            model_path,
            providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
        )
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        self.sample_rate = 16000  # Must match training config
        self.frame_length = 1.5  # Seconds of audio needed for prediction

    def preprocess_audio(self, audio_data):
        """Convert raw audio bytes to MFCC features."""
        try:
            # Convert bytes to numpy array
            audio = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
            
            # Extract MFCC features (match training parameters)
            mfcc = librosa.feature.mfcc(
                y=audio,
                sr=self.sample_rate,
                n_mfcc=40,
                n_fft=512,
                hop_length=160
            )
            
            # Normalize and reshape for model input
            mfcc = (mfcc - np.mean(mfcc)) / np.std(mfcc)
            return mfcc.T.astype(np.float32)[np.newaxis, ...]  # Add batch dimension
            
        except Exception as e:
            logger.error(f"Audio preprocessing failed: {str(e)}")
            return None

    def detect(self, audio_chunk):
        """Run inference on audio chunk."""
        try:
            features = self.preprocess_audio(audio_chunk)
            if features is None:
                return False
                
            # Pad if insufficient frames
            if features.shape[2] < 96:
                features = np.pad(features, ((0, 0), (0, 0), (0, 96 - features.shape[2])))
                
            outputs = self.session.run(
                [self.output_name],
                {self.input_name: features}
            )
            return outputs[0][0][0] > 0.5  # Threshold can be adjusted
            
        except Exception as e:
            logger.error(f"Inference failed: {str(e)}")
            return False
