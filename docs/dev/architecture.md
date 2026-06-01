# Architecture

## System Overview

MedVista is a web-based medical image viewer with a Vue 3 frontend and FastAPI backend. The backend handles DICOM parsing, pixel data storage, and heavy computation. The frontend renders images using Cornerstone3D (WebGL) with a Canvas2D fallback for incompatible browsers.

```
┌─────────────────────────────────────────────────────────┐
│                    Browser (Vue 3)                       │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐  │
│  │ Dashboard│  │  Viewer  │  │Converter │  │Settings │  │
│  └────┬────┘  └────┬─────┘  └────┬─────┘  └─────────┘  │
│       │             │              │                      │
│  ┌────┴─────────────┴──────────────┴──────────────────┐  │
│  │              Composables Layer                      │  │
│  │  useTools │ useFusion │ useAI │ useSegmentation     │  │
│  └────────────────────┬───────────────────────────────┘  │
│                       │                                   │
│  ┌────────────────────┴───────────────────────────────┐  │
│  │              Pinia Stores                           │  │
│  │  appStore │ patientStore │ settingsStore            │  │
│  └────────────────────┬───────────────────────────────┘  │
│                       │                                   │
│  ┌────────────────────┴───────────────────────────────┐  │
│  │              Axios HTTP Client                      │  │
│  └────────────────────┬───────────────────────────────┘  │
└───────────────────────┼─────────────────────────────────┘
                        │
                    HTTP API
                        │
┌───────────────────────┼─────────────────────────────────┐
│                FastAPI Backend                           │
│  ┌────────────────────┴───────────────────────────────┐  │
│  │              Routers (API Layer)                    │  │
│  │  dicom │ ai │ converter │ anonymization │ seg      │  │
│  └────────────────────┬───────────────────────────────┘  │
│                       │                                   │
│  ┌────────────────────┴───────────────────────────────┐  │
│  │              Services (Business Logic)              │  │
│  │  dicom_service │ ai_service │ nifti_service        │  │
│  └────────────────────┬───────────────────────────────┘  │
│                       │                                   │
│  ┌────────────────────┴───────────────────────────────┐  │
│  │              Storage Layer                          │  │
│  │  In-memory session dict │ Disk (.npy pixel data)   │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Frontend Architecture

### Rendering Pipeline

```
DICOM Upload → Backend Parsing → Volume Binary → Cornerstone3D Volume
                                                      │
                              ┌────────────────────────┤
                              │                        │
                         WebGL Path              Canvas2D Path
                    (GPU available)            (GPU fallback)
                              │                        │
                         setVolumes()            drawImage()
                              │                        │
                         MPR Viewport            2D Canvas
```

### Composable Pattern

Each major feature is encapsulated in a Vue composable:

```typescript
// composables use a consistent pattern:
export function useFeature() {
  // Reactive state
  const state = ref<T>()

  // Methods
  async function doSomething() { ... }

  // Cleanup
  onUnmounted(() => { ... })

  return { state, doSomething }
}
```

| Composable | Responsibility |
|-----------|----------------|
| `useTools` | Measurement tools (length, angle, ROI, probe, arrow) |
| `useFusion` | PET-CT dual-volume fusion with blend controls |
| `useAI` | AI analysis job management and SSE streaming |
| `useSegmentation` | DICOM SEG mask overlay |
| `useFourD` | 4D temporal sequence playback |
| `useSettings` | User preferences persistence |
| `useClientMode` | Client-side DICOM parsing fallback |

### Store Architecture

Three Pinia stores manage state:

- **appStore** — Session, patient, study, series selection
- **patientStore** — Patient list and metadata
- **settingsStore** — User preferences (window presets, opacity, etc.)

### i18n

Two locales: English (`en.ts`) and Chinese (`zh-CN.ts`). Keys are organized by feature area:

```typescript
viewer: {
  ai: { title, model, run, ... },
  fusion: { ctSeries, ptSeries, blend, ... },
  tools: { length, angle, roi, ... },
}
```

## Backend Architecture

### Data Flow

```
Client Upload
    │
    ▼
FastAPI Router (dicom.py)
    │
    ▼
DICOM Service (dicom_service.py)
    ├── Parse DICOM headers → metadata dict
    ├── Extract pixel data → numpy array
    ├── Save pixel data → disk (.npy)
    └── Store metadata → in-memory session dict
    │
    ▼
Volume Request
    │
    ▼
Volume Builder (image_builder.py)
    ├── Load .npy from disk
    ├── Apply window/level
    └── Return as uint8 binary
```

### Session Model

Sessions are stored in-memory:

```python
sessions = {
    "session_id": {
        "files": [...],           # Original file references
        "patients": [...],        # Patient metadata
        "studies": [...],         # Study metadata
        "series": [...],          # Series metadata
        "raw_data": {
            "series_uid": {
                "pixel_data": "path/to/file.npy",  # Disk path
                "metadata": {...},                  # DICOM tags
                "window": {"center": 40, "width": 400}
            }
        }
    }
}
```

Pixel data is stored as `.npy` files on disk to avoid holding large arrays in memory. The session dict only holds metadata and file paths.

### AI Integration

AI analysis uses OpenAI-compatible API with vision capabilities:

```
Frontend → POST /api/ai/analyze → Backend
                                      │
                                      ├── Load pixel data from disk
                                      ├── Convert to base64 PNG
                                      ├── Call vision API
                                      ├── Parse structured response
                                      └── Store results
                                      │
Frontend ← SSE /api/ai/jobs/{id}/stream ← Progress updates
```

### Rate Limiting

All endpoints are rate-limited using `slowapi`:
- Upload: 10 req/min
- Read: 100 req/min
- AI: 5 req/min

### Error Handling

Backend errors return consistent JSON:

```json
{
  "success": false,
  "data": null,
  "error": "Error description"
}
```

Uncaught exceptions are logged with full tracebacks and return 500 with a sanitized message.

## Key Design Decisions

### Why In-Memory Sessions?

- Simplicity — no database setup required
- Adequate for single-server deployment
- Session TTL cleanup prevents unbounded growth
- Can be replaced with Redis for multi-server deployments

### Why Disk-Based Pixel Data?

- Medical images can be 500MB+ per volume
- In-memory would cause OOM for multi-patient workflows
- `.npy` format is fast to load with numpy
- Enables lazy loading and demand paging

### Why Composable-First?

- Each feature (tools, fusion, AI) is self-contained
- Easy to test in isolation
- Clear ownership of state and lifecycle
- Vue 3 Composition API provides natural encapsulation

### Why Canvas2D Fallback?

- Some browsers/devices lack WebGL 2.0 support
- Mobile devices may have limited GPU capabilities
- Canvas2D provides basic viewing for these cases
- Full functionality requires WebGL

## Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | Vue 3 | 3.4+ |
| State | Pinia | 2.2+ |
| Routing | Vue Router | 4.3+ |
| i18n | vue-i18n | 9.14+ |
| Rendering | Cornerstone3D | 4.22+ |
| Styling | Tailwind CSS | 3.4+ |
| HTTP | Axios | 1.7+ |
| Backend | FastAPI | 0.115+ |
| DICOM | pydicom | 2.4+ |
| Medical I/O | nibabel, SimpleITK | latest |
| API Docs | Swagger/ReDoc | built-in |
| Rate Limiting | slowapi | 0.1+ |
