# CalmAlert - Wakeword Detection System

## Overview
CalmAlert is a wakeword detection system that utilizes Django for the backend and a React-based frontend. The system processes audio inputs to detect specific wakewords and classify emotions based on audio recordings.

## Table of Contents
- [Backend Setup](#backend-setup)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Configuration](#environment-configuration)
  - [Running the Server](#running-the-server)
- [Frontend Setup](#frontend-setup)
  - [Prerequisites](#prerequisites-1)
  - [Installation](#installation-1)
  - [Running the Frontend](#running-the-frontend)
- [API Endpoints](#api-endpoints)
- [Troubleshooting](#troubleshooting)

---

## Backend Setup

### Prerequisites
Ensure you have the following installed:
- Python 3.9+
- pip (Python package manager)
- virtualenv (recommended for dependency management)
- Redis (for WebSocket channels)
- PostgreSQL/MySQL (if not using SQLite in production)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/CalmAlert.git
   cd CalmAlert/backend/wakeword
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   .venv\Scripts\activate  # On Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Environment Configuration
Create a `.env` file in the `backend/wakeword/` directory:
   ```ini
   DJANGO_SECRET_KEY=your_secret_key
   DJANGO_DEBUG=True
   DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
   TWILIO_SID=your_twilio_sid
   TWILIO_TOKEN=your_twilio_auth_token
   REDIS_URL=redis://127.0.0.1:6379
   ```

### Running the Server
1. Apply database migrations:
   ```bash
   python manage.py migrate
   ```

2. Create a superuser (optional, for Django admin panel):
   ```bash
   python manage.py createsuperuser
   ```

3. Run the server:
   ```bash
   python manage.py runserver
   ```
   The backend will be accessible at `http://127.0.0.1:8000/`

---

## Frontend Setup

### Prerequisites
Ensure you have the following installed:
- Node.js (16+ recommended)
- npm or yarn

### Installation
1. Navigate to the frontend directory:
   ```bash
   cd CalmAlert/frontend
   ```

2. Install dependencies:
   ```bash
   npm install  # or yarn install
   ```

### Running the Frontend
1. Start the development server:
   ```bash
   npm start  # or yarn start
   ```
   The frontend will be accessible at `http://localhost:3000/`

---

## API Endpoints
- `POST /api/detect/` - Upload an audio file for wakeword detection
- `GET /api/status/` - Check system status
- `POST /api/emotion/` - Classify emotion from an audio file

---

## Troubleshooting
### ModuleNotFoundError: No module named 'rest_framework'
Run:
```bash
pip install djangorestframework
```

### ModuleNotFoundError: No module named 'corsheaders'
Run:
```bash
pip install django-cors-headers
```
Add `'corsheaders'` to `INSTALLED_APPS` and `'corsheaders.middleware.CorsMiddleware'` to `MIDDLEWARE`.

### Redis Connection Issue
Ensure Redis is running:
```bash
redis-server
```

---

## Contributing
Feel free to fork and submit pull requests!

## License
MIT License

