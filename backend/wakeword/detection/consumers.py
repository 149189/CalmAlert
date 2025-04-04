# detection/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json
import base64
import asyncio
from concurrent.futures import ThreadPoolExecutor
from .utils import wakeword_onnx, panic_detection

class MonitoringConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wakeword_detector = wakeword_onnx.WakeWordDetector(
            settings.WAKEWORD_MODEL_PATH
        )
        self.panic_detector = panic_detection.PanicDetector(
            settings.PANIC_MODEL_PATH
        )
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    async def _run_in_thread(self, func, *args):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, func, *args)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            audio_bytes = base64.b64decode(data['audio'])
            
            # Parallel detection
            wake_detected = await self._run_in_thread(
                self.wakeword_detector.detect, 
                audio_bytes
            )
            
            panic_result = await self.panic_detector.detect(audio_bytes)
            
            responses = []
            if wake_detected:
                responses.append({
                    'type': 'wakeword',
                    'message': 'Wakeword activated',
                    'timestamp': data['timestamp']
                })
                
            if panic_result['panic']:
                responses.append({
                    'type': 'panic',
                    'confidence': panic_result['confidence'],
                    'features': panic_result['features'],
                    'timestamp': data['timestamp']
                })
                await self._trigger_emergency()
            
            if responses:
                await self.send(json.dumps(responses))

        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
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