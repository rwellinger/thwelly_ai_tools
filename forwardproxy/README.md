# Forward Proxy - Nginx Reverse Proxy

Production reverse proxy for routing requests to backend services and serving the Angular frontend.

## Overview

Nginx-based reverse proxy that provides:
- **HTTPS Termination**: SSL/TLS encryption for all traffic
- **Request Routing**: Intelligent routing to backend services
- **Rate Limiting**: Protection against excessive requests
- **Static File Serving**: Angular application deployment
- **WebSocket Support**: Real-time communication proxy
- **Security Headers**: HSTS, XSS protection, content security
- **API Documentation**: Swagger UI access

## Architecture

### Routing Configuration

```
┌─────────────────────────────────────────────────────────┐
│                     Nginx (Port 443)                    │
└─────────────────────────────────────────────────────────┘
                           │
      ┌────────────────────┼────────────────────┐
      │                    │                    │
      ▼                    ▼                    ▼
┌──────────┐      ┌─────────────────┐    ┌───────────┐
│  WebUI   │      │   aiproxysrv    │    │  Static   │
│ (Ollama) │      │   (Port 5050)   │    │   Files   │
│  :8080   │      └─────────────────┘    │  /aiwebui │
└──────────┘                             └───────────┘
```

## Project Structure

```
forwardproxy/
├── nginx/
│   └── nginx.conf           # Main configuration file
├── certs/
│   ├── webui.crt           # SSL certificate
│   └── webui.key           # SSL private key
├── html/
│   └── aiwebui/            # Angular production build output
│       └── browser/        # Static files
├── logs/                   # Nginx access and error logs
├── docker-compose.yml      # Docker deployment config
└── README.md              # This file
```

## Configuration Details

### SSL/TLS Settings

**TLS Version**: TLSv1.3 only
**Ciphers**: EECDH+AESGCM:EDH+AESGCM
**HSTS**: Enabled with 1-year max-age

### Rate Limiting

**Default**: 5 requests/second per IP
**Burst**: 10 requests allowed
**Delay**: 2 requests before throttling

**Stricter limits for authentication**:
- User endpoints: 5 burst, 1 delay

### Timeouts

**LLM/AI Generation** (600s):
- `/aiproxysrv/api/v1/image`
- `/aiproxysrv/api/v1/song`
- `/aiproxysrv/api/v1/instrumental`
- `/aiproxysrv/api/v1/ollama/chat`

**Authentication** (30s):
- `/aiproxysrv/api/v1/user`

**Documentation** (60s):
- `/aiproxysrv/api/docs/`
- `/aiproxysrv/api/openapi.json`

## Setup

### Prerequisites

- Docker and Docker Compose installed
- `mkcert` for local SSL certificates (development)
- `openssl` for production certificates

### Generate SSL Certificate

#### Development (Local Network)

```bash
# Install mkcert (macOS)
brew install mkcert
mkcert -install

# Generate certificate for local IPs and hostnames
cd forwardproxy/certs
mkcert macstudio macstudionas 10.0.1.120 localhost

# Rename certificates
mv macstudio+3-key.pem webui.key
mv macstudio+3.pem webui.crt
```

#### Production

```bash
# Using Let's Encrypt (recommended)
certbot certonly --standalone -d yourdomain.com

# Copy certificates
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./certs/webui.crt
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./certs/webui.key

# Or generate self-signed (for testing only)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ./certs/webui.key \
  -out ./certs/webui.crt
```

### Protected Areas (Optional)

Create HTTP Basic Auth for sensitive endpoints:

```bash
# Install htpasswd
sudo apt-get install apache2-utils  # Ubuntu/Debian
brew install httpd                   # macOS

# Create password file
htpasswd -c ./nginx/.htpasswd username

# Add to nginx.conf location block
location /protected/ {
  auth_basic "Restricted Area";
  auth_basic_user_file /etc/nginx/.htpasswd;
  ...
}
```

### Deploy Angular Frontend

```bash
# Build Angular production bundle
cd ../aiwebui
npm run build:prod

# Output automatically goes to forwardproxy/html/aiwebui/
# Verify files exist
ls -la ../forwardproxy/html/aiwebui/browser/
```

## Deployment

### Start Service

```bash
cd forwardproxy

# Start nginx container
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### Stop Service

```bash
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Restart Service

```bash
docker-compose restart

# Or reload configuration without downtime
docker exec forward-proxy nginx -s reload
```

## Route Configuration

### Frontend Routes

**Main Application**
```
GET  /aiwebui/          → Angular app (index.html)
GET  /aiwebui/assets/*  → Static assets (CSS, JS, images)
GET  /assets/*          → Absolute path assets
```

**Fallback**: All unmatched `/aiwebui/*` routes redirect to `index.html` for Angular routing.

### Backend API Routes

**Image Generation**
```
POST /aiproxysrv/api/v1/image/generate      → aiproxysrv:5050
GET  /aiproxysrv/api/v1/image/list          → aiproxysrv:5050
GET  /aiproxysrv/api/v1/image/:id           → aiproxysrv:5050
PUT  /aiproxysrv/api/v1/image/:id           → aiproxysrv:5050
DELETE /aiproxysrv/api/v1/image/:id         → aiproxysrv:5050
```

**Song Generation**
```
POST /aiproxysrv/api/v1/song/generate       → aiproxysrv:5050
GET  /aiproxysrv/api/v1/song/list           → aiproxysrv:5050
POST /aiproxysrv/api/v1/song/:id/stem       → aiproxysrv:5050
```

**Instrumental Generation**
```
POST /aiproxysrv/api/v1/instrumental/generate → aiproxysrv:5050
GET  /aiproxysrv/api/v1/instrumental/:id      → aiproxysrv:5050
```

**Chat API**
```
POST /aiproxysrv/api/v1/ollama/chat        → aiproxysrv:5050
```

**Prompt Management**
```
GET  /aiproxysrv/api/v1/prompts            → aiproxysrv:5050
POST /aiproxysrv/api/v1/prompts            → aiproxysrv:5050
```

**User Management**
```
POST /aiproxysrv/api/v1/user/register      → aiproxysrv:5050
POST /aiproxysrv/api/v1/user/login         → aiproxysrv:5050
GET  /aiproxysrv/api/v1/user/profile       → aiproxysrv:5050
```

**API Documentation**
```
GET /aiproxysrv/api/docs/                  → Swagger UI
GET /aiproxysrv/api/openapi.json           → OpenAPI spec (JSON)
GET /aiproxysrv/api/openapi.yaml           → OpenAPI spec (YAML)
```

### WebUI Routes (Ollama)

**Open WebUI**
```
GET  /                   → webui:8080
GET  /ws/socket.io/      → WebSocket proxy to webui:8080
```

### Health & Status

```
GET /nginx_status        → Nginx stub status (localhost only)
```

## Security Features

### Headers

**HSTS (HTTP Strict Transport Security)**
```nginx
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

**Additional Security Headers** (User endpoints)
```nginx
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
```

### Rate Limiting

**Zone Configuration**
```nginx
limit_req_zone $binary_remote_addr zone=one:10m rate=5r/s;
```

**Per-Endpoint Limits**
```nginx
# Standard endpoints
limit_req zone=one burst=10 delay=2;

# Authentication endpoints
limit_req zone=one burst=5 delay=1;
```

### SSL Configuration

```nginx
ssl_protocols       TLSv1.3;
ssl_ciphers         EECDH+AESGCM:EDH+AESGCM;
```

## Monitoring

### Access Logs

```bash
# View access logs
docker exec forward-proxy tail -f /var/log/nginx/access.log

# Or from host (if volume mounted)
tail -f logs/access.log
```

### Error Logs

```bash
# View error logs
docker exec forward-proxy tail -f /var/log/nginx/error.log

# Or from host
tail -f logs/error.log
```

### Health Check

```bash
# Container health status
docker ps --filter name=forward-proxy

# Nginx status (from within container)
docker exec forward-proxy curl http://localhost/nginx_status

# HTTPS connectivity
curl -k https://localhost/aiwebui/
```

## Troubleshooting

### Certificate Issues

**Error**: `SSL certificate problem`

```bash
# Check certificate validity
openssl x509 -in certs/webui.crt -text -noout

# Verify certificate and key match
openssl x509 -noout -modulus -in certs/webui.crt | openssl md5
openssl rsa -noout -modulus -in certs/webui.key | openssl md5
# Both should output the same hash

# Regenerate certificates
cd certs
mkcert macstudio 10.0.1.120 localhost
mv macstudio+1-key.pem webui.key
mv macstudio+1.pem webui.crt
```

### Port Conflicts

**Error**: `bind() to 0.0.0.0:443 failed`

```bash
# Find process using port 443
sudo lsof -i :443

# Kill conflicting process
sudo kill -9 [PID]

# Or change port in docker-compose.yml
ports:
  - "8443:443"  # Use port 8443 instead
```

### Configuration Errors

**Error**: `nginx: [emerg] invalid parameter`

```bash
# Test configuration
docker exec forward-proxy nginx -t

# View detailed error
docker-compose logs nginx

# Validate nginx.conf syntax
nginx -t -c nginx/nginx.conf
```

### 502 Bad Gateway

**Cause**: Backend service not running or incorrect proxy_pass URL

```bash
# Check backend service
curl http://10.0.1.120:5050/api/health
curl http://localhost:8080/  # WebUI

# Verify network connectivity
docker exec forward-proxy ping 10.0.1.120

# Check nginx error logs
docker-compose logs nginx | grep "upstream"
```

### Static Files Not Found

**Error**: 404 for `/aiwebui/` or assets

```bash
# Verify files exist
ls -la html/aiwebui/browser/index.html
ls -la html/aiwebui/browser/assets/

# Check file permissions
docker exec forward-proxy ls -la /usr/share/nginx/html/aiwebui/browser/

# Rebuild frontend
cd ../aiwebui
npm run build:prod
```

## Performance Tuning

### Keepalive Settings

```nginx
keepalive_requests 100;
keepalive_timeout 120s;
```

### Buffering (Disabled for Streaming)

```nginx
proxy_buffering         off;
proxy_request_buffering off;
```

### Static File Caching

```nginx
location /assets/ {
  expires 1y;
  add_header Cache-Control "public, immutable";
}
```

## Development vs Production

### Development Setup

- Uses `mkcert` for local SSL certificates
- Backend on `localhost:5050`
- WebUI on `localhost:8080`
- Less restrictive rate limits

### Production Setup

- Uses Let's Encrypt or commercial SSL certificates
- Backend on internal network IP (10.0.1.120:5050)
- WebUI in Docker container
- Stricter rate limits and security headers
- Production domain name configuration

## Nginx Configuration Updates

### Modify Configuration

```bash
# Edit configuration
vi nginx/nginx.conf

# Test configuration
docker exec forward-proxy nginx -t

# Reload without downtime
docker exec forward-proxy nginx -s reload

# Or restart container
docker-compose restart
```

### Add New Backend Route

```nginx
location /aiproxysrv/api/v1/newservice {
  limit_req zone=one burst=10 delay=2;
  proxy_pass          http://10.0.1.120:5050/api/v1/newservice;
  proxy_set_header    Host $host;
  proxy_set_header    X-Real-IP $remote_addr;
  proxy_set_header    X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header    X-Forwarded-Proto https;
  proxy_read_timeout  600s;
}
```

## Best Practices

### DO

✅ Use HTTPS for all production traffic
✅ Regenerate certificates before expiration
✅ Monitor access and error logs regularly
✅ Test configuration changes with `nginx -t`
✅ Use rate limiting to prevent abuse
✅ Enable health checks for monitoring
✅ Keep nginx version updated

### DON'T

❌ Commit SSL private keys to repository
❌ Use self-signed certificates in production
❌ Disable security headers
❌ Ignore error logs
❌ Skip configuration validation
❌ Expose internal service ports directly
❌ Use weak SSL/TLS configurations

## Docker Build & GitHub Actions

### Multi-Platform Docker Images

The project uses GitHub Actions to automatically build and publish multi-platform Docker images (AMD64 and ARM64) to GitHub Container Registry (ghcr.io).

**Workflow**: `.github/workflows/docker-build.yml`

### Published Images

All images are available at `ghcr.io/rwellinger/`:

- `aiwebui-app:latest` - Angular 18 frontend (Nginx-based)
- `aiproxysrv-app:latest` - FastAPI backend server
- `celery-worker-app:latest` - Celery async worker

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
2. **Builds for AMD64 and ARM64** architectures
3. **Tags images** with version and `latest`
4. **Pushes to GitHub Container Registry**

### Using Pre-Built Images

**Pull images:**
```bash
docker pull ghcr.io/rwellinger/aiwebui-app:latest
docker pull ghcr.io/rwellinger/aiproxysrv-app:latest
docker pull ghcr.io/rwellinger/celery-worker-app:latest
```

**Use in docker-compose:**
```yaml
services:
  aiwebui:
    image: ghcr.io/rwellinger/aiwebui-app:latest
    # or specific version
    # image: ghcr.io/rwellinger/aiwebui-app:v1.0.0
```

### Local Multi-Platform Build

**Build aiwebui locally:**
```bash
cd aiwebui

# AMD64 + ARM64 build
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --target production \
  -t aiwebui-app:local \
  .

# Single platform (faster for testing)
docker build \
  --target production \
  -t aiwebui-app:local \
  .
```

### Image Registry Authentication

For private repositories, authenticate before pulling:
```bash
# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Pull image
docker pull ghcr.io/rwellinger/aiwebui-app:latest
```

### Image Tags

- `latest` - Most recent build from main branch
- `v1.0.0` - Specific version tag
- Platform-specific manifests automatically selected based on host architecture

### Build Targets

The `aiwebui` Dockerfile has multiple stages:

**Development:**
```dockerfile
FROM node:18-alpine AS development
# Development dependencies and dev server
```

**Build:**
```dockerfile
FROM node:18-alpine AS build
# Production build artifacts
```

**Production:**
```dockerfile
FROM nginx:alpine AS production
# Optimized Nginx image with built artifacts
```

**Usage:**
```bash
# Development image
docker build --target development -t aiwebui:dev .

# Production image (default)
docker build --target production -t aiwebui:prod .
```

## Related Documentation

- **Backend API**: `../aiproxysrv/openai_impl.md`
- **Frontend**: `../aiwebui/README.md`
- **Nginx Documentation**: https://nginx.org/en/docs/
- **GitHub Container Registry**: https://github.com/rwellinger/mac_ki_service/pkgs/container

## Quick Reference

### Common Commands

```bash
# Start proxy
docker-compose up -d

# Stop proxy
docker-compose down

# View logs
docker-compose logs -f

# Reload configuration
docker exec forward-proxy nginx -s reload

# Test configuration
docker exec forward-proxy nginx -t

# Check status
docker-compose ps

# Access logs
docker exec forward-proxy tail -f /var/log/nginx/access.log
```
