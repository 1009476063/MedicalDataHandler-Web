# Getting Started

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** and **pnpm**
- **DICOM data** — any of: DICOM, NIfTI (.nii/.nii.gz), NRRD (.nrrd), or MHA (.mha)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/MedVista.git
cd MedVista
```

### 2. Start the Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API is now running at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### 3. Start the Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

The viewer is now running at `http://localhost:5173`.

## Loading Data

### Via the Web UI

1. Click **"Upload DICOM Files"** on the dashboard
2. Select one or more DICOM files from your system
3. The viewer will automatically parse the DICOM hierarchy (Patient → Study → Series)
4. Click a series to open it in the 3D viewer

### Via the API

```bash
# Upload DICOM files
curl -X POST http://localhost:8000/api/dicom/upload \
  -F "files=@scan1.dcm" \
  -F "files=@scan2.dcm"
```

### Supported Formats

| Format | Extensions | Notes |
|--------|-----------|-------|
| DICOM | `.dcm`, `.ima` | Primary format. Supports CT, MR, PT, RT, SEG, RTSTRUCT, RTDOSE |
| NIfTI | `.nii`, `.nii.gz` | Auto-detected from DICOM context or direct upload |
| NRRD | `.nrrd`, `.nhdr` | NRRD format with optional gzip compression |
| MHA | `.mha`, `.mhd` | MetaImage format |

## Configuration

### Environment Variables (Backend)

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_API_BASE` | — | OpenAI-compatible API base URL |
| `AI_API_KEY` | — | API key for AI analysis |
| `AI_DEFAULT_MODEL` | `gpt-4o` | Default model for AI analysis |
| `AI_BACKEND` | `openai` | AI backend: `openai`, `monai`, or `onnx` |
| `MONAI_LABEL_URL` | `http://localhost:8000` | MONAI Label server URL (if using MONAI) |
| `ONNX_MODEL_DIR` | `./models` | Directory containing ONNX models (if using ONNX) |

### Frontend Configuration

Set the API base URL in `frontend/.env`:

```
VITE_API_BASE_URL=http://localhost:8000
```

## First Launch Checklist

1. Upload a DICOM dataset
2. Verify 3D volume rendering works (MPR view)
3. Test measurement tools (Length, Angle, ROI)
4. Try window/level presets (CT, Lung, Bone)
5. Load an RT structure set and toggle overlays
6. If you have PET data, test PET-CT fusion
7. Run AI analysis (requires API key configuration)
