# thWelly's AI Toolbox

<img src="python_ai_services.png" alt="Python AI Services" width="204" height="204">

A full-stack platform for AI-powered image and music generation with Python backend (FastAPI) and Angular 18 frontend.

## 🎯 Features

- **Image Generation** via DALL·E 3 (OpenAI)
- **Song Generation** via Mureka API (asynchronous with Celery)
- **Chat Integration** via Ollama (llama3.2:3b & gpt-oss:20b)
- **PostgreSQL** database for persistent storage
- **Angular 18** frontend with Material Design
- **Redis & Celery** for asynchronous task processing

---

## 📋 System Requirements

### Hardware
- **Development**: MacBook min. M1, 32GB RAM (Apple Silicon)
- **Production**: min. Mac Studio M1 Max, 32GB RAM (Apple Silicon)

### Software
- **macOS** (Apple Silicon)
- **Python 3.x** (with Miniconda3)
- **Node.js & npm** (for Angular)
- **Docker** (via Colima for macOS)
- **Git**

---

## 🚀 Installation

### Quick Start with Pre-built Docker Images

**Recommended for users who just want to run the services:**

```bash
# Pull pre-built images from GitHub Container Registry
# Supports both AMD64 (Intel/AMD) and ARM64 (Apple Silicon)
docker pull ghcr.io/rwellinger/aiproxysrv-app:latest
docker pull ghcr.io/rwellinger/celery-worker-app:latest

# Or use a specific version
docker pull ghcr.io/rwellinger/aiproxysrv-app:v2.0.0
docker pull ghcr.io/rwellinger/celery-worker-app:v2.0.0

# Configure environment and start
cd aiproxysrv
cp env_template .env
# Edit .env with your API keys
docker compose pull
docker compose up -d
```

---

### Full Installation from Source

### 1. Clone Repository

```bash
git clone <repository-url>
cd mac_ki_service
```

### 2. Install Docker/Colima

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Colima
brew install colima docker

# Start Colima (optimized for Apple Silicon)
colima start --arch aarch64 --cpu 4 --memory 4 --disk 80 --vm-type=vz
```

### 3. Create Docker Network

```bash
docker network create webui-network
```

### 4. Python Environment (Conda)

```bash
# Install Miniconda3 (if not already installed)
# https://docs.conda.io/en/latest/miniconda.html

# Create environment
conda create -n mac_ki_service python=3.11
conda activate mac_ki_service
```

### 5. Backend Setup (aiproxysrv)

```bash
cd aiproxysrv

# Install Python dependencies
pip install -e .

# Create .env file
cp env_template .env
```

**Important: Configure `.env` file:**

```bash
# Generate JWT secret
openssl rand -base64 32

# Edit .env and set the following values:
# - JWT_SECRET_KEY=<generated-key>
# - OPENAI_API_KEY=<your-openai-key>
# - MUREKA_API_KEY=<your-mureka-key>
# - POSTGRES_PASSWORD=<secure-password>
# - DATABASE_URL=postgresql://aiproxy:<password>@localhost:5432/aiproxysrv
```

**Create PostgreSQL .env:**

```bash
# Create .env_postgres
cat > .env_postgres << EOF
POSTGRES_USER=aiproxy
POSTGRES_PASSWORD=<same-as-above>
POSTGRES_DB=aiproxysrv
EOF
```

### 6. Frontend Setup (aiwebui)

```bash
cd ../aiwebui

# Install dependencies
npm install
```

### 7. Start Database & Services

#### Option A: Development (PostgreSQL + Redis in Docker)

```bash
# In develop-env/
cd develop-env
docker compose up -d

# Database migrations
cd ../aiproxysrv
alembic upgrade head
```

#### Option B: Production (Full Stack in Docker)

```bash
cd aiproxysrv
docker compose up -d
```

---

## 🔧 Development Workflow

### Start Backend (Development)

```bash
# Terminal 1: Activate Conda environment
conda activate mac_ki_service
cd aiproxysrv

# Development server
python src/server.py
# Running on http://localhost:5050

# Terminal 2: Celery Worker (for song generation)
python src/worker.py
```

### Start Frontend (Development)

```bash
cd aiwebui

# Development server
npm run dev
# Running on http://localhost:4200
```

### Production Build

```bash
# Build frontend
cd aiwebui
npm run build:prod

# Output in: forwardproxy/html/aiwebui/
```

---

## 🗂️ Project Structure

```
mac_ki_service/
├── aiproxysrv/          # Python Backend (FastAPI)
│   ├── src/
│   │   ├── api/         # API routes & business logic
│   │   ├── db/          # Database models & migrations
│   │   ├── celery_app/  # Async worker (Mureka)
│   │   ├── schemas/     # Pydantic models
│   │   ├── server.py    # Dev server
│   │   └── worker.py    # Celery worker
│   ├── docker-compose.yml
│   ├── env_template
│   └── pyproject.toml
│
├── aiwebui/             # Angular 18 Frontend
│   ├── src/app/
│   │   ├── pages/       # Feature pages
│   │   ├── services/    # API services
│   │   ├── components/  # Shared components
│   │   └── models/      # TypeScript interfaces
│   └── package.json
│
├── forwardproxy/        # Nginx reverse proxy (Production)
│   ├── html/           # Angular build output
│   └── nginx/          # Nginx config
│
├── aitestmock/          # Mock API (Testing)
└── develop-env/         # Development Docker setup
    └── docker-compose.yml
```

---

## 🛠️ Important Commands

### Backend

```bash
# Development server
python src/server.py

# Celery worker
python src/worker.py

# Database migrations
cd src && alembic upgrade head
cd src && alembic revision --autogenerate -m "description"

# Docker (Production)
cd aiproxysrv
docker compose up -d
docker compose logs -f
```

### Frontend

```bash
# Development
npm run dev

# Production build
npm run build:prod

# Linting
npm run lint
npm run lint:fix

# Tests
npm run test
```

---

## 🔐 API Keys & Security

### Required API Keys

1. **OpenAI (DALL·E 3)**
   - https://platform.openai.com/api-keys
   - Cost: ~$0.040-0.080 per image

2. **Mureka (Song Generation)**
   - https://mureka.ai/
   - Cost: Credit-based

3. **JWT Secret**
   ```bash
   openssl rand -base64 32
   ```

> ⚠️ **Important!**
> - Never commit `.env` files to the repository
> - Keep API keys secure
> - In production: Use strong passwords
> - Rotate JWT_SECRET_KEY regularly

---

## 🧪 Testing

### Mock API (aitestmock)

For testing without API costs:

```bash
cd aitestmock
python mock_server.py
# Running on http://localhost:3080
```

**Test scenarios:**
- Image: `prompt="0001"` → Success
- Image: `prompt="0002"` → Error (invalid token)
- Song: `prompt="0001"` → Success
- Song: `prompt="0002"` → Error (invalid token)
- Song: `prompt="30s"` → 30s duration test

---

## 🐛 Troubleshooting

### Docker Issues

```bash
# Check ports
lsof -i :5050  # Backend
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# Docker cleanup
docker system prune -f
docker volume prune -f
```

### Database Connection

```bash
# PostgreSQL status
docker compose ps postgres
docker compose logs postgres

# Connect manually
docker exec -it postgres psql -U aiproxy -d aiproxysrv

# Migration status
alembic current
alembic history
```

### Celery Worker

```bash
# Worker status
celery -A worker inspect active

# Restart worker
pkill -f "celery worker"
python src/worker.py
```

---

## 📚 Architecture

### Backend (aiproxysrv)
- **Framework**: FastAPI (Flask compatibility)
- **Database**: PostgreSQL + SQLAlchemy ORM
- **Async Tasks**: Celery + Redis
- **Migrations**: Alembic

### Frontend (aiwebui)
- **Framework**: Angular 18
- **UI**: Angular Material
- **Styling**: SCSS
- **State**: RxJS

### Production
- **Reverse Proxy**: Nginx
- **Container**: Docker + Colima
- **Orchestration**: Docker Compose

---

## 🤝 Contributing

For questions or issues:
1. Create an issue
2. Create a branch: `feature/xyz` or `fix/xyz`
3. Pull request against `main`

---

## 📄 License

Private project - All rights reserved

---

## ⚙️ Environment Variables

Complete list in `aiproxysrv/env_template`:

| Variable | Description | Example |
|----------|-------------|---------|
| `JWT_SECRET_KEY` | JWT Token Secret | `openssl rand -base64 32` |
| `OPENAI_API_KEY` | OpenAI API Key | `sk-...` |
| `MUREKA_API_KEY` | Mureka API Key | `mk_...` |
| `DATABASE_URL` | PostgreSQL Connection | `postgresql://user:pass@localhost:5432/db` |
| `REDIS_URL` | Redis Connection | `redis://localhost:6379` |
| `DEBUG` | Debug Mode | `true` / `false` |

---

## 📞 Support

- **Docs**: See `./docs/README.md` for detailed developer documentation
- **Issues**: GitHub Issues
- **Email**: rob.wellinger@gmail.com

