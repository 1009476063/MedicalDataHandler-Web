# MedicalDataHandler Web

A web-based medical image viewer and processing platform for radiation therapy. Supports DICOM, NIfTI, NRRD, and MHA formats with multi-planar reconstruction, structure/dose overlays, and RT plan analysis.

![Vue 3](https://img.shields.io/badge/Vue-3-42b883?logo=vue.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.10+-3776ab?logo=python)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178c6?logo=typescript)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-06b6d4?logo=tailwindcss)

## Features

### Image Viewer
- **Multi-Planar Reconstruction (MPR)** — Axial, Sagittal, Coronal views with synchronized navigation
- **Synchronized Crosshairs** — Cross-plane localization for precise navigation
- **Window/Level Presets** — CT, Lung, Bone, Soft Tissue, Brain, Subdural presets
- **Voxel Inspection** — Real-time HU/value readout at cursor position
- **DICOM Tag Inspector** — Searchable tag viewer with filtering
- **Image Controls** — Rotation, flip, zoom/pan speed, orientation labels

### Structure & Dose Overlays
- **RT Structure Overlays** — Color-coded contour rendering with configurable opacity and thickness
- **ROI Centering** — One-click navigation to center of any structure across all planes
- **TG-263 Type Inference** — Automatic structure type classification (Target, OAR, External, etc.)
- **Dose Overlays** — Color-mapped dose distribution visualization
- **Dose Summation** — Combine multiple dose distributions into a single volume

### RT Plans
- **Plan Viewer** — Beam summary with energy, gantry angle, and weight
- **Fractionation Display** — Number of fractions, dose per fraction, total dose

### Post-Processing
- **HU-to-RED Conversion** — CT Hounsfield Units to Relative Electron Density with 450+ point calibration table
- **TG-263 Auto-Rename** — Batch rename structures to TG-263 standard naming conventions
- **Dose Summation** — Combine multiple dose distributions into a single volume
- **NRRD Export** — Export CT (HU) and RED volumes as NRRD files for AI/ML pipelines

### Converter & Sequence Analysis
- **DICOM to NIfTI Conversion** — Convert DICOM series to NIfTI format for AI/ML pipelines with real-time SSE progress
- **Intelligent Sequence Analysis** — Automatic classification of DICOM series into ADC, DWI, DCE, MG, US types using advanced DICOM tags (DiffusionBValue, TemporalPositionIdentifier, ContrastBolusAgent, ImageType, etc.)
- **DCE Phase Detection** — Groups dynamic contrast-enhanced series by temporal position or acquisition time
- **DWI B-value Analysis** — Infers b-value count (single vs dual) from slice geometry
- **Smart Series Selection** — Automatically selects the best series for each type based on file count, geometry matching, and clinical rules
- **DICOM Anonymization** — Remove patient PHI (Personally Identifiable Information) from DICOM files

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
- **Real-time Activity Log** — Track all processing operations
- **Configurable Settings** — Window presets, overlay defaults, interaction speeds

## Architecture

```
MedicalDataHandler-Web/
├── backend/                  # FastAPI + Python
│   ├── app/
│   │   ├── main.py          # App entry, CORS, routers
│   │   ├── routers/         # API endpoints
│   │   │   ├── dicom.py     # DICOM upload, slice, structs, dose, plans, ROI bounds
│   │   │   ├── converter.py # DICOM-to-NIfTI conversion (scan, convert-stream, anonymize, download)
│   │   │   ├── analysis.py  # Sequence analysis (ADC/DWI/DCE/MG/US classification)
│   │   │   ├── export.py    # NRRD volume export
│   │   │   ├── postprocessing.py  # HU-RED, dose summation, TG-263 rename
│   │   │   ├── medical_formats.py # NIfTI/NRRD/MHA upload
│   │   │   ├── config.py    # TG-263 config, window presets
│   │   │   └── logging.py   # Activity logging
│   │   ├── services/        # Business logic
│   │   │   ├── dicom_service.py    # DICOM session management
│   │   │   ├── dicom_converter_service.py # DICOM-to-NIfTI conversion logic
│   │   │   ├── sequence_analysis_service.py # Intelligent sequence classification & selection
│   │   │   ├── image_builder.py    # Volume building & slice extraction
│   │   │   ├── rt_struct_builder.py # RT structure contour processing
│   │   │   ├── rt_dose_builder.py  # RT dose grid processing
│   │   │   ├── nifti_service.py    # NIfTI/NRRD/MHA loader
│   │   │   └── log_service.py      # Activity log
│   │   └── utils/
│   ├── config_files/        # TG-263 names, organ matching, window presets
│   ├── requirements.txt
│   └── run.py               # Uvicorn launcher
├── frontend/                 # Vue 3 + TypeScript
│   ├── src/
│   │   ├── views/           # 9 page views
│   │   ├── components/      # Reusable components
│   │   │   ├── layout/      # AppLayout, AppSidebar, AppHeader
│   │   │   ├── viewer/      # ImageSliceViewer (canvas-based)
│   │   │   └── common/      # DataTable, StatusBadge, SequenceCard, etc.
│   │   ├── stores/          # Pinia state management
│   │   ├── i18n/            # English + Chinese translations
│   │   ├── router/          # Vue Router with lazy loading
│   │   └── types/           # TypeScript interfaces
│   ├── server.cjs           # Production proxy (serves build + proxies API)
│   ├── tailwind.config.js
│   └── vite.config.ts
└── test-data/               # Sample DICOM files for testing
```

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

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/dicom/upload` | Upload DICOM files |
| POST | `/api/upload/medical` | Upload NIfTI/NRRD/MHA files |
| GET | `/api/dicom/patients/{session}` | List patients |
| POST | `/api/dicom/slice` | Get image slice |
| GET | `/api/dicom/structs/{session}/{patient}` | List RT structures |
| GET | `/api/dicom/struct-mask/{session}/{patient}/{key}/{slice}` | Get structure mask |
| GET | `/api/dicom/roi-bounds/{session}/{patient}/{key}` | Get ROI bounding box |
| GET | `/api/dicom/dose/{session}/{patient}/{uid}/{slice}` | Get dose slice |
| GET | `/api/dicom/plans/{session}/{patient}` | Get RT plans |
| POST | `/api/converter/scan` | Scan patient series for conversion |
| POST | `/api/converter/convert-stream` | Convert DICOM to NIfTI (SSE progress) |
| POST | `/api/converter/anonymize` | Anonymize DICOM files |
| GET | `/api/converter/download/{session}/{filename}` | Download converted file |
| POST | `/api/analysis/analyze` | Analyze & classify DICOM sequences |
| POST | `/api/postprocessing/convert-hu` | HU to RED conversion |
| POST | `/api/postprocessing/sum-doses` | Sum dose distributions |
| POST | `/api/postprocessing/auto-rename-structs` | TG-263 batch rename |
| GET | `/api/export/nrrd/{session}/{patient}/{series}` | Export NRRD volume |

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

- **Frontend**: Vue 3, TypeScript, Pinia, Vue Router, Vue I18n, Tailwind CSS, Vite
- **Backend**: Python, FastAPI, Uvicorn, pydicom, nibabel, SimpleITK, pynrrd, NumPy, Pillow
- **Design**: Glass morphism UI with mesh gradient backgrounds

## License

MIT
