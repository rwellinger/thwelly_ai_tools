# AI Test Mock - Development Testing API

Mock API server for testing AI generation features without incurring external API costs. Simulates OpenAI and Mureka API responses with configurable test scenarios.

## Overview

The AI Test Mock provides a local testing environment that replicates external API behavior, enabling:
- **Cost-Free Development**: Test without OpenAI or Mureka API charges
- **Predictable Responses**: Controlled test scenarios with known outcomes
- **Async Simulation**: Realistic job processing with configurable delays
- **Error Testing**: Simulate error conditions (rate limits, invalid tokens, failures)
- **Offline Development**: Work without internet connectivity

## Architecture

### Core Components

**Flask Server** (`src/server.py`)
- Lightweight HTTP server on port 3080
- CORS enabled for frontend integration
- Health check endpoint

**API Routes**
- `src/api/openai.py`: OpenAI DALL-E image generation simulation
- `src/api/mureka.py`: Mureka song/instrumental generation simulation
- `src/api/chat.py`: Chat API simulation

**Controllers** (`src/controllers/`)
- `openai_controller.py`: Image generation logic
- `mureka_controller.py`: Song/instrumental generation logic

**Services** (`src/services/`)
- `openai_service.py`: Mock data loading and response generation
- `mureka_service.py`: Async job simulation with timing control

**Mock Data** (`data/`)
- JSON response files for different test scenarios
- Static image/audio files for realistic responses

## Project Structure

```
aitestmock/
├── src/
│   ├── api/                 # Route definitions
│   ├── controllers/         # Request handling logic
│   ├── services/           # Business logic & mock data
│   ├── config/             # Configuration settings
│   ├── utils/              # Logging utilities
│   └── server.py           # Flask application entry point
├── data/
│   ├── openai/             # OpenAI mock responses
│   │   ├── 0001/           # Success scenario
│   │   └── 0002/           # Error scenario
│   └── mureka/             # Mureka mock responses
│       ├── 0001/           # Success scenario
│       ├── 0002/           # Invalid token scenario
│       └── 0003/           # Generation failed scenario
└── static/                 # Static files (images, audio)
```

## Getting Started

### Prerequisites

- Python 3.9+
- pip or conda package manager

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or with conda
conda activate mac_ki_service
pip install -r requirements.txt
```

### Start Server

```bash
# Development server
python src/server.py

# Server runs on http://localhost:3080
```

### Health Check

```bash
curl http://localhost:3080/health
# Response: {"status": "ok"}
```

## API Endpoints

### Base URL

`http://localhost:3080`

### OpenAI Endpoints

#### Generate Image

```bash
POST /v1/images/generations
Content-Type: application/json
Authorization: Bearer test-token

{
  "prompt": "0001 a beautiful sunset",
  "model": "dall-e-3",
  "size": "1024x1024",
  "quality": "standard",
  "n": 1
}
```

**Supported Sizes**:
- `1024x1024`: Square format
- `1792x1024`: Landscape format
- `1024x1792`: Portrait format

### Mureka Endpoints

#### Generate Song

```bash
POST /v1/song/generate
Content-Type: application/json
Authorization: Bearer test-token

{
  "lyrics": "0001 verse one, verse two",
  "model": "auto",
  "prompt": "rock style, 30s"
}
```

#### Query Song Status

```bash
GET /v1/song/query/{job_id}
Authorization: Bearer test-token
```

#### Generate Stems

```bash
POST /v1/song/stem
Content-Type: application/json
Authorization: Bearer test-token

{
  "url": "0001 http://example.com/song.mp3"
}
```

#### Get Billing Info

```bash
GET /v1/account/billing
Authorization: Bearer test-token
```

#### Generate Instrumental

```bash
POST /v1/instrumental/generate
Content-Type: application/json
Authorization: Bearer test-token

{
  "model": "auto",
  "prompt": "0001 jazz style, 20s"
}
```

#### Query Instrumental Status

```bash
GET /v1/instrumental/query/{job_id}
Authorization: Bearer test-token
```

## Test Scenarios

Test scenarios are controlled by special codes in request parameters (prompt, lyrics, or URL).

### Test Number Format

Include a 4-digit test number at the beginning of the parameter:
- `"0001 your content"` → Success scenario
- `"0002 your content"` → Error scenario (invalid token)
- `"0003 your content"` → Error scenario (generation failed)

### Duration Control

Simulate processing time by including duration in the prompt:
- `"30s rock style"` → 30 second processing delay
- `"1m jazz style"` → 1 minute processing delay
- `"10s delay"` → 10 second processing delay

**Default durations**:
- Songs: 2 seconds
- Instrumentals: 10 seconds
- Images: Instant (or custom delay)

### Image Generation Scenarios

**Success (0001)**
```bash
curl -X POST http://localhost:3080/v1/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token" \
  -d '{
    "prompt": "0001 beautiful landscape",
    "size": "1024x1024"
  }'
```

**Response**:
```json
{
  "created": 1234567890,
  "data": [
    {
      "url": "http://localhost:3080/static/images/82ce2c8095_1757869305.png",
      "revised_prompt": "beautiful landscape"
    }
  ]
}
```

**Invalid Token (0002)**
```bash
curl -X POST http://localhost:3080/v1/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token" \
  -d '{
    "prompt": "0002 test image",
    "size": "1024x1024"
  }'
```

**Response**: 401 Unauthorized
```json
{
  "error": {
    "message": "Incorrect API key provided",
    "type": "invalid_request_error",
    "code": "invalid_api_key"
  }
}
```

### Song Generation Scenarios

**Success with 30s delay (0001)**
```bash
curl -X POST http://localhost:3080/v1/song/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token" \
  -d '{
    "lyrics": "0001 verse one verse two",
    "model": "auto",
    "prompt": "30s rock style"
  }'
```

**Response**:
```json
{
  "id": "job-12345",
  "status": "processing"
}
```

**Query Status (after 30s)**
```bash
curl http://localhost:3080/v1/song/query/job-12345 \
  -H "Authorization: Bearer test-token"
```

**Response**:
```json
{
  "id": "job-12345",
  "status": "succeeded",
  "data": {
    "audio_url": "http://localhost:3080/static/audio/song.mp3",
    "title": "Generated Song"
  }
}
```

**Invalid Token (0002)**
```bash
curl -X POST http://localhost:3080/v1/song/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token" \
  -d '{
    "lyrics": "0002 test lyrics",
    "model": "auto"
  }'
```

**Response**: 401 Unauthorized

**Generation Failed (0003)**
```bash
curl -X POST http://localhost:3080/v1/song/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token" \
  -d '{
    "lyrics": "0003 test lyrics",
    "model": "auto"
  }'
```

**Response**: 400 Bad Request
```json
{
  "error": "Generation failed",
  "message": "Unable to generate song with provided parameters"
}
```

## Integration with aiproxysrv

### Configuration

Update `aiproxysrv` environment variables to point to the mock server:

```bash
# .env
OPENAI_API_BASE_URL=http://localhost:3080/v1
MUREKA_API_BASE_URL=http://localhost:3080/v1
OPENAI_API_KEY=test-token
MUREKA_API_KEY=test-token
```

### Start Both Services

```bash
# Terminal 1: Start mock server
cd aitestmock
python src/server.py

# Terminal 2: Start aiproxysrv
cd aiproxysrv
python src/server.py

# Terminal 3: Start frontend
cd aiwebui
npm run dev
```

## Development

### Add New Test Scenario

1. **Create mock data directory**:
   ```bash
   mkdir -p data/openai/0004
   ```

2. **Add response JSON**:
   ```bash
   # data/openai/0004/response.json
   {
     "created": 1234567890,
     "data": [
       {
         "url": "http://localhost:3080/static/images/test.png",
         "revised_prompt": "test scenario"
       }
     ]
   }
   ```

3. **Add static files** (if needed):
   ```bash
   cp image.png static/images/test.png
   ```

4. **Test scenario**:
   ```bash
   curl -X POST http://localhost:3080/v1/images/generations \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer test-token" \
     -d '{"prompt": "0004 test"}'
   ```

### Custom Duration Testing

Test async processing with custom delays:

```bash
# 5 second delay
curl -X POST http://localhost:3080/v1/song/generate \
  -d '{"lyrics": "0001 test", "prompt": "5s delay"}'

# 2 minute delay
curl -X POST http://localhost:3080/v1/song/generate \
  -d '{"lyrics": "0001 test", "prompt": "2m delay"}'
```

## Logging

Logs are output to console with structured formatting using Loguru.

**Log levels**: DEBUG, INFO, WARNING, ERROR

**Configure log level**:
```python
# config/settings.py
LOG_LEVEL = "DEBUG"
```

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 3080
lsof -i :3080

# Kill process
sudo kill -9 [PID]
```

### Mock Data Not Found

**Error**: `Mock data not found for test number 0005`

**Solution**: Verify directory structure and JSON files exist:
```bash
ls -la data/openai/0005/
cat data/openai/0005/response.json
```

### CORS Issues

CORS is enabled by default. If issues persist:

```python
# src/server.py
CORS(app, resources={r"/*": {"origins": "*"}})
```

### Authorization Errors

The mock server requires `Authorization: Bearer <token>` header for all requests except `/health`.

```bash
# Missing auth
curl http://localhost:3080/v1/images/generations
# Response: 401 Unauthorized

# With auth
curl -H "Authorization: Bearer test-token" \
     http://localhost:3080/v1/images/generations
# Response: 200 OK
```

## Best Practices

### DO

✅ Use test numbers to control scenarios (`0001`, `0002`, etc.)
✅ Include duration for realistic async testing (`30s`, `1m`)
✅ Test error scenarios before implementing error handling
✅ Use mock server for local development and testing
✅ Keep mock data files organized by test number

### DON'T

❌ Use mock server in production
❌ Commit sensitive API keys in mock data
❌ Skip authorization headers in requests
❌ Forget to start mock server before testing
❌ Hardcode mock URLs in production code

## Test Coverage

### Supported Test Scenarios

**Image Generation**:
- ✅ Success (0001)
- ✅ Invalid API key (0002)
- ✅ Custom delays
- ✅ All image sizes (square, landscape, portrait)

**Song Generation**:
- ✅ Success (0001)
- ✅ Invalid token (0002)
- ✅ Generation failed (0003)
- ✅ Async job processing
- ✅ Custom duration delays

**Instrumental Generation**:
- ✅ Success (0001)
- ✅ Error scenarios
- ✅ Async job processing

**Stems Generation**:
- ✅ Success (0001)
- ✅ Error scenarios

**Account Info**:
- ✅ Billing information (0001)

## Performance

- **Image generation**: Instant (configurable delay)
- **Song generation**: 2s default (configurable)
- **Instrumental generation**: 10s default (configurable)
- **Stems generation**: 2s fixed
- **Status queries**: Instant

## Future Enhancements

- [ ] Add rate limiting simulation
- [ ] Support for batch operations
- [ ] WebSocket support for real-time updates
- [ ] More error scenarios (quota exceeded, network errors)
- [ ] Request/response logging to file
- [ ] Mock data randomization

## Contributing

1. Add new test scenarios in `data/` directory
2. Update service logic in `src/services/`
3. Test with aiproxysrv integration
4. Document new scenarios in this README

## Related Documentation

- **Backend API**: `../aiproxysrv/openai_impl.md`
- **Frontend**: `../aiwebui/README.md`
- **Project Overview**: `../.claude/CLAUDE.md`
