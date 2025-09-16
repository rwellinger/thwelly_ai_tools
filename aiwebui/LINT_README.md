# ESLint Konfiguration für aiwebui

## Übersicht

ESLint wurde für das Angular 17 Projekt konfiguriert mit angepassten Regeln für bestehenden Code.

## Verfügbare Scripts

```bash
# Standard Linting mit allen Ausgaben
npm run lint

# Automatische Fehlerbehebung wo möglich
npm run lint:fix

# Nur Fehler anzeigen (keine Warnungen)
npm run lint:check
```

## Konfiguration

Die Konfiguration in `eslint.config.js` verwendet:
- Standard Angular ESLint Regeln
- TypeScript ESLint Regeln
- Angepasste Regeln für bestehenden Code

### Angepasste Regeln

- `@typescript-eslint/no-explicit-any`: "warn" - Erlaubt `any` als Warnung
- `@angular-eslint/prefer-inject`: "warn" - Constructor injection erlaubt
- `@typescript-eslint/no-inferrable-types`: "off" - Explizite Typen erlaubt
- `@typescript-eslint/no-empty-function`: "off" - Leere Funktionen erlaubt
- Accessibility-Regeln als Warnungen statt Fehler

### Ignorierte Dateien

- Build-Verzeichnisse (`dist/`, `build/`)
- Test-Dateien (`**/*.spec.ts`)
- Umgebungsdateien (`src/environments/`)
- Auto-generierte Dateien

## Aktuelle Status

- **3 Fehler** (kritisch, sollten behoben werden)
- **11 Warnungen** (optional, für Code-Qualität)

### Verbleibende Fehler

1. `song.service.ts`: Unbenutzte Observable Import
2. `popup-audio-player.component.ts`: Output-Namen mit "on" Präfix (2x)

Diese können bei Bedarf manuell behoben werden.

## Vorschlag für CLAUDE.md

Füge zu deiner CLAUDE.md hinzu:

```
### Code Quality
- ESLint konfiguriert: `npm run lint`
- Automatische Fixes: `npm run lint:fix`
- Nur Fehler: `npm run lint:check`
```