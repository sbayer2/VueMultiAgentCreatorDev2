# GEMINI.md

## Project Overview

This project is a full-stack web application for creating and managing OpenAI assistants. It features a Vue.js 3 frontend and a Python FastAPI backend. The application provides user authentication, real-time chat with assistants, and file management capabilities. It is designed to be deployed using Docker and Google Cloud Run.

**Frontend:**
- Framework: Vue.js 3 with Vite
- Language: TypeScript
- State Management: Pinia
- Styling: Tailwind CSS
- HTTP Client: Axios

**Backend:**
- Framework: FastAPI
- Language: Python
- ORM: SQLAlchemy
- Database: MySQL
- Real-time: WebSockets

**Deployment:**
- Containerization: Docker
- Orchestration: Docker Compose
- Cloud: Google Cloud Run

## Building and Running

### Development

**Prerequisites:**
- Node.js 18+
- Python 3.11+
- MySQL 8.0+
- OpenAI API key

**1. Set up environment variables:**

*Backend:*
```bash
cd backend
cp .env.example .env
# Edit .env with your configurations
```

*Frontend:*
```bash
cd ../frontend
cp .env.example .env.local
# Edit .env.local with your API URL
```

**2. Install dependencies:**

*Backend:*
```bash
cd backend
pip install -r requirements.txt
```

*Frontend:*
```bash
cd ../frontend
npm install
```

**3. Run the application:**

*Backend (from `backend` directory):*
```bash
python main.py
```

*Frontend (from `frontend` directory):*
```bash
npm run dev
```

### Docker

To run the application using Docker Compose:

```bash
docker-compose up --build
```

## Development Conventions

### Frontend

- **Component-Based Architecture:** The frontend is built with Vue.js components, organized by feature in the `src/components` directory.
- **State Management:** Pinia is used for centralized state management. Stores are defined in `src/stores`.
- **Styling:** Tailwind CSS is used for utility-first styling.
- **Linting and Formatting:** ESLint and Prettier are configured to enforce code style. Use `npm run lint` to check and fix issues.
- **Type Checking:** TypeScript is used for static type checking. Use `npm run type-check` to verify types.

### Backend

- **API Design:** The backend follows RESTful principles, with API endpoints defined in the `api` directory.
- **Database Migrations:** Alembic is used for database migrations, although no migration files are present in the repository.
- **Testing:** Pytest is the designated testing framework, as indicated in the `README.md`.
