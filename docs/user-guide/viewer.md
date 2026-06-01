# 3D Viewer Guide

The MedVista viewer is built on Cornerstone3D, providing GPU-accelerated volume rendering with multi-planar reconstruction (MPR).

## Viewer Layout

```
┌──────────────┬──────────────────────────────────┐
│              │                                  │
│   Sidebar    │         Viewport Area            │
│              │                                  │
│  - Series    │    ┌──────────┬──────────┐       │
│  - Controls  │    │  Axial   │ Sagittal │       │
│  - AI Panel  │    ├──────────┼──────────┤       │
│  - Fusion    │    │ Coronal  │  3D View │       │
│              │    └──────────┴──────────┘       │
│              │                                  │
└──────────────┴──────────────────────────────────┘
```

## Navigation

- **Scroll** — Navigate through slices in the current viewport
- **Left-click + drag** — Pan the image
- **Right-click + drag** — Zoom in/out
- **Middle-click + drag** — Rotate (in 3D viewport)

## Measurement Tools

Select a tool from the toolbar, then click on the viewport to use it.

### Length Tool
Click two points to measure distance in mm. A measurement label displays the distance.

### Angle Tool
Click three points (vertex first) to measure an angle in degrees.

### ROI Statistics
Draw a rectangle or ellipse over a region to see mean, standard deviation, min, and max HU values.

### Probe Tool
Click a single point to read the voxel value (HU for CT, intensity for MR).

### Arrow Annotation
Click to place an arrow with a text label.

## Window/Level Presets

Presets are available in the sidebar. Click a preset to apply it:

| Preset | Center | Width | Use Case |
|--------|--------|-------|----------|
| Default | 40 | 400 | General soft tissue |
| CT | 40 | 400 | Abdominal CT |
| Lung | -600 | 1500 | Lung imaging |
| Bone | 400 | 1800 | Bone/soft tissue |
| Brain | 40 | 80 | Brain CT |
| Subdural | 75 | 215 | Subdural hematoma |
| PET | 2.5 | 15 | PET SUV display |

You can also manually adjust center/width with the slider controls.

## RT Structure Overlays

When an RT Structure Set is loaded:

1. The **Structures** panel appears in the sidebar
2. Click a structure name to toggle its visibility
3. Adjust opacity with the slider
4. Click **"Center on ROI"** to navigate to the structure's center across all planes

Structure types are auto-classified using TG-263 conventions (Target, OAR, External, etc.).

## PET-CT Fusion

For PET-CT data (CT + PET in the same study):

1. The sidebar automatically detects PET series
2. Enable **Fusion** with the toggle
3. Use the **Blend Slider** to control PET opacity (0-100%)
4. Toggle **Blend Mode** between Additive and Default
5. Enable **Show SUV** for standardized uptake value display

The PET volume is overlaid on the CT volume in the viewport, with configurable opacity.

## 4D Dynamic Sequences

For time-series data (4D-CT, cardiac MRI):

1. The **Time Slider** appears at the bottom of the sidebar
2. Use **Play/Pause** to animate through time points
3. Adjust **Frame Rate** with the slider
4. Step forward/backward with the arrow buttons

## DICOM Tag Inspector

Click **"DICOM Tags"** in the sidebar to browse all DICOM metadata:

- Search tags by keyword or tag number
- Filter by group
- View tag values, VR (Value Representation), and length

## AI Analysis

If AI is configured (see [Getting Started](./getting-started.md)):

1. Select a model from the **AI Analysis** panel
2. Optionally enter a custom prompt describing what to analyze
3. Click **"Run Analysis"**
4. Watch the progress bar as the analysis runs
5. View findings with severity, confidence, and region descriptions

Findings are color-coded by severity:
- **Severe** — Red
- **Moderate** — Yellow
- **Mild** — Blue
- **Normal** — Green

## DICOM Segmentation (SEG) Support

When DICOM SEG objects are loaded:

1. The **Segmentation** panel appears in the sidebar
2. Each segment is listed with its name and color
3. Toggle visibility per segment
4. Adjust opacity per segment
5. Segmentation masks are overlaid on the volume

## Export and Data

- **Export Measurements** — CSV export of all measurement annotations
- **Export to DICOM** — Convert processed data back to DICOM format
- **Export to NIfTI** — Convert DICOM series to NIfTI format
