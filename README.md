# Vue Multi-Agent Creator

A modern web application for managing OpenAI assistants with a Vue.js frontend and FastAPI backend.

## Features

- 🔐 User authentication with JWT tokens
- 🤖 Create and manage multiple OpenAI assistants
- 💬 Real-time chat with streaming responses
- 📁 File upload and management
- 🔄 WebSocket support for live updates
- 📱 Responsive design for mobile and desktop
- ☁️ Google Cloud Run ready

## Architecture

- **Frontend**: Vue 3 + TypeScript + Vite + Tailwind CSS
- **Backend**: FastAPI + SQLAlchemy + MySQL
- **Real-time**: WebSocket with Socket.io
- **Deployment**: Docker + Google Cloud Run

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- MySQL 8.0+
- Redis (for WebSocket)
- OpenAI API key

### Development Setup

1. Clone the repository
```bash
git clone <repository-url>
cd VueMultiAgentCreator
```

2. Set up environment variables
```bash
# Backend
cd backend
cp .env.example .env
# Edit .env with your configurations

# Frontend
cd ../frontend
cp .env.example .env.local
# Edit .env.local with your API URL
```

3. Install dependencies
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

4. Start development servers
```bash
# Backend (from backend directory)
python main.py

# Frontend (from frontend directory)
npm run dev
```

### Docker Setup

```bash
# Start all services
docker-compose up

# Build for production
docker-compose build
```

## Deployment

### Google Cloud Run

1. Set up Google Cloud project
```bash
gcloud config set project YOUR_PROJECT_ID
```

2. Create secrets
```bash
gcloud secrets create openai-api-key --data-file=- < openai-key.txt
gcloud secrets create jwt-secret-key --data-file=- < jwt-key.txt
```

3. Deploy using Cloud Build
```bash
gcloud builds submit --config cloudbuild.yaml
```

## API Documentation

Once the backend is running, visit:
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
VueMultiAgentCreator/
├── frontend/                 # Vue.js frontend
│   ├── src/
│   │   ├── components/      # Reusable components
│   │   ├── views/          # Page components
│   │   ├── stores/         # Pinia state management
│   │   ├── composables/    # Vue composables
│   │   └── api/            # API client
│   └── public/             # Static assets
├── backend/                 # FastAPI backend
│   ├── api/                # API endpoints
│   ├── models/             # Database models
│   ├── services/           # Business logic
│   └── utils/              # Utilities
└── deployment/             # Deployment configs
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License