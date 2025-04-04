import os
import logging
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-)m%q*kivs8=8ud@yi_a3kv142@l20#gl)q&_4gc$-zz7u)cd3l')
if SECRET_KEY.startswith("django-insecure-"):
    logger.warning("Using the default insecure secret key. Set DJANGO_SECRET_KEY for production.")

DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',') if os.getenv('DJANGO_ALLOWED_HOSTS') else []

# Installed Apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'detection', 
    'corsheaders',
]

# Middleware
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # ✅ Required for CORS
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# CORS Settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Adjust for your frontend
]

CORS_ALLOW_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']
CORS_ALLOW_HEADERS = ['authorization', 'content-type', 'accept', 'origin', 'user-agent', 'x-csrftoken', 'x-requested-with']

# URLs & WSGI
ROOT_URLCONF = 'wakeword.urls'
WSGI_APPLICATION = 'wakeword.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Database Warning for Production
if DEBUG and DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
    logger.warning("⚠️ SQLite is not recommended for production. Consider using PostgreSQL or MySQL.")

# Authentication
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Timezone & Language
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static Files
STATIC_URL = 'static/'

# Auto Field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Model Configuration
DETECTION_PATH = os.path.join(BASE_DIR, 'detection')

MODEL_CONFIG = {
    'WAKEWORD': {
        'PATH': os.path.join(BASE_DIR, 'detection/models/wakeword.onnx'),
        'THRESHOLD': 0.7,
        'SAMPLE_RATE': 16000,
        'CHUNK_SIZE': 24000  # 1.5 seconds of audio
    },
    'PANIC': {
        'PATH': os.path.join(BASE_DIR, 'detection/models/calmalert_model.pt'),
        'THRESHOLD': 0.65,
        'SAMPLE_RATE': 16000,
        'MAX_LENGTH': 2.4
    }
}

# Audio Processing
AUDIO_CONFIG = {
    'MAX_FILE_SIZE': 5242880,
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

# Twilio Credentials Check
if not (os.getenv('TWILIO_SID') and os.getenv('TWILIO_TOKEN')) and not DEBUG:
    raise ImproperlyConfigured("Twilio credentials are required in production!")

# Create temp directory with error handling
try:
    os.makedirs(AUDIO_CONFIG['TEMP_DIR'], exist_ok=True)
    logger.info(f"Temporary audio directory ensured at {AUDIO_CONFIG['TEMP_DIR']}")
except Exception as e:
    logger.error(f"Failed to create temporary audio directory: {e}")
    raise
