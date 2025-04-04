import json
import base64
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from .utils import wakeword_onnx, panic_detection

class MonitoringConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wakeword_detector = wakeword_onnx.WakeWordDetector(settings.WAKEWORD_MODEL_PATH)
        self.panic_detector = panic_detection.PanicDetector(settings.PANIC_MODEL_PATH)
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.ERROR)

    async def _run_in_thread(self, func, *args):
        """Runs a blocking function in a separate thread to avoid blocking the event loop."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, func, *args)

    async def receive(self, text_data):
        """Handles incoming WebSocket messages, processes audio, and sends response."""
        try:
            data = json.loads(text_data)
            audio_bytes = base64.b64decode(data['audio'])
            
            # Run wakeword detection in a thread
            wake_detected = await self._run_in_thread(self.wakeword_detector.detect, audio_bytes)
            
            # Run panic detection asynchronously
            panic_result = await self._run_in_thread(self.panic_detector.detect, audio_bytes)

            responses = []
            if wake_detected:
                responses.append({
                    'type': 'wakeword',
                    'message': 'Wakeword activated',
                    'timestamp': data.get('timestamp')
                })
                
            if panic_result.get('panic'):
                responses.append({
                    'type': 'panic',
                    'confidence': panic_result['confidence'],
                    'features': panic_result.get('features', {}),
                    'timestamp': data.get('timestamp')
                })
                await self._trigger_emergency()

            # Send all responses as a WebSocket message
            if responses:
                await self.send(json.dumps(responses))

        except Exception as e:
            self.logger.error(f"Processing error: {str(e)}")
            await self.send(json.dumps([{
                'type': 'error',
                'message': 'Processing failed'
            }]))

    async def _trigger_emergency(self):
        """Emergency response pipeline"""
        await self.channel_layer.group_send(
            "emergency_responses",
            {
                "type": "emergency.alert",
                "message": "PANIC_DETECTED",
                "channel": self.channel_name
            }
        )


class EmergencyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Accepts the WebSocket connection."""
        await self.accept()
        await self.send(text_data=json.dumps({"message": "Connected to EmergencyConsumer"}))

    async def disconnect(self, close_code):
        """Handles disconnection."""
        print(f"Disconnected with code {close_code}")

    async def receive(self, text_data):
        """Handles emergency messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get("type")

            if message_type == "emergency_alert":
                response = {
                    "type": "emergency_response",
                    "message": "Emergency alert received!",
                    "status": "acknowledged"
                }
                await self.send(text_data=json.dumps(response))

        except Exception as e:
            print(f"Error processing emergency message: {e}")
            await self.send(text_data=json.dumps({"type": "error", "message": "Invalid data format"}))
