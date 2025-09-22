# Produktions-Migration: Prompt-Config DB-Update

## Übersicht
Migration der Prompt-Templates von lokalem TypeScript Service zur PostgreSQL Datenbank.

## 1. Code-Update auf Produktion

```bash
# Git Repository aktualisieren
git pull origin main
```

## 2. Backend Migration (aiproxysrv)

### Docker Container stoppen
```bash
docker-compose down
```

### Neue Docker Images bauen
```bash
# Im aiproxysrv Verzeichnis
docker build -t aiproxysrv-app .
docker build -f celery.dockerfile -t celery-worker-app .
```

### DB-Migration ausführen
```bash
# Temporärer Container für Migration
docker run --rm \
  --network webui-network \
  -v $(pwd)/.env:/app/.env \
  aiproxysrv-app \
  alembic upgrade head
```

### Templates in DB laden
```bash
# Seeding Script ausführen
docker run --rm \
  --network webui-network \
  -v $(pwd)/.env:/app/.env \
  aiproxysrv-app \
  python scripts/seed_prompts.py
```

## 3. Frontend Update (aiwebui)

### Build und Deploy
```bash
# Im aiwebui Verzeichnis
npm run build:prod

# Output wird automatisch nach forwardproxy/html/aiwebui kopiert
```

## 4. Services neu starten

```bash
# Alle Services hochfahren
docker-compose up -d
```

## 5. Verification

### API testen
```bash
# Alle Templates abrufen
curl -s http://localhost:5050/api/v1/prompts | jq

# Spezifisches Template testen
curl -s http://localhost:5050/api/v1/prompts/music/enhance | jq
```

### Frontend prüfen
- Browser öffnen: https://deine-domain.com
- Song Generator → Style Prompt → Dropdown testen
- Bei API-Problemen: Automatischer Fallback auf lokale Templates

## 6. Neue API-Endpoints

Nach Migration verfügbar:

```bash
# Alle Templates
GET /api/v1/prompts

# Templates einer Kategorie
GET /api/v1/prompts/{category}

# Spezifisches Template
GET /api/v1/prompts/{category}/{action}

# Template aktualisieren
PUT /api/v1/prompts/{category}/{action}

# Neues Template erstellen
POST /api/v1/prompts
```

## 7. Rollback-Plan

Falls Probleme auftreten:

```bash
# Zurück zur vorherigen Migration
docker run --rm \
  --network webui-network \
  -v $(pwd)/.env:/app/.env \
  aiproxysrv-app \
  alembic downgrade df73746c9254
```

**Hinweis**: Frontend nutzt automatisch lokale Fallback-Templates bei API-Fehlern.

## 8. Benefits nach Migration

- ✅ Zentrale Template-Verwaltung in DB
- ✅ Dynamische Prompt-Updates ohne Deployment
- ✅ API für Template-Management
- ✅ Fallback-Sicherheit bei API-Problemen
- ✅ Caching für bessere Performance

## 9. Troubleshooting

### DB-Connection Probleme
```bash
# Container Logs prüfen
docker logs aiproxysrv-app

# DB-Status prüfen
docker exec postgres-container psql -U aiproxy -d aiproxysrv -c "\dt"
```

### Frontend API-Fehler
- Überprüfe Browser Console
- API-Calls werden automatisch auf Fallback umgestellt
- Logs: `console.warn('Failed to load prompt templates from API')`

---

**Geschätzte Downtime**: 2-3 Minuten für Docker-Restart