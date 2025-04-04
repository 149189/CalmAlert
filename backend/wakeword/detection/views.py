# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import base64
import json
from .utils import wakeword_onnx, panic_detection

class AudioUploadView(APIView):
    def post(self, request):
        try:
            audio_file = request.FILES['audio']
            audio_bytes = audio_file.read()
            
            # Process with both models
            wake_detected = wakeword_onnx.WakeWordDetector.detect(audio_bytes)
            panic_result = panic_detection.PanicDetector.detect(audio_bytes)
            
            return Response({
                'wakeword': wake_detected,
                'panic': panic_result['panic'],
                'confidence': panic_result['confidence'],
                'processing_time_ms': {
                    'wakeword': wake_detected['processing_time'],
                    'panic': panic_result['processing_time']
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class StreamingEndpoint(APIView):
    def post(self, request):
        try:
            data = json.loads(request.body)
            audio_chunk = base64.b64decode(data['audio'])
            
            # Real-time processing
            wake_detected = wakeword_onnx.WakeWordDetector.detect(audio_chunk)
            panic_result = panic_detection.PanicDetector.detect(audio_chunk)
            
            return Response({
                'wakeword': wake_detected,
                'panic': panic_result['panic'],
                'timestamp': data.get('timestamp')
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)