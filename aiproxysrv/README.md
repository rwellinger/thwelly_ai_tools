# User Management Setup

## Initial User Creation

To create the initial admin user, use environment variables for security:

```bash
# Set environment variables
export INITIAL_USER_EMAIL="admin@yourdomain.com"
export INITIAL_USER_PASSWORD="your_secure_password"
export INITIAL_USER_FIRST_NAME="Your"
export INITIAL_USER_LAST_NAME="Name"

# Run the script
python scripts/create_initial_user.py
```

## Alternative: API Endpoint User Creation

For initial setup or development environments, you can also create users directly via the REST API.

### Prerequisites

- aiproxysrv server must be running (`python server.py` or via Docker)
- API accessible at `http://localhost:8000` (development) or your production URL

### Method 1: Using Swagger UI (Recommended for Development)

1. **Open Swagger UI:**
   - Development: `http://localhost:8000/docs`
   - Production: `https://your-domain/docs`

2. **Navigate to User Management:**
   - Find the `/api/v1/user/create` endpoint in the "User Authentication and Management" section
   - Click "Try it out"

3. **Fill in User Details:**
   ```json
   {
     "email": "admin@yourdomain.com",
     "password": "your_secure_password",
     "first_name": "Admin",
     "last_name": "User"
   }
   ```

4. **Execute Request:**
   - Click "Execute"
   - Check response for success confirmation

### Method 2: Using cURL

```bash
curl -X POST "http://localhost:8000/api/v1/user/create" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@yourdomain.com",
    "password": "your_secure_password",
    "first_name": "Admin",
    "last_name": "User"
  }'
```

### Method 3: Using HTTP Client (Postman, Insomnia, etc.)

**URL:** `POST http://localhost:8000/api/v1/user/create`

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "email": "admin@yourdomain.com",
  "password": "your_secure_password",
  "first_name": "Admin",
  "last_name": "User"
}
```

### Expected Response

**Success (201):**
```json
{
  "success": true,
  "message": "User created successfully",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "admin@yourdomain.com"
}
```

**Error (400/409/500):**
```json
{
  "success": false,
  "error": "Email already exists"
}
```

### Important Notes

- ⚠️ **Development Only**: API user creation without authentication is intended for initial setup
- ⚠️ **Production Security**: In production with token authentication, only admin users can create new users
- 🔒 **Password Requirements**: Minimum 4 characters (consider longer passwords for security)
- 📧 **Email Validation**: Valid email format required
- 🚫 **Duplicate Prevention**: Email addresses must be unique

### Additional User Management Endpoints

Once you have created users, these endpoints are also available:

- `POST /api/v1/user/login` - User authentication
- `GET /api/v1/user/list` - List all users (admin only)
- `GET /api/v1/user/profile/{user_id}` - Get user profile
- `PUT /api/v1/user/edit/{user_id}` - Update user information
- `PUT /api/v1/user/password/{user_id}` - Change password
- `POST /api/v1/user/password-reset` - Admin password reset

### Security Notes

- **Never** hardcode credentials in source code
- Use strong passwords (minimum 8 characters, mixed case, numbers, symbols)
- Change default credentials immediately after first login
- Use environment variables or secure configuration management

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `INITIAL_USER_EMAIL` | Yes | - | Admin user email address |
| `INITIAL_USER_PASSWORD` | Yes | - | Admin user password |
| `INITIAL_USER_FIRST_NAME` | No | "Admin" | User's first name |
| `INITIAL_USER_LAST_NAME` | No | "User" | User's last name |

### Example

```bash
# Create admin user
INITIAL_USER_EMAIL="admin@mycompany.com" \
INITIAL_USER_PASSWORD="MySecurePassword123!" \
INITIAL_USER_FIRST_NAME="System" \
INITIAL_USER_LAST_NAME="Administrator" \
python scripts/create_initial_user.py
```

## Docker Build & GitHub Actions

### Multi-Platform Docker Images

The project uses GitHub Actions to automatically build and publish multi-platform Docker images (AMD64 and ARM64) to GitHub Container Registry (ghcr.io).

**Workflow**: `.github/workflows/docker-build.yml`

### Published Images

All images are available at `ghcr.io/rwellinger/`:

- `aiproxysrv-app:latest` - FastAPI backend server
- `celery-worker-app:latest` - Celery async worker for song generation
- `aiwebui-app:latest` - Angular 18 frontend

### Triggering Builds

**Automatic on version tag:**
```bash
git tag v1.0.0
git push origin v1.0.0
```

**Manual trigger:**
- Go to GitHub Actions → "Build and Push Multi-Platform Docker Images" → Run workflow

### Build Process

The GitHub Actions workflow:
1. **Sets up multi-platform support** (QEMU + Docker Buildx)
2. **Builds separate jobs** for app and worker images
3. **Builds for AMD64 and ARM64** architectures
4. **Tags images** with version and `latest`
5. **Pushes to GitHub Container Registry**

### Docker Multi-Stage Build

The `aiproxysrv/dockerfile` uses multi-stage builds to create optimized images:

**Base Stage:**
```dockerfile
FROM python:3.11-slim AS base
# System dependencies and Python packages
```

**App Target:**
```dockerfile
FROM base AS app
# FastAPI server (Gunicorn + Uvicorn)
CMD ["gunicorn", "src.wsgi:app", ...]
```

**Worker Target:**
```dockerfile
FROM base AS worker
# Celery worker for async tasks
CMD ["celery", "-A", "src.worker", "worker", ...]
```

### Using Pre-Built Images

**Pull images:**
```bash
docker pull ghcr.io/rwellinger/aiproxysrv-app:latest
docker pull ghcr.io/rwellinger/celery-worker-app:latest
```

**Use in docker-compose:**
```yaml
services:
  aiproxysrv:
    image: ghcr.io/rwellinger/aiproxysrv-app:latest
    # or specific version
    # image: ghcr.io/rwellinger/aiproxysrv-app:v1.0.0
    ports:
      - "5050:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres/db
      - REDIS_URL=redis://redis:6379/0

  celery-worker:
    image: ghcr.io/rwellinger/celery-worker-app:latest
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres/db
      - REDIS_URL=redis://redis:6379/0
      - MUREKA_API_KEY=${MUREKA_API_KEY}
```

### Local Multi-Platform Build

**Build both targets locally:**
```bash
cd aiproxysrv

# Build app image (AMD64 + ARM64)
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --target app \
  -t aiproxysrv-app:local \
  .

# Build worker image (AMD64 + ARM64)
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --target worker \
  -t celery-worker-app:local \
  .

# Single platform (faster for testing)
docker build --target app -t aiproxysrv-app:test .
docker build --target worker -t celery-worker-app:test .
```

### Image Registry Authentication

For private repositories, authenticate before pulling:
```bash
# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Pull images
docker pull ghcr.io/rwellinger/aiproxysrv-app:latest
docker pull ghcr.io/rwellinger/celery-worker-app:latest
```

### Image Tags

- `latest` - Most recent build from main branch
- `v1.0.0` - Specific version tag (semantic versioning)
- Platform-specific manifests automatically selected based on host architecture

### Architecture Support

Both images support:
- **linux/amd64** - Intel/AMD x86_64 processors
- **linux/arm64** - ARM-based processors (Apple Silicon M1/M2/M4, AWS Graviton, etc.)

Docker automatically pulls the correct image variant for your platform.

### Development vs Production

**Development:**
```bash
# Run directly with Python
python src/server.py          # Backend server
python src/worker.py           # Celery worker
```

**Production:**
```bash
# Run with Docker images
docker run -d ghcr.io/rwellinger/aiproxysrv-app:latest
docker run -d ghcr.io/rwellinger/celery-worker-app:latest

# Or use docker-compose
docker-compose up -d
```

### Dockerfile Location

**Backend & Worker**: `aiproxysrv/dockerfile`
- Single Dockerfile with multiple build targets
- Target `app` → FastAPI server
- Target `worker` → Celery worker

### Environment Variables

Both images require:
```bash
# Database connection
DATABASE_URL=postgresql://user:password@host:5432/database

# Redis (for Celery task queue)
REDIS_URL=redis://host:6379/0

# API Keys (worker only needs Mureka)
MUREKA_API_KEY=your_mureka_key
OPENAI_API_KEY=your_openai_key  # app only
```

### Health Checks

**App health check:**
```bash
curl http://localhost:8000/api/health
```

**Worker monitoring:**
```bash
# Inside container
celery -A src.worker inspect active
celery -A src.worker inspect stats

# Or use Flower
docker run -d -p 5555:5555 \
  ghcr.io/rwellinger/celery-worker-app:latest \
  celery -A src.worker flower
```

### Build Verification

After building, verify multi-platform support:
```bash
# Check image manifest
docker buildx imagetools inspect ghcr.io/rwellinger/aiproxysrv-app:latest

# Output shows both architectures:
# Name:      ghcr.io/rwellinger/aiproxysrv-app:latest
# MediaType: application/vnd.docker.distribution.manifest.list.v2+json
# Digest:    sha256:...
# Manifests:
#   linux/amd64
#   linux/arm64
```

### Troubleshooting

**Build fails on ARM64:**
- Ensure QEMU is installed: `docker run --privileged --rm tonistiigi/binfmt --install all`
- Use Docker Buildx: `docker buildx create --use`

**Image pull authentication error:**
- Login first: `echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin`
- Ensure repository visibility is public or you have access

**Wrong architecture pulled:**
- Check platform: `docker image inspect IMAGE_NAME | grep Architecture`
- Force specific platform: `docker pull --platform linux/arm64 IMAGE_NAME`

### Related Documentation

- **GitHub Container Registry**: https://github.com/rwellinger/mac_ki_service/pkgs/container
- **Docker Buildx**: https://docs.docker.com/buildx/working-with-buildx/
- **Multi-Platform Builds**: https://docs.docker.com/build/building/multi-platform/