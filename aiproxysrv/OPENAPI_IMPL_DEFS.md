# OpenAPI/Swagger Implementation Documentation

## Overview

Flask-based API with Pydantic validation and OpenAPI/Swagger documentation, ensuring compatibility with Celery workers.

## Architecture

### Core Components

**Pydantic Schemas** (`schemas/`)
- `common_schemas.py`: BaseResponse, ErrorResponse, PaginationResponse
- `image_schemas.py`: Image generation and management schemas
- `song_schemas.py`: Song generation, listing, and stem generation schemas
- `chat_schemas.py`: Chat request/response schemas

**Integration**
- `flask-pydantic>=0.12.0`: Request/response validation
- `apispec[validation]>=6.3.0`: OpenAPI spec generation
- `flask-apispec>=0.11.4`: Flask-Pydantic integration

**Celery Safety**
- Schemas use only standard Python + Pydantic
- No Flask module imports in schemas
- No direct DB model imports in schemas

## API Documentation

**Swagger UI**: `http://localhost:8000/api/docs`
**OpenAPI JSON**: `http://localhost:8000/api/openapi.json`

### Validated Endpoints

**Images**
- POST `/api/v1/image/generate` - Generate image with schema validation
- GET `/api/v1/image/list` - List images with pagination
- PUT `/api/v1/image/{id}` - Update image metadata

**Songs**
- POST `/api/v1/song/generate` - Generate song with schema validation
- GET `/api/v1/song/list` - List songs with pagination
- POST `/api/v1/song/{id}/stem/generate` - Generate stems

**Chat**
- POST `/api/v1/chat/generate` - Generate chat response

## Development

### Start Services

```bash
# Flask Server
python server.py

# Celery Worker
celery -A worker worker --loglevel=info

# Check Worker Status
celery -A worker inspect active
celery -A worker inspect stats
```

### Testing

```bash
# Valid Request
curl -X POST http://localhost:8000/api/v1/image/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test image","size":"1024x1024"}'

# Schema Validation Test (should fail)
curl -X POST http://localhost:8000/api/v1/image/generate \
  -H "Content-Type: application/json" \
  -d '{"invalid_field":"value"}'
```

## Features

✅ **Automatic Schema Validation**: Request/response validation via Pydantic
✅ **Interactive Documentation**: Swagger UI with all endpoints
✅ **Type Safety**: Full type annotations and validation
✅ **Error Handling**: Standardized error responses
✅ **Celery Compatible**: Parallel service execution without conflicts
✅ **Frontend Compatible**: Backward compatible with aiwebui