# DICOM Converter

MedVista includes a DICOM-to-NIfTI converter for preparing medical imaging data for downstream processing.

## Supported Conversions

| Input Format | Output Format | Extensions |
|-------------|---------------|-----------|
| DICOM | NIfTI | `.dcm` → `.nii.gz` |
| DICOM | NRRD | `.dcm` → `.nrrd` |
| NIfTI | DICOM | `.nii`/`.nii.gz` → `.dcm` |
| NRRD | DICOM | `.nrrd` → `.dcm` |

## Using the Converter

### Via the Web UI

1. Navigate to the **Converter** page from the sidebar
2. Upload DICOM files or select from existing sessions
3. Choose output format (NIfTI or NRRD)
4. Configure options:
   - **Resample** — Resample to isotropic voxel spacing
   - **Interpolation** — Nearest neighbor, linear, or cubic
   - **Window/Level** — Apply windowing before conversion
5. Click **"Convert"**
6. Download the converted file

### Via the API

```bash
# Convert DICOM to NIfTI
curl -X POST http://localhost:8000/api/converter/convert \
  -F "files=@scan1.dcm" \
  -F "files=@scan2.dcm" \
  -F "format=nifti" \
  -F "resample=true"
```

## Conversion Options

| Option | Default | Description |
|--------|---------|-------------|
| `format` | `nifti` | Output format: `nifti` or `nrrd` |
| `resample` | `false` | Resample to isotropic voxel spacing |
| `interpolation` | `linear` | Interpolation method for resampling |
| `dtype` | `float32` | Output data type |

## Batch Conversion

For large datasets, use the batch conversion API:

```bash
curl -X POST http://localhost:8000/api/converter/batch \
  -F "files=@series1/*.dcm" \
  -F "format=nifti"
```

## Resampling

When `resample=true`, the converter will:

1. Compute the target voxel spacing as the minimum of the original spacing
2. Use the specified interpolation method to resample
3. Update the affine matrix to reflect the new spacing

This is useful when:
- Voxel spacing is highly anisotropic (e.g., 5mm slice thickness with 0.5mm in-plane)
- Downstream tools require isotropic voxels
- You need consistent voxel sizes across datasets

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No DICOM files found" | Ensure files have valid DICOM headers |
| "Inconsistent slice spacing" | Some series may have mixed spacing; try resampling |
| "File too large" | For large datasets, use batch conversion or split the series |
