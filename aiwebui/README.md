# AI Web UI - Angular 18 Frontend

Angular-based web interface for AI-powered image and song generation, integrated with the aiproxysrv backend.

## Overview

This Angular 18 application provides a user-friendly interface for:
- **Image Generation**: AI-powered image creation via DALL-E/OpenAI API
- **Song Generation**: AI music creation via Mureka API
- **Media Management**: Browse, rate, and organize generated content
- **Prompt Templates**: Reusable prompt management
- **User Profiles**: Account settings and preferences

## Technology Stack

- **Angular 18**: Frontend framework
- **Angular Material**: UI component library
- **SCSS**: Styling with custom themes
- **TypeScript**: Type-safe development
- **HttpClient**: API communication with JWT injection
- **RxJS**: Reactive programming

## Project Structure

```
src/app/
├── pages/                    # Feature modules
│   ├── image-generator/      # Image generation UI
│   ├── image-view/           # Image gallery and details
│   ├── song-generator/       # Song generation UI
│   ├── song-view/            # Song library and playback
│   ├── song-profile/         # Mureka account status
│   ├── prompt-templates/     # Prompt management
│   └── user-profile/         # User settings
├── components/               # Shared UI components
├── services/                 # Business logic & API calls
├── pipes/                    # Data transformation utilities
├── models/                   # TypeScript interfaces
├── guards/                   # Route protection
├── interceptors/             # HTTP request/response handling
└── auth/                     # Authentication logic
```

## Development

### Prerequisites

- Node.js 18+ with npm
- Backend service (aiproxysrv) running on `http://localhost:5050`

### Install Dependencies

```bash
npm install
```

### Development Server

```bash
npm run dev
# or
ng serve
```

Navigate to `http://localhost:4200/`. The application automatically reloads on file changes.

### Code Quality

```bash
# Run linter
npm run lint

# Fix linting issues
npm run lint -- --fix
```

## Build

### Development Build

```bash
npm run build
```

Build artifacts are stored in `dist/` directory.

### Production Build

```bash
npm run build:prod
```

**IMPORTANT**: Production build outputs to `../forwardproxy/html/aiwebui/` for nginx deployment.

**Always run after changes**:
```bash
cd aiwebui && npm run build && npm run lint
```

## Code Scaffolding

### Generate Components

```bash
ng generate component component-name
ng generate directive|pipe|service|class|guard|interface|enum|module
```

### Preferred Location
- Pages: `src/app/pages/feature-name/`
- Shared: `src/app/components/shared-component/`

## API Integration

### Backend Base URL

Development: `http://localhost:5050/api`

### Key Services

**ImageService** (`services/image.service.ts`)
- `generateImage()`: Create new image
- `getImages()`: List images with pagination
- `getImage()`: Get specific image
- `updateImage()`: Update metadata
- `deleteImage()`: Remove image

**SongService** (`services/song.service.ts`)
- `generateSong()`: Create new song
- `getSongs()`: List songs with pagination
- `getSong()`: Get specific song
- `updateSong()`: Update metadata
- `generateStems()`: Create song stems

**PromptService** (`services/prompt.service.ts`)
- `getPrompts()`: List available prompts
- `createPrompt()`: Create new prompt template

### HTTP Client Usage

**IMPORTANT**: Always use `HttpClient` instead of `fetch` for JWT injection via interceptors.

```typescript
import { HttpClient } from '@angular/common/http';

constructor(private http: HttpClient) {}

getData(): Observable<Response> {
  return this.http.get<Response>(`${this.baseUrl}/endpoint`);
}
```

## Architecture Patterns

### Component Pattern

```typescript
@Component({
  selector: 'app-feature',
  templateUrl: './feature.component.html',
  styleUrls: ['./feature.component.scss']
})
export class FeatureComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  ngOnInit(): void {
    this.loadData();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadData(): void {
    this.service.getData()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => this.handleData(data),
        error: (error) => this.handleError(error)
      });
  }
}
```

### Service Pattern

```typescript
@Injectable({
  providedIn: 'root'
})
export class DataService {
  private readonly baseUrl = 'http://localhost:5050/api';

  constructor(private http: HttpClient) {}

  getData(): Observable<Item[]> {
    return this.http.get<ApiResponse<Item[]>>(`${this.baseUrl}/items`)
      .pipe(
        map(response => response.data),
        catchError(this.handleError)
      );
  }
}
```

## Styling

### SCSS Structure

- **Global styles**: `src/styles.scss`
- **Component styles**: `*.component.scss`
- **Mixins**: Reusable style patterns
- **Variables**: Theme colors, spacing, breakpoints

### Master-Detail Layout

```scss
.master-detail-container {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: $spacing-lg;
  height: calc(100vh - 200px);
  overflow: hidden;

  .master-panel {
    overflow-y: auto;
    min-width: 0;
  }

  .detail-panel {
    overflow-y: auto;
    overflow-x: hidden;
  }

  @media (max-width: 1024px) {
    grid-template-columns: 1fr;
  }
}
```

## Testing

### Unit Tests

```bash
npm run test

# Watch mode
npm run test -- --watch
```

Tests use [Karma](https://karma-runner.github.io) test runner.

### End-to-End Tests

```bash
npm run e2e
```

## Deployment

### Production Deployment Flow

1. **Build production bundle**:
   ```bash
   cd aiwebui
   npm run build:prod
   ```

2. **Output location**: `../forwardproxy/html/aiwebui/`

3. **Nginx serves** the static files via reverse proxy configuration

4. **Backend API** proxied through nginx to aiproxysrv

### Environment Configuration

Development: `src/environments/environment.ts`
Production: `src/environments/environment.prod.ts`

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 4200
lsof -i :4200

# Kill process
sudo kill -9 [PID]
```

### Build Errors

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Angular cache
rm -rf .angular
```

### API Connection Issues

- Verify backend is running: `curl http://localhost:5050/api/health`
- Check browser console for CORS errors
- Verify HttpClient is used (not fetch)

## Best Practices

### DO

✅ Use HttpClient for all API calls (JWT injection)
✅ Run `npm run build && npm run lint` before committing
✅ Follow clean code patterns
✅ Implement proper subscription cleanup with `takeUntil()`
✅ Use Angular Material components
✅ Follow BEM-inspired CSS naming

### DON'T

❌ Use `fetch()` for API calls (bypasses JWT interceptor)
❌ Skip linting before commits
❌ Forget to unsubscribe from observables
❌ Mix component logic with presentation
❌ Hardcode API URLs (use environment config)

## Contributing

1. Create feature branch from `main`
2. Make changes following code standards
3. Run linting and build
4. Test locally with backend
5. Commit with descriptive message
6. Create pull request

## Further Help

- **Angular CLI**: `ng help` or [Angular CLI Docs](https://angular.io/cli)
- **Angular Material**: [Material Components](https://material.angular.io/)
- **Backend API**: See `../aiproxysrv/openai_impl.md`
