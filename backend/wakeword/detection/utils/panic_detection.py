# detection/utils/panic_detection.py
import torch
import librosa
import numpy as np
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class PanicDetector:
    def __init__(self, model_path):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self._load_model(model_path)
        self.sample_rate = 16000
        self.model.eval()
        
    def _load_model(self, model_path):
        # Define model architecture (must match training)
        class PanicClassifier(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.lstm = torch.nn.LSTM(40, 128, bidirectional=True)
                self.classifier = torch.nn.Sequential(
                    torch.nn.Linear(256, 64),
                    torch.nn.ReLU(),
                    torch.nn.Linear(64, 2)
                )
            
            def forward(self, x):
                x, _ = self.lstm(x)
                return self.classifier(x[:, -1, :])
        
        model = PanicClassifier()
        model.load_state_dict(torch.load(model_path, map_location=self.device))
        return model.to(self.device)

    def extract_features(self, audio_bytes):
        """Match features used during training"""
        audio = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
        return librosa.feature.mfcc(
            y=audio,
            sr=self.sample_rate,
            n_mfcc=40,
            n_fft=512,
            hop_length=160
        )

    async def detect(self, audio_bytes):
        try:
            with torch.no_grad():
                features = self.extract_features(audio_bytes)
                tensor = torch.Tensor(features.T).unsqueeze(0).to(self.device)
                
                if tensor.shape[1] < 96:  # Pad if needed
                    tensor = torch.nn.functional.pad(tensor, (0,0,0,96-tensor.shape[1]))
                
                outputs = self.model(tensor)
                probs = torch.nn.functional.softmax(outputs, dim=1)
                return {
                    "panic": probs[0][1].item() > 0.65,  # Threshold
                    "confidence": probs[0][1].item(),
                    "features": features.shape
                }
        except Exception as e:
            logger.error(f"Panic detection failed: {str(e)}")
            return {"panic": False, "error": str(e)}