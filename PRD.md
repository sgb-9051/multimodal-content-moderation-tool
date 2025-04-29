# Product Requirements Document

## 1. Overview
This document outlines the Product Requirements for a desktop application that identifies and quarantines graphic and other Not Safe For Work (NSFW) objectionable images (e.g., gore, extreme violence, offensive language) using a strict, offline, pure‑Python content-moderation detection library. Designed as a hackathon MVP, it focuses on simplicity, cross‑platform compatibility, and minimal dependencies.

## 2. Purpose and Goals
- **Purpose:** Provide end users with a lightweight tool to scan and block images containing graphic or otherwise objectionable content (e.g., gore, extreme violence, offensive language, and other NSFW material) on their machines.
- **Primary Goals:**
  - Enable manual selection and scanning of image files.
  - Strictly detect and quarantine images classified as objectionable by violence, gore, or offensive text criteria.
  - Deliver a working MVP within a 3‑4 hour hackathon window.

## 3. Scope
- **In Scope (MVP):**
  - Image formats: JPEG, PNG, GIF.
  - Manual “Browse & Scan” workflow.
  - NSFW detection via a pure‑Python model for gore/violence scores and OCR‑based text analysis for offensive language.
  - Move flagged files to a local `quarantine/` folder.
  - Display per‑file results (Safe / Flagged) in a simple GUI.
- **Out of Scope (Nice‑to‑Have):**
  - Video or audio scanning.
  - Automatic directory watching or live monitoring.
  - External alerting or agency API integration.
  - Encrypted database or detailed logging.

## 4. User Stories
- **As a user**, I want to select one or more image files so I can scan them for graphic violence or offensive language.
- **As a user**, I want to see clear feedback (Safe / Flagged) for each file scanned.
- **As a user**, I want flagged files moved to a quarantine folder so they are no longer accessible in their original location.

## 5. Functional Requirements
| ID   | Description                                                                                                            | Priority |
|------|------------------------------------------------------------------------------------------------------------------------|----------|
| FR1  | File selection dialog for JPEG/PNG/GIF files.                                                                          | Must     |
| FR2  | Run content classification using offline Python models for graphic violence, offensive language (via OCR), and general Not Safe For Work (NSFW) content. | Must     |
| FR3  | Apply strict thresholds (gore_score ≥ 0.8 OR any offensive_text matches) to determine flagged content.                   | Must     |
| FR4  | Move flagged images to `./quarantine/` directory.                                                                      | Must     |
| FR5  | Display filename and status (Safe/Flagged) in the UI log area.                                                         | Must     |
| FR6  | Show a spinner or progress indicator during scanning.                                                                  | Should   |

## 6. Non‑Functional Requirements
- **Performance:** Process at least 5 images per second on typical hardware (for gore detection only).
- **Dependencies:** Only pure‑Python packages that install cleanly on Windows.
- **Usability:** Simple, uncluttered interface built with PySimpleGUI.
- **Platform:** Windows, macOS, Linux (via Python).

## 7. UX/UI Design
- **Main Window Layout:**
  1. **File List Panel:** Lists selected file paths.
  2. **Controls:** “Browse…” button and “Scan All” button.
  3. **Log Area:** Multiline text showing per‑file scan results.
  4. **Progress Indicator:** Spinner or progress bar during scan.

## 8. System Architecture
```
┌─────────────────────────┐
│   Desktop App (Python)  │
│ ┌─────────────────────┐ │
│ │    PySimpleGUI UI   │ │
│ └─────────────────────┘ │
│           ↓             │
│ ┌─────────────────────┐ │
│ │  Gore Detector Model│ │
│ ├─────────────────────┤ │
│ │  OCR Text Analyzer  │ │
│ └─────────────────────┘ │
│           ↓             │
│ ┌─────────────────────┐ │
│ │ Quarantine Handler  │ │
│ └─────────────────────┘ │
└─────────────────────────┘
```

## 9. Technology Stack & Dependencies
- **UI Framework:** PySimpleGUI (`pip install PySimpleGUI`)
- **Gore Detection:** `gore_detector` (hypothetical pure‑Python library)
- **OCR Text Analysis:** `pytesseract` (`pip install pytesseract`) + `Pillow`
- **Built‑ins:** `shutil`, `pathlib`, `logging`

## 10. Implementation Roadmap
| Step                | Duration  | Deliverable                                     |
|---------------------|-----------|-------------------------------------------------|
| 1. Setup            | 10 min    | Virtualenv + requirements.txt                   |
| 2. UI Scaffold      | 20 min    | Browse & Scan buttons + file list               |
| 3. Model Integration| 30 min    | Load gore model, OCR, classify selected images  |
| 4. Quarantine Logic | 15 min    | Move flagged files + update UI log              |
| 5. Polish & Test    | 1 hr      | Progress indicator, error handling, small tweaks|
| 6. Packaging        | 45 min    | Single‑file script or PyInstaller bundle        |

## 11. Risks & Mitigations
- **Model Download Delay:** Provide local sample model or stub for hackathon.  
- **False Positives:** Thresholds may misclassify; keep adjustable for future.  
- **Dependency Conflicts:** Test in clean Windows environment.

## 12. Future Enhancements
- Implement video/audio scanning support.
- Integrate real‑time alerting to a nodal agency.
- Encrypt logs and support detailed audit trails.
- Provide automatic model updates via GitHub or custom server.

---
*End of PRD*