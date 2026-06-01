# Changelog

All notable changes to MedVista will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [2.1.0] - 2026-06-01

### Added — AI-Powered ROI Drawing (ITK-SNAP Style)
- Full-featured ROI drawing toolbar: paintbrush, polygon, rectangle, ellipse, magic wand (flood fill), eraser
- Multi-label support with custom name and color per label
- Real-time mask overlay rendering on all three MPR planes (axial, sagittal, coronal)
- Cross-plane mask synchronization — draw on one plane, see on all
- Undo/redo with zlib-compressed snapshots (30 levels deep)

### Added — Morphological Post-Processing
- Erode, dilate, and Gaussian smooth operations on individual labels
- Clear label and clear all functionality

### Added — AI Segmentation
- Auto-segmentation: AI locates pathology via vision API, then generates pixel-level masks via classic image processing (Otsu thresholding + morphological ops)
- Text-guided segmentation: describe target region in natural language (e.g. "liver tumor"), AI uses HU ranges and organ matching to segment
- Reference-guided segmentation: provide a reference label, AI extracts intensity statistics and generates matching masks
- SSE progress streaming for real-time segmentation feedback

### Added — ROI Export
- NIfTI label map export (.nii.gz) with per-label metadata
- DICOM SEG export for clinical PACS integration
- NIfTI label map import for loading previously exported ROIs

### Added — ROI Settings
- Default brush radius, draw overlay opacity, auto-save toggle, export format preference
- All settings persist across sessions via singleton composable

### Added — Bilingual ROI UI
- Complete English + Simplified Chinese translations for all ROI features
- DrawingToolbar, ROIPanel, and ViewerSidebar draw mode integration

### Improved
- ImageSliceViewer supports dual rendering modes (WebGL + Canvas2D fallback) for ROI overlays
- Cornerstone3D viewers use transparent overlay canvas for draw event capture and brush cursor

## [2.0.0] - 2026-06-01

### Added — AI Integration
- AI-powered medical image analysis with OpenAI-compatible API (GPT-4o, Claude, etc.)
- Multi-slice analysis: single slice, 5-slice grid, and MIP projection modes
- AI-assisted TG-263 fuzzy structure rename (LLM-powered name matching)
- AI-suggested window width/level based on modality and anatomy
- AI burned-in annotation detection for anonymization compliance
- AI DICOM tag compliance review with risk assessment
- AI study summary generation from structured findings
- AI connectivity check and model list in Settings

### Added — PET-CT Fusion
- Dual-volume PET-CT overlay using Cornerstone3D multi-volume rendering
- Blend ratio controls (0-100%) with additive/default modes
- SUV (Standardized Uptake Value) calculation from DICOM metadata
- Auto-detection of CT/PET series pairs within the same study

### Added — DICOM Worklist (MWL)
- DICOM Modality Worklist query and display
- Remote MWL server connection management
- MWL query with patient name, ID, and date range filters

### Added — DICOM Structured Reports (SR)
- SR document creation from AI analysis findings
- SR document listing and viewing per study
- One-click "Generate SR Report" from AI panel

### Added — DICOM Print
- DICOM print service with printer management
- Print job submission and status tracking
- Configurable film size, orientation, and density

### Added — Enhanced Anonymization
- Profile-based anonymization (Research, Clinical Trial, Full De-identification)
- Custom per-tag rules (remove, hash, replace, offset)
- Date shifting with configurable offset
- Preview mode before applying changes
- Audit log for all anonymization operations
- Compliance validation against profiles

### Added — Post-Processing
- HU-to-RED conversion with 450+ point calibration table
- TG-263 auto-rename for structure naming standards
- Dose summation for combining multiple dose distributions
- NRRD export for CT (HU) and RED volumes

### Added — Sequence Analysis
- Automatic DICOM series classification (ADC, DWI, DCE, MG, US)
- DCE phase detection by temporal position or acquisition time
- DWI b-value analysis from slice geometry
- Smart series selection for optimal data

### Added — Developer Experience
- Backend AI service with configurable API endpoint and key
- SSE progress streaming for DICOM-to-NIfTI conversion
- Persistent settings singleton composable
- Settings changelog display with version history
- System info endpoint (version, Python, OS, uptime)

### Improved
- Memory management: disk-based pixel storage, session size limits, LRU caches
- Security: SSRF protection, path traversal prevention, rate limiting, API key masking
- Performance: Cornerstone3D code splitting, lazy-loaded imports, virtual scrolling
- Offline support: Service Worker SHA-256 body-hashed cache keys
- WebWorker: OffscreenCanvas rendering, background DICOM parsing
- HTTP/2 multiplexing with automatic fallback
- Bilingual UI (English + Simplified Chinese)

### Fixed
- Path traversal in session_id validation
- Cache key cross-session pollution
- Window 0 treated as null in viewer settings
- Negative slice index handling
- SSE hang on conversion completion
- Cornerstone3D code-splitting memory leak
- useAI, useFourD, useClientMode memory leaks
- ImageSliceViewer watcher over-triggering
- Service Worker POST caching vulnerability
- Auth guard race condition on initial render
- SR session index bug preventing AI-generated reports
- API key exposed in GET /config response
- Error message leakage in API responses
- Fragile JSON parsing in AI endpoints

## [1.1.0] - 2026-05-30

### Added
- Settings optimization: contour thickness, default tool, 4D FPS, segment opacity, recent patients count
- Changelog feature with version history display in Settings

### Fixed
- Viewer ignoring default window/level setting from preferences
- Segment overlay opacity not reading from settings
- 4D playback FPS not reading from settings

## [1.0.0] - 2026-05-15

### Added
- Initial release
- WebGL 3D viewer with Cornerstone3D
- RT structure and dose overlays
- DICOMweb / PACS connectivity
- DICOM anonymization with profile-based rules
- Multi-format support (DICOM, NIfTI, NRRD, MHA)
- 4D dynamic sequence support
- DICOM segmentation (SEG) overlay
- Measurement and annotation tools
- Client-side DICOM parsing mode
- PWA and offline support
- WebWorker rendering and parsing
- HTTP/2 multiplexing
- OIDC authentication
- Bilingual UI (English + Chinese)
