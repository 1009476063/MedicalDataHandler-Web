# MedVista API Reference

Base URL: `http://localhost:8000`

Interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Authentication

MedVista uses JWT-based authentication. Include the token in the `Authorization` header:

```
Authorization: Bearer <token>
```

Obtain a token via:

```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "your-password"
}
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

## API Endpoints

### DICOM Upload & Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/dicom/upload` | Upload DICOM files |
| `GET` | `/api/dicom/patients` | List all patients |
| `GET` | `/api/dicom/studies` | List studies for a patient |
| `GET` | `/api/dicom/series` | List series for a study |
| `GET` | `/api/dicom/instances` | List instances for a series |
| `GET` | `/api/dicom/tags/{instance_uid}` | Get DICOM tags for an instance |
| `GET` | `/api/dicom/suv-info` | Get SUV parameters for PET series |
| `GET` | `/api/dicom/find-pt-series` | Find CT/PET series pairs in a study |

### Volume Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/dicom/volume-binary` | Get volume data as binary (uint8) |
| `POST` | `/api/dicom/slice-binary` | Get a single slice as binary |
| `GET` | `/api/dicom/volume-meta` | Get volume metadata (dimensions, spacing) |

### Measurements & Annotations

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/annotations/save` | Save measurements/annotations |
| `GET` | `/api/annotations/load` | Load annotations for a series |
| `DELETE` | `/api/annotations/{id}` | Delete an annotation |

### AI Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/ai/models` | List available AI models |
| `POST` | `/api/ai/analyze` | Start AI analysis job |
| `GET` | `/api/ai/jobs/{job_id}` | Get job status |
| `GET` | `/api/ai/jobs/{job_id}/stream` | SSE progress stream |
| `GET` | `/api/ai/results/{job_id}` | Get analysis results |

### Converter

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/converter/convert` | Convert medical image format |
| `GET` | `/api/converter/progress/{job_id}` | SSE conversion progress |

### Anonymization

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/anonymization/anonymize` | Anonymize DICOM files |
| `POST` | `/api/anonymization/de-anonymize` | De-anonymize files (requires key) |

### DICOM Segmentation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/seg/segments` | List segments for a series |
| `GET` | `/api/seg/mask/{segment_id}` | Get segmentation mask |

### RT Structures & Dose

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/dicom/structures` | Get RT structures for a study |
| `GET` | `/api/dicom/dose` | Get dose data |
| `POST` | `/api/dicom/dose-sum` | Sum multiple dose distributions |

### 4D Sequences

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/four-d/frames` | List temporal frames |
| `GET` | `/api/four-d/frame/{index}` | Get a specific frame |

### DICOMweb

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/dicomweb/connect` | Connect to a DICOMweb server |
| `GET` | `/api/dicomweb/studies` | QIDO-RS query |
| `GET` | `/api/dicomweb/series` | Query series |

### Export

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/export/dicom` | Export as DICOM |
| `POST` | `/api/export/nifti` | Export as NIfTI |
| `POST` | `/api/export/nrrd` | Export as NRRD |
| `POST` | `/api/export/csv` | Export measurements as CSV |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/system/info` | System information |
| `GET` | `/api/system/gpu` | GPU detection |

### Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | Login and get JWT token |
| `POST` | `/api/auth/refresh` | Refresh JWT token |
| `GET` | `/api/auth/me` | Get current user info |

## Response Format

All API responses follow a consistent envelope:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": {
    "total": 100,
    "page": 1,
    "limit": 20
  }
}
```

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad request / validation error |
| 401 | Unauthorized (missing or invalid token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Resource not found |
| 413 | Request entity too large |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

## Rate Limiting

API endpoints are rate-limited to prevent abuse. Default limits:
- Upload endpoints: 10 requests/minute
- Read endpoints: 100 requests/minute
- AI endpoints: 5 requests/minute

## File Upload

Upload endpoints accept multipart form data:

```bash
curl -X POST http://localhost:8000/api/dicom/upload \
  -F "files=@scan1.dcm" \
  -F "files=@scan2.dcm"
```

Maximum file size: 500 MB per file.
Maximum total upload: 2 GB per request.

## Server-Sent Events (SSE)

Progress endpoints use SSE for real-time updates:

```
GET /api/ai/jobs/{job_id}/stream
Accept: text/event-stream
```

Event format:
```
data: {"progress": 0.5, "message": "Processing slice 100/200"}

data: {"done": true, "message": "Analysis complete"}
```

## WebSocket

Not currently used. All streaming uses SSE.
