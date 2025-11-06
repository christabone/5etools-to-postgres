# Documentation Structure

This document outlines the organization of documentation for the 5etools-to-postgres project.

## Organization Summary

### Root Level (Essential User-Facing Docs)
- **README.md** - Project overview and getting started
- **QUICKSTART.md** - Quick start guide for users
- **TESTING.md** - Testing procedures and test suite documentation

### docs/architecture/
Design documents and high-level system architecture planning.

| File | Description |
|------|-------------|
| PLAN.md | Overall project plan and strategy |
| FLOW.md | System flow and data flow diagrams |
| INDEX_PLAN.md | Database indexing strategy and plan |
| IMPORT_PLAN.md | Data import process and methodology |

### docs/development/
Build process, development progress, and phase reviews. Primarily internal development tracking.

| File | Description |
|------|-------------|
| PHASE_2_PROGRESS.md | Development progress tracking for Phase 2 |
| PHASE_2.1_REVIEW.md | Review findings from Phase 2.1 |
| PHASE_2.2_REVIEW.md | Review findings from Phase 2.2 |

### docs/reference/
Reference materials for data structures, formats, and special considerations.

| File | Description |
|------|-------------|
| CONTROLLED_VOCABULARY.md | Controlled vocabulary used in the project |
| PIPES_AND_ABBREVIATIONS_REPORT.md | Report on pipes and abbreviations in data |
| SPECIAL_CHARACTERS_REPORT.md | Report on special characters handling |
| REVIEW_FINDINGS.md | General review findings and observations |

## File Categorization

| Original Location | New Location | Reason |
|-------------------|-------------|--------|
| README.md | Root | Essential user-facing documentation |
| QUICKSTART.md | Root | Essential getting started guide |
| TESTING.md | Root | Essential testing documentation |
| PLAN.md | docs/architecture/ | High-level project design document |
| FLOW.md | docs/architecture/ | System architecture and flow design |
| INDEX_PLAN.md | docs/architecture/ | Database design documentation |
| IMPORT_PLAN.md | docs/architecture/ | Data import architecture and design |
| PHASE_2_PROGRESS.md | docs/development/ | Internal development progress tracking |
| PHASE_2.1_REVIEW.md | docs/development/ | Internal development review notes |
| PHASE_2.2_REVIEW.md | docs/development/ | Internal development review notes |
| CONTROLLED_VOCABULARY.md | docs/reference/ | Reference material for data structures |
| PIPES_AND_ABBREVIATIONS_REPORT.md | docs/reference/ | Reference material for data formats |
| SPECIAL_CHARACTERS_REPORT.md | docs/reference/ | Reference material for character handling |
| REVIEW_FINDINGS.md | docs/reference/ | Reference material and analysis results |

## Navigation Structure

When referencing documentation from README or other files, use these paths:

```
project/
├── README.md                          # Start here
├── QUICKSTART.md                      # Quick setup guide
├── TESTING.md                         # Test documentation
└── docs/
    ├── architecture/                  # Design & architecture docs
    │   ├── PLAN.md
    │   ├── FLOW.md
    │   ├── INDEX_PLAN.md
    │   └── IMPORT_PLAN.md
    ├── development/                   # Development progress & reviews
    │   ├── PHASE_2_PROGRESS.md
    │   ├── PHASE_2.1_REVIEW.md
    │   └── PHASE_2.2_REVIEW.md
    └── reference/                     # Reference materials
        ├── CONTROLLED_VOCABULARY.md
        ├── PIPES_AND_ABBREVIATIONS_REPORT.md
        ├── SPECIAL_CHARACTERS_REPORT.md
        └── REVIEW_FINDINGS.md
```

