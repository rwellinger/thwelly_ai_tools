# Ollama AI Server - Local LLM with Web Interface

Local AI server running Ollama with Open WebUI for chat interactions.

## Overview

This setup provides:
- **Ollama 0.12.0**: Latest stable version with full GPU support
- **Native Mac Installation**: Direct GitHub releases for optimal M1/M4 performance
- **Open WebUI**: Docker-based web interface for chat
- **LaunchDaemon**: Auto-start on system boot
- **GPU Acceleration**: Full Metal GPU support on Apple Silicon

## Architecture

```
┌─────────────────────────────────────┐
│         Mac (Native)                │
│  Ollama 0.12.0 (Port 11434)        │
│  GPU: Apple Silicon Metal           │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│      Docker Container               │
│  Open WebUI (Port 8080)             │
└─────────────────────────────────────┘
```

## Why Native Installation?

**Ollama must run natively on macOS** (not in Docker) because:
- ✅ Direct access to Apple Silicon GPU (Metal)
- ✅ 10-20x faster inference performance
- ✅ Lower memory overhead
- ✅ Better thermal management
- ❌ Docker containers cannot access M1/M4 GPU efficiently

## Installation

### Prerequisites

- macOS with Apple Silicon (M1/M2/M3/M4)
- Docker and Docker Compose (for Open WebUI)
- Internet connection for downloading models

### 1. Install Ollama

**Download latest stable release (v0.12.0)**:

```bash
# Download from GitHub releases
wget https://github.com/ollama/ollama/releases/download/v0.12.0/ollama-darwin.tgz

# Extract archive
tar -xzf ollama-darwin.tgz

# Move to system directory
sudo mv ollama /usr/local/bin/

# Verify installation
ollama --version
# Should output: ollama version is 0.12.0
```

**Alternative: Direct installation**:

```bash
# Download and install in one command
curl -fsSL https://ollama.ai/install.sh | sh
```

### 2. Setup LaunchDaemon (Auto-Start)

Create LaunchDaemon configuration to automatically start Ollama on boot:

```bash
# Copy provided plist file to system directory
sudo cp LaunchDaemon/com.ollama.serve.plist /Library/LaunchDaemons/

# Set correct permissions
sudo chown root:wheel /Library/LaunchDaemons/com.ollama.serve.plist
sudo chmod 644 /Library/LaunchDaemons/com.ollama.serve.plist

# Load daemon
sudo launchctl load /Library/LaunchDaemons/com.ollama.serve.plist

# Start immediately
sudo launchctl start com.ollama.serve
```

**LaunchDaemon Management**:

```bash
# Load daemon (enable auto-start)
sudo launchctl load /Library/LaunchDaemons/com.ollama.serve.plist

# Unload daemon (disable auto-start)
sudo launchctl unload /Library/LaunchDaemons/com.ollama.serve.plist

# Start immediately
sudo launchctl start com.ollama.serve

# Stop immediately
sudo launchctl stop com.ollama.serve

# Check if running
sudo launchctl list | grep ollama
```

### 3. Verify Ollama Installation

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Expected response (JSON with installed models)
{"models":[]}

# Test from network
curl http://<Server-IP>:11434/api/tags
```

### 4. Install LLM Models

**Install gpt-oss:20b model** (20 billion parameters):

```bash
# Pull the model (this will take several minutes)
ollama pull gpt-oss:20b

# Verify installation
ollama list

# Expected output:
# NAME            ID              SIZE      MODIFIED
# gpt-oss:20b     abc123def456    12 GB     2 minutes ago
```

**Test model inference**:

```bash
# Test chat completion
ollama run gpt-oss:20b "What is the meaning of life?"

# Test via API
curl http://localhost:11434/api/generate -d '{
  "model": "gpt-oss:20b",
  "prompt": "Why is the sky blue?",
  "stream": false
}'
```

**Additional recommended models**:

```bash
# Smaller, faster model for testing
ollama pull llama3.2:3b

# Code-focused model
ollama pull codellama:13b

# Vision-capable model
ollama pull llava:13b
```

### 5. Install Open WebUI

Open WebUI provides a ChatGPT-like interface for Ollama.

```bash
# Start Open WebUI with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

**Access Open WebUI**:
- Local: http://localhost:8080
- Network: http://<Server-IP>:8080

**First-time setup**:
1. Open http://localhost:8080
2. Create admin account
3. Configure Ollama endpoint: http://host.docker.internal:11434
4. Select model: gpt-oss:20b
5. Start chatting!

## Configuration

### Ollama Settings

**Environment variables** (add to LaunchDaemon plist if needed):

```xml
<key>EnvironmentVariables</key>
<dict>
    <key>OLLAMA_HOST</key>
    <string>0.0.0.0:11434</string>
    <key>OLLAMA_MODELS</key>
    <string>/Users/Shared/ollama/models</string>
    <key>OLLAMA_MAX_LOADED_MODELS</key>
    <string>2</string>
    <key>OLLAMA_NUM_PARALLEL</key>
    <string>4</string>
</dict>
```

### Model Storage Location

Default: `~/.ollama/models`

**Change storage location**:

```bash
# Set custom path
export OLLAMA_MODELS=/path/to/models

# Or add to .zshrc / .bash_profile
echo 'export OLLAMA_MODELS=/Volumes/External/ollama/models' >> ~/.zshrc
```

### Performance Tuning

**GPU Memory Allocation**:

```bash
# Set GPU layers (default: auto)
export OLLAMA_NUM_GPU=33  # Use 33 GPU layers for gpt-oss:20b

# Limit memory usage
export OLLAMA_MAX_VRAM=16000  # 16GB max VRAM
```

**Concurrent Requests**:

```bash
# Number of parallel requests
export OLLAMA_NUM_PARALLEL=4

# Maximum loaded models
export OLLAMA_MAX_LOADED_MODELS=2
```

## Usage

### CLI Commands

```bash
# List installed models
ollama list

# Pull new model
ollama pull <model-name>

# Run interactive chat
ollama run gpt-oss:20b

# Remove model
ollama rm <model-name>

# Show model info
ollama show gpt-oss:20b

# Update Ollama
curl -fsSL https://ollama.ai/install.sh | sh
```

### API Integration

**Chat Completion**:

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "gpt-oss:20b",
  "messages": [
    {
      "role": "user",
      "content": "Explain quantum computing"
    }
  ],
  "stream": false
}'
```

**Text Generation**:

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "gpt-oss:20b",
  "prompt": "Write a Python function to reverse a string",
  "stream": false
}'
```

**Embeddings**:

```bash
curl http://localhost:11434/api/embeddings -d '{
  "model": "gpt-oss:20b",
  "prompt": "The sky is blue"
}'
```

## Troubleshooting

### Ollama Not Running

```bash
# Check if process exists
ps aux | grep ollama

# Check LaunchDaemon status
sudo launchctl list | grep ollama

# View logs
sudo tail -f /var/log/system.log | grep ollama

# Restart service
sudo launchctl stop com.ollama.serve
sudo launchctl start com.ollama.serve
```

### GPU Not Utilized

```bash
# Check GPU usage during inference
sudo powermetrics --samplers gpu_power -i 1000 -n 1

# Verify Metal support
ollama show gpt-oss:20b --verbose

# Should show: "metal: enabled"
```

### Model Download Issues

```bash
# Check disk space
df -h ~/.ollama

# Retry download
ollama pull gpt-oss:20b

# Manual download location
ls -lh ~/.ollama/models/blobs/
```

### Port Already in Use

```bash
# Find process using port 11434
lsof -i :11434

# Kill process
sudo kill -9 [PID]

# Change Ollama port
export OLLAMA_HOST=0.0.0.0:11435
```

### Open WebUI Connection Issues

**Error**: "Cannot connect to Ollama"

```bash
# Verify Ollama is accessible
curl http://localhost:11434/api/tags

# Check Docker network
docker exec -it open-webui curl http://host.docker.internal:11434/api/tags

# Update Open WebUI Ollama endpoint
# In UI: Settings → Connections → Ollama API URL
# Set to: http://host.docker.internal:11434
```

## Model Management

### Available Models

**Recommended for Production**:
- `gpt-oss:20b` (20B params, 12GB): Best quality/performance balance
- `llama3.2:8b` (8B params, 5GB): Faster, good quality
- `mistral:7b` (7B params, 4GB): Fast, efficient

**Specialized Models**:
- `codellama:13b`: Code generation
- `llava:13b`: Vision + language
- `deepseek-coder:6.7b`: Code completion

### Update Models

```bash
# Pull latest version
ollama pull gpt-oss:20b

# Old version is automatically archived
# Remove old versions
ollama rm gpt-oss:20b-old
```

### Backup Models

```bash
# Create backup
tar -czf ollama-models-backup.tar.gz ~/.ollama/models

# Restore backup
tar -xzf ollama-models-backup.tar.gz -C ~/
```

## Integration with aiproxysrv

The aiproxysrv backend proxies chat requests to Ollama.

**Configuration** (`aiproxysrv/.env`):

```bash
OLLAMA_API_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gpt-oss:20b
```

**API Endpoint**:

```bash
# Via aiproxysrv
curl http://localhost:5050/api/v1/ollama/chat -d '{
  "message": "Hello, how are you?",
  "model": "gpt-oss:20b"
}'
```

## Performance Benchmarks

**Mac Studio M1 Max (32GB)**:
- Model: gpt-oss:20b
- Tokens/second: 25-30
- First token latency: 200-300ms
- Memory usage: 14GB

**MacBook Air M4 (32GB)**:
- Model: gpt-oss:20b
- Tokens/second: 35-45
- First token latency: 150-200ms
- Memory usage: 13GB

## Upgrade Guide

### Update Ollama

```bash
# Download new version
wget https://github.com/ollama/ollama/releases/download/v0.13.0/ollama-darwin.tgz

# Stop service
sudo launchctl stop com.ollama.serve

# Replace binary
tar -xzf ollama-darwin.tgz
sudo mv ollama /usr/local/bin/

# Start service
sudo launchctl start com.ollama.serve

# Verify version
ollama --version
```

### Update Open WebUI

```bash
# Pull latest image
docker-compose pull

# Restart container
docker-compose up -d
```

## Best Practices

### DO

✅ Run Ollama natively on macOS (not Docker)
✅ Use LaunchDaemon for auto-start
✅ Monitor GPU usage during inference
✅ Keep models updated
✅ Use gpt-oss:20b for production quality
✅ Backup model directory regularly

### DON'T

❌ Run Ollama in Docker on Mac (slow!)
❌ Use all available RAM for models (leave 4GB+ free)
❌ Run multiple large models simultaneously
❌ Expose Ollama API to internet without auth
❌ Skip version updates (security & performance)

## Related Documentation

- **Ollama GitHub**: https://github.com/ollama/ollama
- **Open WebUI**: https://github.com/open-webui/open-webui
- **Backend Integration**: `../aiproxysrv/openai_impl.md`
- **Model Library**: https://ollama.ai/library

## Quick Reference

```bash
# Installation
wget https://github.com/ollama/ollama/releases/download/v0.12.0/ollama-darwin.tgz
tar -xzf ollama-darwin.tgz && sudo mv ollama /usr/local/bin/

# Setup auto-start
sudo cp LaunchDaemon/com.ollama.serve.plist /Library/LaunchDaemons/
sudo launchctl load /Library/LaunchDaemons/com.ollama.serve.plist

# Install model
ollama pull gpt-oss:20b

# Start Open WebUI
docker-compose up -d

# Test
curl http://localhost:11434/api/tags
ollama run gpt-oss:20b "Hello!"
```
