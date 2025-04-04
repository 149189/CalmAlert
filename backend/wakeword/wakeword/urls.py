# Model Configuration
MODEL_CONFIG = {
    'WAKEWORD': {
        'PATH': os.path.join(BASE_DIR, 'detection/models/wakeword.onnx'),
        'THRESHOLD': 0.7,  # Confidence threshold
        'SAMPLE_RATE': 16000,
        'CHUNK_SIZE': 24000  # 1.5 seconds of audio
    },
    'PANIC': {
        'PATH': os.path.join(BASE_DIR, 'detection/models/calmalert_model.pt'),
        'THRESHOLD': 0.65,
        'SAMPLE_RATE': 16000,
        'MAX_LENGTH': 2.4  # Seconds
    }
}

# Audio Processing
AUDIO_CONFIG = {
    'MAX_FILE_SIZE': 5242880,  # 5MB
    'ALLOWED_TYPES': ['audio/wav', 'audio/x-wav'],
    'TEMP_DIR': os.path.join(BASE_DIR, 'temp_audio')
}

# WebSocket Configuration
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    }
}

# Emergency Alerts
EMERGENCY_CONFIG = {
    'TWILIO': {
        'ACCOUNT_SID': os.getenv('TWILIO_SID'),
        'AUTH_TOKEN': os.getenv('TWILIO_TOKEN'),
        'FROM_NUMBER': '+1234567890'
    },
    'CONTACTS': [
        '+15551234567',
        'admin@example.com'
    ]
}

# Create temp directory on startup
os.makedirs(AUDIO_CONFIG['TEMP_DIR'], exist_ok=True)