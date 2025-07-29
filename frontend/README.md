# Vue Multi-Agent Creator Frontend

A production-ready Vue.js 3 frontend application for creating and managing AI assistants.

## Features

- 🚀 **Vue 3** with Composition API and TypeScript
- 📦 **Vite** for fast development and optimized builds
- 🎨 **Tailwind CSS** for responsive, utility-first styling
- 🔐 **Authentication** with JWT token management
- 🤖 **Assistant Management** - Create, edit, and delete AI assistants
- 💬 **Real-time Chat** with streaming support
- 📁 **File Upload** with drag-and-drop
- 🏪 **Pinia** for state management with persistence
- 🚦 **Vue Router** for navigation with auth guards
- ☁️ **Google Cloud Run** ready deployment

## Tech Stack

- Vue 3.4+
- TypeScript 5.3+
- Vite 5.1+
- Tailwind CSS 3.4+
- Pinia 2.1+
- Vue Router 4.2+
- Axios for API calls
- Headless UI for accessible components
- Heroicons for consistent iconography

## Project Structure

```
frontend/
├── src/
│   ├── assets/         # Static assets and global CSS
│   ├── components/     # Reusable Vue components
│   │   ├── auth/      # Authentication components
│   │   ├── assistant/ # Assistant management components
│   │   ├── chat/      # Chat interface components
│   │   ├── common/    # Common/shared components
│   │   └── upload/    # File upload components
│   ├── composables/   # Vue composition functions
│   ├── layouts/       # Page layouts
│   ├── router/        # Vue Router configuration
│   ├── stores/        # Pinia stores
│   ├── types/         # TypeScript type definitions
│   ├── utils/         # Utility functions
│   └── views/         # Page components
├── public/            # Public static files
└── dist/              # Production build output
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm 9+
- Git

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd VueMultiAgentCreator/frontend
```

2. Install dependencies:
```bash
npm install
```

3. Copy environment variables:
```bash
cp .env.example .env.local
```

4. Update `.env.local` with your configuration:
```env
VITE_API_BASE_URL=http://localhost:8080/api
```

### Development

Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000`

### Building for Production

1. Build the application:
```bash
npm run build
```

2. Preview the production build:
```bash
npm run preview
```

### Type Checking

Run TypeScript type checking:
```bash
npm run type-check
```

### Linting and Formatting

```bash
# Lint code
npm run lint

# Format code
npm run format
```

## Docker Deployment

### Local Docker Build

1. Build the Docker image:
```bash
docker build -t vue-multiagent-frontend .
```

2. Run the container:
```bash
docker run -p 8080:80 vue-multiagent-frontend
```

### Google Cloud Run Deployment

1. Set up Google Cloud CLI and authenticate:
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

2. Build and deploy using Cloud Build:
```bash
gcloud builds submit --config cloudbuild.yaml
```

Or manually:

1. Build and push to Container Registry:
```bash
docker build -t gcr.io/YOUR_PROJECT_ID/vue-multiagent-frontend .
docker push gcr.io/YOUR_PROJECT_ID/vue-multiagent-frontend
```

2. Deploy to Cloud Run:
```bash
gcloud run deploy vue-multiagent-frontend \
  --image gcr.io/YOUR_PROJECT_ID/vue-multiagent-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API URL | `/api` |
| `VITE_APP_NAME` | Application name | `Vue Multi-Agent Creator` |
| `VITE_ENABLE_STREAMING` | Enable chat streaming | `true` |
| `VITE_MAX_FILE_SIZE_MB` | Max file upload size | `10` |

## Key Features Implementation

### Authentication
- JWT token management with automatic refresh
- Protected routes with navigation guards
- Persistent authentication state

### State Management
- Centralized state with Pinia stores
- Automatic persistence for selected data
- Type-safe store definitions

### API Integration
- Axios interceptors for auth headers
- Centralized error handling
- Request/response type safety

### File Upload
- Drag-and-drop support
- Progress tracking
- File type and size validation

### Real-time Chat
- Server-Sent Events for streaming
- Message queuing
- Automatic reconnection

## Development Guidelines

### Component Structure
- Use Composition API with `<script setup>`
- Implement proper TypeScript types
- Follow single responsibility principle

### Styling
- Use Tailwind utility classes
- Create custom components for repeated patterns
- Maintain consistent spacing and colors

### State Management
- Use Pinia stores for global state
- Keep component state local when possible
- Implement proper error handling

### Performance
- Lazy load routes and components
- Implement proper code splitting
- Optimize bundle size with tree shaking

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Android)

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is proprietary and confidential.