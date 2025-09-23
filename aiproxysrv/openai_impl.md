# OpenAPI/Swagger Implementation Plan - Branch: openapi-umstellung

**Ziel**: Flask + Pydantic + OpenAPI/Swagger Integration ohne Celery-Konflikte

**Timeline**: ~4.5h mit Buffer für Tests

---

## 📋 Phase 1: Dependencies & Setup (30min)

### 1.1 Dependencies hinzufügen
- [ ] `flask-pydantic>=0.12.0` zu pyproject.toml
- [ ] `apispec[validation]>=6.3.0` zu pyproject.toml
- [ ] `flask-apispec>=0.11.4` zu pyproject.toml
- [ ] Dependencies installieren: `pip install -e .`

### 1.2 Celery-Test (Baseline)
- [ ] Celery Worker starten: `celery -A worker worker --loglevel=info`
- [ ] Test-Song generieren (Baseline funktioniert)
- [ ] Worker stoppen

**Git Commit**: `feat: add OpenAPI dependencies`

---

## 📋 Phase 2: Pydantic Schemas (60min)

### 2.1 Common Schemas (15min)
```python
# schemas/common_schemas.py
- [ ] BaseResponse
- [ ] ErrorResponse
- [ ] PaginationResponse
- [ ] ValidationErrorResponse
```

### 2.2 Image Schemas (15min)
```python
# schemas/image_schemas.py
- [ ] ImageGenerateRequest
- [ ] ImageResponse
- [ ] ImageListRequest
- [ ] ImageListResponse
- [ ] ImageUpdateRequest
```

### 2.3 Song Schemas (20min)
```python
# schemas/song_schemas.py
- [ ] SongGenerateRequest
- [ ] SongResponse
- [ ] SongListRequest
- [ ] SongListResponse
- [ ] SongUpdateRequest
- [ ] StemGenerateRequest
```

### 2.4 Chat Schemas (10min)
```python
# schemas/chat_schemas.py
- [ ] ChatRequest
- [ ] ChatResponse
- [ ] ChatOptions
```

**Celery-Safety Check**:
- [ ] Schemas importieren **KEINE** Flask-Module
- [ ] Schemas importieren **KEINE** DB-Models direkt
- [ ] Nur Standard-Python + Pydantic

**Git Commit**: `feat: add Pydantic schemas for all APIs`

---

## 📋 Phase 3: Flask-Pydantic Integration (90min)

### 3.1 OpenAPI Setup in app.py (20min)
- [ ] Import `flask-pydantic`, `apispec`
- [ ] OpenAPI spec configuration
- [ ] Swagger UI route `/api/docs`
- [ ] JSON spec route `/api/openapi.json`

### 3.2 Image Routes Refactor (25min)
- [ ] Import Image Schemas
- [ ] `@validate()` Decorator für `/generate`
- [ ] `@validate()` Decorator für `/list`
- [ ] `@validate()` Decorator für andere Endpoints
- [ ] Response Schema Validation

### 3.3 Song Routes Refactor (30min)
- [ ] Import Song Schemas
- [ ] `@validate()` für `/generate`
- [ ] `@validate()` für `/list`
- [ ] `@validate()` für `/stem/generate`
- [ ] `@validate()` für andere Endpoints

### 3.4 Chat Routes Refactor (15min)
- [ ] Import Chat Schemas
- [ ] `@validate()` für `/generate`
- [ ] Response Schema Validation

**Celery-Test nach jeder Route-Gruppe**:
- [ ] Image Routes → Celery Test
- [ ] Song Routes → Celery Test
- [ ] Chat Routes → Celery Test

**Git Commit**: `feat: integrate Pydantic validation in routes`

---

## 📋 Phase 4: OpenAPI/Swagger UI (30min)

### 4.1 OpenAPI Spec Generation (15min)
- [ ] Automatic schema generation aus Pydantic models
- [ ] API Info (title, version, description)
- [ ] Server configurations
- [ ] Tags für API grouping

### 4.2 Swagger UI Konfiguration (15min)
- [ ] Custom Swagger UI title
- [ ] API documentation unter `/api/docs`
- [ ] JSON spec unter `/api/openapi.json`
- [ ] Test Swagger UI Funktionalität

**Final Celery Test**:
- [ ] Beide Services parallel starten
- [ ] Song-Generierung testen
- [ ] Swagger UI testen

**Git Commit**: `feat: add OpenAPI spec generation and Swagger UI`

---

## 📋 Phase 5: Testing & Finalisierung (60min)

### 5.1 API Testing (20min)
- [ ] Alle Image Endpoints via Swagger UI
- [ ] Alle Song Endpoints via Swagger UI
- [ ] Alle Chat Endpoints via Swagger UI
- [ ] Schema Validierung (invalid requests)

### 5.2 Integration Tests (20min)
- [ ] Frontend (aiwebui) Kompatibilität prüfen
- [ ] Error Handling testen
- [ ] Response Format Konsistenz

### 5.3 Dokumentation (20min)
- [ ] README Update mit `/api/docs` URL
- [ ] Example requests in OpenAPI descriptions
- [ ] Type annotations verify

**Git Commit**: `feat: finalize OpenAPI integration with tests`

---

## 🚨 Rollback Strategy

**Bei Celery-Problemen**:
1. `git log --oneline` → letzten funktionierenden Commit finden
2. `git reset --hard <commit-hash>`
3. Problem analysieren in separatem Branch

**Checkpoints**:
- Nach Phase 1: Dependencies installiert
- Nach Phase 2: Schemas erstellt
- Nach Phase 3: Route-Integration
- Nach Phase 4: Swagger UI funktional

---

## 🔍 Debug Commands

**Celery Worker**:
```bash
# Worker starten
celery -A worker worker --loglevel=info

# Worker Status prüfen
celery -A worker inspect active
celery -A worker inspect stats

# Worker stoppen
pkill -f "celery worker"
```

**Flask Server**:
```bash
# Development Server
python server.py

# Swagger UI
# http://localhost:8000/api/docs

# OpenAPI JSON
# http://localhost:8000/api/openapi.json
```

**Testing**:
```bash
# API Test
curl -X POST http://localhost:8000/api/v1/image/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test image","size":"1024x1024"}'

# Schema Validation Test
curl -X POST http://localhost:8000/api/v1/image/generate \
  -H "Content-Type: application/json" \
  -d '{"invalid_field":"value"}'
```

---

## ✅ Success Criteria

- [ ] **Swagger UI funktional** unter `/api/docs`
- [ ] **Alle APIs dokumentiert** mit korrekten Schemas
- [ ] **Request/Response Validierung** funktioniert
- [ ] **Celery Worker läuft parallel** ohne Probleme
- [ ] **Frontend bleibt kompatibel** (aiwebui)
- [ ] **Error Handling** mit validen OpenAPI Responses

---

## 📝 Notes & Learnings

**Problems encountered:**
<!-- Hier Probleme dokumentieren während Implementation -->

**Solutions found:**
<!-- Hier Lösungen dokumentieren -->

**Performance notes:**
<!-- Performance-Beobachtungen -->

**Future improvements:**
<!-- Ideen für weitere Verbesserungen -->