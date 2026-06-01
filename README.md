<p align="right">
  <b>English</b> | <a href="./README.zh-CN.md">中文</a>
</p>

# MedVista

A web-based medical image viewer and processing platform for radiation therapy. Supports DICOM, NIfTI, NRRD, and MHA formats with WebGL-powered 3D rendering, structure/dose overlays, RT plan analysis, PACS connectivity, and AI-powered analysis.

**Live Demo:** https://medical.1661688.xyz

![Version](https://img.shields.io/badge/version-2.1.0-059669)
![Vue 3](https://img.shields.io/badge/Vue-3-42b883?logo=vue.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.10+-3776ab?logo=python)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178c6?logo=typescript)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-06b6d4?logo=tailwindcss)
![Cornerstone3D](https://img.shields.io/badge/Cornerstone3D-4.22-ff6b35)

## Why MedVista?

MedVista is not just another DICOM viewer — it is a **complete radiation therapy imaging platform** that combines clinical-grade visualization with AI-powered intelligence, all running in a single web application.

### Unique Advantages

**1. Full RT Workflow Coverage**
Unlike general-purpose DICOM viewers, MedVista covers the entire radiation therapy pipeline: CT/MRI/PET viewing, RT structure contour visualization, dose distribution analysis, RT plan inspection, and TG-263 compliant structure naming — all in one tool.

**2. AI-Integrated Analysis**
MedVista embeds AI directly into the clinical workflow:
- **Multi-slice analysis** — sends 5 uniformly-distributed slices or MIP projection to vision models for richer context
- **Intelligent structure rename** — LLM-powered fuzzy matching maps non-standard DICOM structure names to TG-263 standards
- **Smart windowing** — AI suggests optimal window width/level based on modality and anatomy
- **Burned-in annotation detection** — vision AI identifies patient-identifiable text burned into pixel data
- **One-click SR generation** — AI findings convert directly into DICOM Structured Reports

**3. PET-CT Fusion with SUV**
First-class PET-CT fusion with automatic series pairing, adjustable blend ratio, and real-time SUV (Standardized Uptake Value) calculation — features typically found only in dedicated oncology workstations.

**4. Client-Server Hybrid Architecture**
MedVista works both with and without a backend. In client-only mode, DICOM parsing, rendering, and measurement all happen in the browser using WebWorkers and OffscreenCanvas. This enables offline clinical review, air-gapped environments, and zero-install deployment.

**5. Production-Grade Memory Management**
Built for real clinical datasets (10,000+ files, multi-GB studies):
- Disk-based pixel storage with numpy .npy format
- LRU caches with bounded memory
- Streaming volume transfer in 4MB chunks
- Background slice prefetching
- Virtual scrolling for large tag tables

**6. DICOM Protocol Native**
Full DICOMweb implementation (QIDO-RS, WADO-RS, STOW-RS) plus Modality Worklist, Structured Reports, and DICOM Print — not a proprietary connector, but standards-based PACS integration.

**7. Open Source & Self-Hosted**
MIT licensed, no vendor lock-in. Deploy on-premise for HIPAA/GDPR compliance. Configure any OpenAI-compatible API for AI features — no mandatory cloud subscription.

## Features

### WebGL 3D Viewer (Cornerstone3D)
- **GPU-Accelerated Rendering** — WebGL-powered volume rendering via Cornerstone3D with real-time MPR (axial, sagittal, coronal)
- **Synchronized Crosshairs** — Cross-plane localization using Cornerstone3D `CrosshairsTool`
- **Window/Level Presets** — CT, Lung, Bone, Soft Tissue, Brain, Subdural presets with interactive adjustment
- **Voxel Inspection** — Real-time HU/value readout at cursor position
- **DICOM Tag Inspector** — Searchable tag viewer with filtering
- **Image Controls** — Rotation, flip, zoom/pan speed, orientation labels

### Measurement & Annotation Tools
- **Length Tool** — Distance measurement in mm
- **Angle Tool** — Angle measurement in degrees
- **ROI Statistics** — Rectangle/Elliptical ROI with mean, std, min, max HU values
- **Probe Tool** — Point value inspection
- **Arrow Annotations** — Text annotations on images
- **Measurement Export** — CSV export of all measurements
- **Persistent Annotations** — Save/load annotations per study

### ROI Drawing (ITK-SNAP Style)
- **Drawing Tools** — Paintbrush, polygon, rectangle, ellipse, magic wand (flood fill), eraser
- **Multi-Label System** — Multiple labeled regions with custom name and color per label
- **Cross-Plane Sync** — Draw on any plane (axial/sagittal/coronal), masks render on all three simultaneously
- **Morphological Post-Processing** — Erode, dilate, Gaussian smooth on individual labels
- **Undo/Redo** — 30-level undo/redo with zlib-compressed snapshots
- **AI Segmentation** — Auto-detect pathology via vision AI, text-guided segmentation, reference-guided segmentation
- **Export Formats** — NIfTI label map (.nii.gz) and DICOM SEG for clinical PACS integration
- **NIfTI Import** — Load previously exported label maps for continued editing
- **Dual Rendering** — Works with both Cornerstone3D WebGL and Canvas2D fallback viewers

### DICOM Segmentation (SEG) Support
- **SEG Object Parsing** — Parse DICOM SEG objects and extract binary masks
- **Segment Overlay** — Display segmentation masks overlaid on volume data
- **Per-Segment Controls** — Individual color, visibility, and opacity per segment
- **Segmentation Panel** — Sidebar panel for segment management

### Structure & Dose Overlays
- **RT Structure Overlays** — Color-coded contour rendering with configurable opacity and thickness
- **ROI Centering** — One-click navigation to center of any structure across all planes
- **TG-263 Type Inference** — Automatic structure type classification (Target, OAR, External, etc.)
- **Dose Overlays** — Color-mapped dose distribution visualization
- **Dose Summation** — Combine multiple dose distributions into a single volume

### 4D Dynamic Sequence Support
- **Time-Series Data** — Support for 4D-CT, cardiac MRI, dynamic contrast-enhanced series
- **Time Slider** — Play/pause, frame rate control, step-by-step navigation
- **Automatic Detection** — Detect temporal positions from DICOM TemporalPositionIdentifier

### RT Plans
- **Plan Viewer** — Beam summary with energy, gantry angle, and weight
- **Fractionation Display** — Number of fractions, dose per fraction, total dose

### PET-CT Fusion
- **Dual-Volume Overlay** — Overlay PET on CT in the same viewport using Cornerstone3D multi-volume rendering
- **Blend Controls** — Adjustable blend ratio (0-100%) for PET opacity
- **Blend Mode Selection** — Additive or default blending modes
- **SUV Display** — Standardized Uptake Value calculation from DICOM metadata (RescaleSlope, PatientWeight, RadiopharmaceuticalDose)
- **Auto-Detection** — Automatically finds CT/PET series pairs within the same study
- **PET Presets** — Optimized window/level preset for PET (center: 2.5, width: 15)

### AI Integration
- **OpenAI-Compatible API** — Call any vision model (GPT-4o, Claude, etc.) for medical image analysis
- **SSE Progress Streaming** — Real-time progress updates during analysis
- **Structured Findings** — JSON-structured results with region, description, severity, and confidence
- **Custom Prompts** — User-defined analysis prompts for specialized tasks
- **Offline Fallback** — Simulated analysis when no API is configured

### DICOMweb / PACS Connectivity
- **QIDO-RS Query** — Search studies/series/instances on remote PACS
- **WADO-RS Retrieve** — Fetch DICOM objects from PACS
- **STOW-RS Store** — Push DICOM objects to PACS
- **Multi-Server** — Manage multiple PACS connections simultaneously
- **PACS Browser** — Tree-view study/series/instance browsing

### DICOM Anonymization
- **Profile-Based** — Predefined profiles: Research, Clinical Trial, Full De-identification
- **Custom Rules** — Per-tag anonymization rules (remove, hash, replace, offset)
- **Date Shifting** — Configurable date offset for temporal anonymization
- **Preview Mode** — Preview anonymization changes before applying
- **Audit Log** — Track all anonymization operations

### Post-Processing
- **HU-to-RED Conversion** — CT Hounsfield Units to Relative Electron Density with 450+ point calibration table
- **TG-263 Auto-Rename** — Batch rename structures to TG-263 standard naming conventions
- **Dose Summation** — Combine multiple dose distributions into a single volume
- **NRRD Export** — Export CT (HU) and RED volumes as NRRD files for AI/ML pipelines

### Converter & Sequence Analysis
- **DICOM to NIfTI Conversion** — Convert DICOM series to NIfTI format for AI/ML pipelines with real-time SSE progress
- **Intelligent Sequence Analysis** — Automatic classification of DICOM series into ADC, DWI, DCE, MG, US types
- **DCE Phase Detection** — Groups dynamic contrast-enhanced series by temporal position or acquisition time
- **DWI B-value Analysis** — Infers b-value count (single vs dual) from slice geometry
- **Smart Series Selection** — Automatically selects the best series for each type

### Client-Only Mode
- **Offline DICOM Viewer** — Parse and view DICOM files entirely in the browser using `dicom-parser`
- **No Backend Required** — Works without a running backend server
- **Drag & Drop** — Drop DICOM files directly onto the viewer

### PWA & Offline Support
- **Progressive Web App** — Installable on desktop and mobile with manifest.json
- **Service Worker Caching** — Automatic caching of DICOM slice responses using SHA-256 body-hashed cache keys
- **Offline Repeat Access** — Previously viewed slices available offline from cache

### WebWorker Rendering & Parsing
- **OffscreenCanvas Rendering** — Image compositing and window/level in a dedicated WebWorker (non-blocking UI)
- **Background DICOM Parsing** — Batch DICOM metadata extraction offloaded to WebWorker for large uploads
- **Fallback to Main Thread** — Graceful degradation when WebWorker is unavailable

### HTTP/2 Multiplexing
- **HTTP/2 Protocol** — Multiplexed connections for concurrent slice/volume requests without head-of-line blocking
- **Automatic Fallback** — Falls back to HTTP/1.1 if h2 is not available

### Authentication (OIDC)
- **OpenID Connect** — Login via any OIDC provider (Keycloak, Auth0, etc.)
- **JWT Tokens** — Secure token-based session management
- **Route Protection** — Auth guard on all routes except login/callback
- **Configurable** — Enable/disable via environment variables

### Scalability & Memory Management
- **Client-Side Metadata Preview** — DICOM metadata parsed in-browser before upload
- **Binary Slice Transfer** — Slice data transferred as raw bytes (~60% smaller than JSON)
- **Disk-Based Pixel Storage** — Pixel data saved to `.npy` files on disk immediately after upload
- **Resource Limits** — Per-session: 10,000 files, 2 GB max size
- **Session Cleanup** — 15-minute TTL with 2-minute cleanup cycle
- **Streaming Volume Transfer** — Large volumes streamed in 4MB chunks to avoid timeouts
- **Slice Prefetching** — Adjacent slices preloaded in background for smooth navigation
- **Virtual Scrolling** — DICOM tag table renders only visible rows for large tag sets
- **LRU Caching** — Bounded memory caches for volumes, structures, and doses

### Multi-Format Support
| Format | Extension | Reader |
|--------|-----------|--------|
| DICOM | `.dcm` | pydicom |
| NIfTI | `.nii`, `.nii.gz` | nibabel |
| NRRD | `.nrrd`, `.nhdr` | pynrrd |
| MHA/MHD | `.mha`, `.mhd` | SimpleITK |

### Additional
- **Bilingual UI** — English and Simplified Chinese (zh-CN)
- **Dark Mode** — Full dark/light theme support
- **Responsive Layout** — Desktop and mobile-friendly interface
- **Real-time Activity Log** — Track all processing operations with level filtering (Info/Warning/Error/Success)
- **Persistent Settings** — Singleton composable syncs viewer, overlay, sidebar, and export preferences across all views
- **Security Hardened** — SSRF protection, path traversal prevention, rate limiting, secure CORS

## Architecture

```
MedVista/
├── backend/                      # FastAPI + Python
│   ├── app/
│   │   ├── main.py               # App entry, CORS, routers
│   │   ├── routers/
│   │   │   ├── dicom.py          # DICOM upload, slice, structs, dose, plans, volume-binary
│   │   │   ├── auth.py           # OIDC login, JWT, token refresh
│   │   │   ├── dicomweb.py       # PACS connectivity (QIDO/WADO/STOW-RS)
│   │   │   ├── seg.py            # DICOM Segmentation objects
│   │   │   ├── four_d.py         # 4D time-series data
│   │   │   ├── annotations.py    # Measurement/annotation persistence
│   │   │   ├── anonymization.py  # DICOM anonymization profiles
│   │   │   ├── converter.py      # DICOM-to-NIfTI conversion (SSE progress)
│   │   │   ├── analysis.py       # Sequence analysis
│   │   │   ├── export.py         # NRRD volume export
│   │   │   ├── postprocessing.py # HU-RED, dose summation, TG-263
│   │   │   ├── medical_formats.py# NIfTI/NRRD/MHA upload
│   │   │   ├── roi.py            # ROI label map CRUD, draw, export
│   │   │   ├── config.py         # TG-263 config, window presets
│   │   │   └── logging.py        # Activity logging
│   │   ├── services/
│   │   │   ├── dicom_service.py          # Session management, disk storage
│   │   │   ├── auth_service.py           # JWT, OIDC discovery, JWKS
│   │   │   ├── dicomweb_service.py       # DICOMweb HTTP client
│   │   │   ├── seg_service.py            # SEG object parsing
│   │   │   ├── four_d_service.py         # 4D volume building
│   │   │   ├── anonymization_service.py  # Anonymization engine
│   │   │   ├── image_builder.py          # Volume building & slices
│   │   │   ├── rt_struct_builder.py      # RT structure contours
│   │   │   ├── rt_dose_builder.py        # RT dose grids
│   │   │   ├── dicom_converter_service.py# DICOM-to-NIfTI
│   │   │   ├── sequence_analysis_service.py
│   │   │   ├── nifti_service.py          # NIfTI/NRRD/MHA loader
│   │   │   ├── roi_service.py            # ROI label map storage, draw, undo/redo, export
│   │   │   └── log_service.py
│   │   └── middleware/
│   │       └── auth.py           # FastAPI auth dependency
│   ├── config_files/             # TG-263 names, organ matching, presets
│   ├── requirements.txt
│   └── run.py
├── frontend/                     # Vue 3 + TypeScript + Cornerstone3D
│   ├── src/
│   │   ├── views/                # 15 page views
│   │   ├── components/
│   │   │   ├── layout/           # AppLayout, AppSidebar, AppHeader, AuthGuard
│   │   │   ├── viewer/           # Cornerstone3DViewer, MeasurementToolbar/Panel,
│   │   │   │                     # SegmentationPanel, TimeSlider, ViewerHeader,
│   │   │   │                     # ViewerSidebar, ImageSliceViewer (Canvas2D),
│   │   │   │                     # DrawingToolbar, ROIPanel
│   │   │   ├── pacs/             # PacsConnectionDialog, PacsBrowser
│   │   │   └── common/           # DataTable, StatusBadge, etc.
│   │   ├── composables/
│   │   │   ├── useCornerstone3D  # Cornerstone3D engine lifecycle
│   │   │   ├── useTools          # Measurement tool management
│   │   │   ├── useSegmentation   # SEG overlay state
│   │   │   ├── useDicomweb       # PACS connection state
│   │   │   ├── useFourD          # 4D time-series state
│   │   │   ├── useAnonymization  # Anonymization state
│   │   │   ├── useAuth           # OIDC login/token management
│   │   │   ├── useSettings       # Persistent app settings (singleton)
│   │   │   ├── useROIDrawing     # ROI drawing state, operations, AI segmentation
│   │   │   ├── useROIDrawInput   # Mouse/touch input handling for draw tools
│   │   │   └── useClientMode     # Backend availability detection
│   │   ├── utils/
│   │   │   ├── cornerstoneVolumeLoader.ts  # Custom volume loader
│   │   │   ├── clientDicomLoader.ts        # Client-side DICOM parser
│   │   │   ├── dicomClientParser.ts        # Client-side DICOM parsing (WebWorker)
│   │   │   └── webglDetector.ts            # GPU capability detection
│   │   ├── workers/
│   │   │   ├── render.worker.ts            # OffscreenCanvas rendering
│   │   │   └── dicom-parse.worker.ts       # Background DICOM parsing
│   │   ├── stores/               # Pinia state management
│   │   ├── i18n/                 # English + Chinese translations
│   │   ├── router/               # Vue Router with auth guard
│   │   └── types/                # TypeScript interfaces
│   ├── tailwind.config.js
│   └── vite.config.ts
└── docs/                         # Competitor analysis
```

## Documentation

| Guide | Description |
|-------|-------------|
| [Getting Started](docs/user-guide/getting-started.md) | Installation, setup, first launch |
| [3D Viewer](docs/user-guide/viewer.md) | Viewer tools, fusion, AI analysis, 4D |
| [Converter](docs/user-guide/converter.md) | DICOM to NIfTI/NRRD conversion |
| [Anonymization](docs/user-guide/anonymization.md) | DICOM anonymization profiles and custom rules |
| [API Reference](docs/api/README.md) | Full REST API documentation |
| [Architecture](docs/dev/architecture.md) | System design and data flow |
| [Development Setup](docs/dev/setup.md) | Local development environment |
| [Contributing](docs/dev/contributing.md) | Code standards, PR workflow |

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+ / pnpm

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Start server (multi-worker)
python run.py
```

Backend runs at `http://localhost:8000`

### Frontend

```bash
cd frontend

# Install dependencies
pnpm install

# Development
pnpm dev

# Production build
pnpm build
node server.cjs
```

Frontend runs at `http://localhost:3000` (production proxy)

### Authentication (Optional)

```bash
# Set these environment variables to enable OIDC authentication
export OIDC_ISSUER=https://your-oidc-provider.com
export JWT_SECRET=your-strong-random-secret
export CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/dicom/upload` | Upload DICOM files |
| POST | `/api/dicom/volume-binary` | Get raw 3D volume (for Cornerstone3D) |
| POST | `/api/dicom/slice` | Get image slice (JSON) |
| POST | `/api/dicom/slice-binary` | Get image slice (binary, ~60% smaller) |
| DELETE | `/api/dicom/session/{session_id}` | Explicit session cleanup |
| GET | `/api/dicom/patients/{session}` | List patients |
| GET | `/api/dicom/structs/{session}/{patient}` | List RT structures |
| GET | `/api/dicom/dose/{session}/{patient}/{uid}/{slice}` | Get dose slice |
| GET | `/api/dicom/plans/{session}/{patient}` | Get RT plans |
| POST | `/api/seg/mask` | Get SEG binary mask |
| POST | `/api/seg/volume` | Get SEG volume data |
| GET | `/api/4d/info` | Get 4D sequence info |
| POST | `/api/4d/volume` | Get 4D volume for time point |
| POST | `/api/dicomweb/connect` | Connect to PACS server |
| GET | `/api/dicomweb/studies` | Search studies on PACS |
| GET | `/api/dicomweb/studies/{uid}/retrieve` | Retrieve study from PACS |
| POST | `/api/annotations/save` | Save annotations |
| GET | `/api/annotations/{session}` | Load annotations |
| POST | `/api/anonymization/apply` | Apply anonymization |
| GET | `/api/anonymization/profiles` | List anonymization profiles |
| POST | `/api/converter/scan` | Scan patient series |
| POST | `/api/converter/convert-stream` | Convert DICOM to NIfTI (SSE) |
| POST | `/api/analysis/analyze` | Analyze DICOM sequences |
| POST | `/api/postprocessing/convert-hu` | HU to RED conversion |
| POST | `/api/postprocessing/sum-doses` | Sum dose distributions |
| POST | `/api/roi/create` | Create empty label map |
| GET | `/api/roi/list/{session}/{patient}` | List label maps for patient |
| POST | `/api/roi/paint` | Paint stroke on label map |
| POST | `/api/roi/shape` | Fill shape on label map |
| POST | `/api/roi/magic-wand` | Magic wand flood fill |
| POST | `/api/roi/slice-mask` | Get mask for a single label on a slice |
| POST | `/api/roi/slice-all` | Get all label masks on a slice |
| POST | `/api/roi/erode` | Erode label |
| POST | `/api/roi/dilate` | Dilate label |
| POST | `/api/roi/smooth` | Gaussian smooth label |
| POST | `/api/roi/undo` | Undo last operation |
| POST | `/api/roi/redo` | Redo last undone operation |
| POST | `/api/roi/export/nifti` | Export label map as NIfTI |
| POST | `/api/roi/export/dicom-seg` | Export label map as DICOM SEG |
| POST | `/api/ai/segment/auto` | AI auto-segmentation |
| POST | `/api/ai/segment/text` | Text-guided segmentation |
| POST | `/api/ai/segment/reference` | Reference-guided segmentation |
| GET | `/api/export/nrrd/{session}/{patient}/{series}` | Export NRRD volume |
| POST | `/api/auth/login` | Login (OIDC or local) |
| GET | `/api/auth/me` | Get current user |
| POST | `/api/auth/refresh` | Refresh JWT token |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/auth/config` | Auth config (enabled/disabled) |
| GET | `/api/system/info` | System info (version, Python, OS, uptime) |

## Configuration

Configuration files are in `backend/config_files/`:

| File | Purpose |
|------|---------|
| `tg263_names.json` | TG-263 structure name mappings |
| `organ_matching.json` | Organ name matching rules |
| `window_presets.json` | Window/Level presets |
| `ct_HU_map_vals.json` | HU calibration values |
| `ct_RED_map_vals.json` | RED calibration values |
| `disease_sites.json` | Treatment site definitions |

## Tech Stack

- **Frontend**: Vue 3, TypeScript, Pinia, Vue Router, Vue I18n, Tailwind CSS, Vite, Cornerstone3D
- **Backend**: Python, FastAPI, Uvicorn, pydicom, nibabel, SimpleITK, pynrrd, NumPy, Pillow, httpx
- **Design**: Glass morphism UI with mesh gradient backgrounds

## License

MIT
