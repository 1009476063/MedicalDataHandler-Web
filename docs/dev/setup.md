# Development Setup

## Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **pnpm** (recommended) or npm
- **Git**

## Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API docs are available at `http://localhost:8000/docs`.

## Frontend Setup

```bash
cd frontend

# Install dependencies
pnpm install

# Start development server
pnpm dev

# Type-check
vue-tsc --noEmit

# Build for production
pnpm build

# Lint
pnpm lint
```

## Environment Variables

### Backend (`.env` in `backend/`)

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `JWT_SECRET` | — | Yes | Secret key for JWT tokens |
| `AI_API_BASE` | — | No | OpenAI-compatible API base URL |
| `AI_API_KEY` | — | No | API key for AI analysis |
| `AI_DEFAULT_MODEL` | `gpt-4o` | No | Default AI model |
| `AI_BACKEND` | `openai` | No | AI backend type |

### Frontend (`.env` in `frontend/`)

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Backend API URL |

## Project Structure

```
MedVista/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry
│   │   ├── routers/             # API route handlers
│   │   │   ├── dicom.py         # DICOM upload & processing
│   │   │   ├── ai.py            # AI analysis endpoints
│   │   │   ├── converter.py     # Format conversion
│   │   │   ├── anonymization.py # DICOM anonymization
│   │   │   ├── seg.py           # Segmentation
│   │   │   ├── four_d.py        # 4D sequences
│   │   │   ├── annotations.py   # Measurements
│   │   │   ├── export.py        # Export endpoints
│   │   │   ├── dicomweb.py      # PACS connectivity
│   │   │   ├── analysis.py      # Sequence analysis
│   │   │   ├── medical_formats.py # Multi-format support
│   │   │   ├── postprocessing.py  # Image processing
│   │   │   ├── config.py        # Configuration
│   │   │   ├── system.py        # System info
│   │   │   └── logging.py       # Logging
│   │   └── services/            # Business logic
│   │       ├── dicom_service.py # DICOM parsing
│   │       ├── ai_service.py    # AI integration
│   │       ├── nifti_service.py # NIfTI support
│   │       └── ...
│   ├── requirements.txt
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── viewer/          # Viewer components
│   │   │   │   ├── ViewerSidebar.vue
│   │   │   │   ├── ViewerHeader.vue
│   │   │   │   ├── AIPanel.vue
│   │   │   │   ├── MeasurementToolbar.vue
│   │   │   │   └── TimeSlider.vue
│   │   │   └── common/          # Shared components
│   │   ├── composables/         # Vue composables
│   │   │   ├── useFusion.ts     # PET-CT fusion
│   │   │   ├── useAI.ts         # AI analysis
│   │   │   ├── useTools.ts      # Measurement tools
│   │   │   ├── useSegmentation.ts # SEG overlay
│   │   │   ├── useFourD.ts      # 4D playback
│   │   │   ├── useSettings.ts   # User settings
│   │   │   └── useClientMode.ts # Client-side rendering
│   │   ├── views/               # Page views
│   │   │   ├── ViewerView.vue   # Main viewer
│   │   │   ├── DashboardView.vue
│   │   │   ├── ConverterView.vue
│   │   │   ├── AnonymizationView.vue
│   │   │   ├── ExportView.vue
│   │   │   └── SettingsView.vue
│   │   ├── stores/              # Pinia stores
│   │   ├── i18n/                # Internationalization
│   │   ├── types/               # TypeScript types
│   │   └── router/              # Vue Router config
│   ├── package.json
│   └── vite.config.ts
├── docs/                        # Documentation
│   ├── user-guide/
│   ├── api/
│   └── dev/
└── test-data/                   # Sample DICOM data
```

## Testing

### Backend

```bash
cd backend
python -m pytest tests/ -v
```

### Frontend

```bash
cd frontend
pnpm test          # Unit tests
pnpm build         # Verify production build
```

## Code Quality

### Linting

```bash
cd frontend
pnpm lint          # Run ESLint
pnpm lint --fix    # Auto-fix
```

### Type Checking

```bash
cd frontend
vue-tsc --noEmit   # TypeScript check
```

## Git Workflow

1. Create a feature branch: `git checkout -b feat/my-feature`
2. Make changes and commit with conventional format
3. Run tests and type checks
4. Push and create a pull request

### Commit Message Format

```
<type>: <description>

[optional body]
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`

## Common Development Tasks

### Adding a New API Endpoint

1. Create the route handler in `backend/app/routers/`
2. Register the router in `backend/app/main.py`
3. Add types in `frontend/src/types/index.ts`
4. Add API client method in the appropriate composable
5. Add i18n keys if the endpoint is user-facing

### Adding a New View

1. Create the component in `frontend/src/views/`
2. Add the route in `frontend/src/router/`
3. Add navigation in `ViewerSidebar.vue`
4. Add i18n keys for the view title and content

### Adding a New Composable

1. Create `frontend/src/composables/use{Name}.ts`
2. Follow the existing pattern (ref/reactive state, async methods, return object)
3. Wire into `ViewerView.vue` or the relevant parent component
