# 5etools-to-postgres Data Pipeline Flow

## Overview

This document describes the complete data processing pipeline from raw 5etools JSON files to a fully normalized PostgreSQL database.

The pipeline is designed to be **repeatable** and **idempotent** so that when 5etools updates their data, we can re-run the entire pipeline to refresh our database.

---

## Pipeline Architecture

```
┌─────────────────────┐
│  Raw 5etools Data   │  /home/ctabone/dnd_bot/5etools-src-2.15.0/data/
│   (JSON files)      │
└──────────┬──────────┘
           │
           ▼
    ┌──────────────┐
    │   PHASE 0    │  Analysis - Understand the data structure
    │   Analysis   │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │  PHASE 0.5   │  Cleaning - Normalize data types & structures
    │   Cleaning   │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │  PHASE 0.6   │  Extraction - Extract structured data from markup
    │  Extraction  │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │   PHASE 1    │  Schema Design - PostgreSQL database schema
    │    Schema    │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │   PHASE 2    │  Import - Load data into PostgreSQL
    │    Import    │
    └──────┬───────┘
           │
           ▼
┌─────────────────────┐
│ PostgreSQL Database │
│   dnd5e_reference   │
└─────────────────────┘
```

---

## Phase 0: Data Structure Analysis

**Goal:** Understand the raw data before writing any import code.

### Scripts (Run Once for New Data)

1. **`analyze_json_structure.py`**
   - Input: Raw 5etools JSON files
   - Output: `analysis/structure_report.json`
   - Purpose: Identify all fields, types, nested structures

2. **`analyze_field_types.py`**
   - Input: Raw 5etools JSON files
   - Output: `analysis/field_types_report.json`
   - Purpose: Document data type variations and polymorphic fields

3. **`analyze_controlled_vocab.py`**
   - Input: Raw 5etools JSON files
   - Output: `analysis/controlled_vocab.json`
   - Purpose: Extract all enum-like values for lookup tables

4. **`analyze_relationships.py`**
   - Input: Raw 5etools JSON files
   - Output: `analysis/relationships.json`
   - Purpose: Discover foreign key relationships

5. **`sample_records.py`**
   - Input: Raw 5etools JSON files
   - Output: `analysis/samples/*.json`
   - Purpose: Extract representative examples for review

### Status
✅ **COMPLETE** - All analysis scripts have been run

---

## Phase 0.5: Data Cleaning & Normalization

**Goal:** Eliminate polymorphic fields and normalize data structures before import.

### Scripts (Run in Order)

1. **`clean_items.py`**
   - Input: Raw `data/items-base.json`, `data/items.json`
   - Output: `cleaned_data/items.json`
   - Transformations:
     - Convert `value` to copper pieces (int)
     - Convert `weight` to float
     - Flatten `property` arrays
     - Normalize `range` to consistent format
     - Extract `mastery` to string array

2. **`clean_monsters.py`**
   - Input: Raw `data/bestiary/*.json`
   - Output: `cleaned_data/monsters.json`
   - Transformations:
     - Normalize `type` to `{type, tags}` structure
     - Normalize `ac` to array format
     - Normalize `alignment` to string array
     - Convert `cr` from fraction strings to decimals
     - Parse `hp` into `{average, formula}`
     - Normalize damage resistances/immunities

3. **`clean_spells.py`**
   - Input: Raw `data/spells/*.json`
   - Output: `cleaned_data/spells.json`
   - Transformations:
     - Normalize `time` structure
     - Normalize `range` structure
     - Normalize `duration` structure
     - Flatten `components` to simple structure

4. **`validate_cleaned.py`**
   - Input: `cleaned_data/*.json`
   - Output: `cleaned_data/VALIDATION_REPORT.json`, `VALIDATION_REPORT.md`
   - Purpose: Verify no polymorphic fields remain

5. **`clean_all.py`** (Master Script)
   - Runs: clean_items.py → clean_monsters.py → clean_spells.py → validate_cleaned.py
   - Output: `cleaned_data/CLEANING_REPORT.md`

### Status
✅ **COMPLETE** - All cleaning scripts have been run

---

## Phase 0.6: Markup Extraction & Advanced Normalization

**Goal:** Extract structured data from 5etools markup tags and special characters.

### Scripts (Run in Order)

#### 1. **`extract_names.py`**
   - Input: `cleaned_data/items.json`, `cleaned_data/monsters.json`, `cleaned_data/spells.json`
   - Output: `cleaned_data/items_extracted.json`, `cleaned_data/monsters_extracted.json`, `cleaned_data/spells_extracted.json`
   - Transformations:
     - Remove all `{@...}` markup from name fields
     - Extract base name and variant from parentheses
     - Parse quantities: "Arrow (20)" → base_name + default_quantity
     - Parse containers: "Acid (vial)" → base_name + container_type
     - Parse bonuses: "+1 Longsword" → base_name + bonus_display
   - New Fields:
     - Items: `base_name`, `variant_name`, `container_type`, `default_quantity`, `bonus_display`
     - Monsters: `base_name`, `variant_name`, `variant_notes`

#### 2. **`normalize_bonuses.py`**
   - Input: `cleaned_data/items_extracted.json`
   - Output: Modifies `items_extracted.json` in place
   - Transformations:
     - Convert bonus strings to integers: "+1" → 1
     - Fields: bonusWeapon, bonusAc, bonusSpellAttack, bonusSpellSaveDc, bonusSavingThrow

#### 3. **`normalize_type_codes.py`**
   - Input: `cleaned_data/items_extracted.json`
   - Output: Modifies `items_extracted.json` in place
   - Transformations:
     - Handle $ prefix in type codes: "$G" → "G" + is_generic_variant flag
   - New Fields:
     - Items: `is_generic_variant`

#### 4. **`extract_conditions.py`** (TODO)
   - Input: `cleaned_data/*_extracted.json`
   - Output: `extraction_data/conditions_extracted.json`
   - Purpose:
     - Parse `{@condition name|source}` tags from all text fields
     - Extract save DC and ability from surrounding context
     - Build relationship data for junction tables
   - Example: "must succeed on a DC 15 Constitution save or be {@condition poisoned|XPHB}"
     → Extract: condition=poisoned, save_dc=15, save_ability=Constitution

#### 5. **`extract_damage.py`** (TODO)
   - Input: `cleaned_data/*_extracted.json`
   - Output: `extraction_data/damage_extracted.json`
   - Purpose:
     - Parse `{@damage dice+bonus}` expressions
     - Extract damage type from surrounding text
     - Parse monster attack blocks
     - Parse spell damage scaling
   - Example: "{@damage 2d6 + 4} fire damage"
     → Extract: dice=2d6, bonus=4, type=fire

#### 6. **`extract_cross_refs.py`** (TODO)
   - Input: `cleaned_data/*_extracted.json`
   - Output: `extraction_data/cross_refs_extracted.json`
   - Purpose:
     - Parse `{@item name|source}` references
     - Parse `{@spell name|source}` references
     - Parse `{@creature name|source}` references
     - Build relationship tables (item requires item, spell summons creature, etc.)

#### 7. **`validate_extraction.py`** (TODO)
   - Input: `cleaned_data/*_extracted.json`, `extraction_data/*.json`
   - Output: `cleaned_data/EXTRACTION_VALIDATION.md`
   - Validations:
     - No `{@...}` markup in name fields
     - No `+` prefix in bonus fields
     - No `$` prefix in type codes
     - All extracted condition IDs are valid
     - All extracted damage type IDs are valid
     - All cross-references point to existing entities

#### 8. **`extract_all.py`** (TODO - Master Script)
   - Runs: extract_names.py → normalize_bonuses.py → normalize_type_codes.py → extract_conditions.py → extract_damage.py → extract_cross_refs.py → validate_extraction.py
   - Output: `cleaned_data/EXTRACTION_REPORT.md`

### Status
🔄 **IN PROGRESS** - Basic extraction/normalization complete, advanced extraction pending

**Completed:**
- ✅ extract_names.py (2,722 items, 4,445 monsters, 937 spells)
- ✅ normalize_bonuses.py (438 bonus fields normalized)
- ✅ normalize_type_codes.py (271 type codes normalized)

**Pending:**
- ⏭️ extract_conditions.py
- ⏭️ extract_damage.py
- ⏭️ extract_cross_refs.py
- ⏭️ validate_extraction.py
- ⏭️ extract_all.py

---

## Phase 1: Schema Design

**Goal:** Design PostgreSQL schema based on cleaned and extracted data.

### Files

1. **`schema.sql`**
   - Complete DDL for all tables
   - Controlled vocabulary tables (sources, item_types, rarities, etc.)
   - Core entity tables (items, monsters, spells)
   - Junction tables for many-to-many relationships
   - Indexes for performance
   - Views for common queries

### Status
✅ **COMPLETE** - Schema designed and tested

---

## Phase 2: Import Implementation

**Goal:** Load cleaned and extracted data into PostgreSQL.

### Scripts (TODO)

1. **`import_controlled_vocab.py`**
   - Input: `analysis/controlled_vocab.json`
   - Output: Populates lookup tables in database
   - Tables: sources, item_types, rarities, damage_types, creature_types, etc.

2. **`import_items.py`**
   - Input: `cleaned_data/items_extracted.json`
   - Output: Populates items table and related junction tables

3. **`import_monsters.py`**
   - Input: `cleaned_data/monsters_extracted.json`
   - Output: Populates monsters table and related junction tables

4. **`import_spells.py`**
   - Input: `cleaned_data/spells_extracted.json`
   - Output: Populates spells table and related junction tables

5. **`import_extracted_data.py`**
   - Input: `extraction_data/*.json`
   - Output: Populates relationship tables (conditions, damage, cross-refs)

6. **`import_all.py`** (Master Script)
   - Runs all import scripts in correct order
   - Handles transactions and rollback on error

### Status
⏭️ **NOT STARTED** - Waiting for Phase 0.6 completion

---

## Phase 3: Validation & Testing

**Goal:** Verify database contents match source data.

### Scripts (TODO)

1. **`validate_import.py`**
   - Compare record counts
   - Verify foreign key relationships
   - Check for orphaned records
   - Validate data integrity

2. **`test_queries.py`**
   - Run sample queries
   - Verify expected results
   - Test performance

### Status
⏭️ **NOT STARTED**

---

## Running the Complete Pipeline

### First-Time Setup

```bash
# 1. Create Python virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your database credentials

# 3. Create database and schema
psql -U postgres -c "CREATE DATABASE dnd5e_reference;"
psql -U dnd5e_user -d dnd5e_reference -f schema.sql
```

### Running the Pipeline (Current State)

```bash
# Phase 0: Analysis (only needed when source data changes significantly)
python3 analyze_json_structure.py
python3 analyze_field_types.py
python3 analyze_controlled_vocab.py
python3 analyze_relationships.py
python3 sample_records.py

# Phase 0.5: Cleaning
python3 clean_all.py
# Creates: cleaned_data/items.json, monsters.json, spells.json

# Phase 0.6: Extraction (current progress)
python3 extract_names.py
python3 normalize_bonuses.py
python3 normalize_type_codes.py
# Creates: cleaned_data/items_extracted.json, monsters_extracted.json, spells_extracted.json

# Phase 0.6: Advanced Extraction (TODO)
python3 extract_conditions.py
python3 extract_damage.py
python3 extract_cross_refs.py
python3 validate_extraction.py
# Creates: extraction_data/*.json

# Phase 2: Import (TODO)
python3 import_all.py
```

### Running the Pipeline (Future - Fully Automated)

Once complete, the entire pipeline will be:

```bash
# One command to rule them all
python3 run_pipeline.py --source /path/to/5etools-src --target dnd5e_reference
```

---

## Data Flow Diagram

```
5etools-src/data/
├── items-base.json ────┐
├── items.json ─────────┤
├── bestiary/*.json ────┼──> Phase 0: Analysis ──> analysis/
├── spells/*.json ──────┤                             ├── structure_report.json
└── *.json ─────────────┘                             ├── field_types_report.json
                                                      ├── controlled_vocab.json
                                                      └── samples/
                          ↓

                    Phase 0.5: Cleaning ──> cleaned_data/
                                              ├── items.json
                                              ├── monsters.json
                                              └── spells.json
                          ↓

                   Phase 0.6: Extraction ──> cleaned_data/
                                              ├── items_extracted.json
                                              ├── monsters_extracted.json
                                              ├── spells_extracted.json
                                              └── extraction_data/
                                                  ├── conditions_extracted.json
                                                  ├── damage_extracted.json
                                                  └── cross_refs_extracted.json
                          ↓

                     Phase 1: Schema ──> schema.sql
                          ↓

                     Phase 2: Import ──> PostgreSQL
                                          dnd5e_reference
                                          ├── items (2,722 records)
                                          ├── monsters (4,445 records)
                                          ├── spells (937 records)
                                          └── [relationships tables]
```

---

## File Locations

### Input Data
- **5etools source:** `/home/ctabone/dnd_bot/5etools-src-2.15.0/data/`

### Output Data
- **Analysis:** `analysis/` (generated once per version)
- **Cleaned:** `cleaned_data/` (regenerated on each run)
- **Extracted:** `extraction_data/` (regenerated on each run)
- **Schema:** `schema.sql` (version controlled)
- **Database:** PostgreSQL `dnd5e_reference`

---

## Version Management

### When 5etools Updates

1. **Download new 5etools-src version** to new directory
2. **Update .env** to point to new source directory
3. **Run analysis** to detect new fields or structures
4. **Review differences** in structure reports
5. **Update cleaning scripts** if new patterns found
6. **Run full pipeline** to regenerate cleaned and extracted data
7. **Backup database** before import
8. **Run import** to refresh database
9. **Validate** results

### Tracking Changes

- `PLAN.md` - Project roadmap and phases
- `FLOW.md` - This file - pipeline documentation
- `README.md` - Project overview and quick start
- `analysis/SUMMARY.md` - Analysis findings
- `cleaned_data/CLEANING_REPORT.md` - Cleaning statistics
- `cleaned_data/EXTRACTION_REPORT.md` - Extraction statistics

---

## Performance Considerations

### Current Runtime

- **Phase 0 (Analysis):** ~2-3 minutes total
- **Phase 0.5 (Cleaning):** ~30-45 seconds total
- **Phase 0.6 (Extraction):** ~15-20 seconds for basic extraction
- **Phase 0.6 (Advanced):** Estimated ~5-10 minutes (not yet implemented)

### Optimization Strategies

1. **Batch Processing:** Process records in batches of 100
2. **Progress Bars:** Use tqdm for visual feedback
3. **Compiled Regex:** Compile patterns once, reuse
4. **Parallel Processing:** Consider for independent files (future)
5. **Caching:** Cache lookup tables during import

---

## Error Handling

### Design Principles

1. **Fail Fast:** Stop on critical errors (missing files, invalid JSON)
2. **Log Warnings:** Continue on data anomalies, but log them
3. **Validate Early:** Check data structure before processing
4. **Atomic Transactions:** Database imports use transactions
5. **Rollback on Failure:** Full rollback if any import fails

### Error Recovery

- All scripts are **idempotent** - safe to re-run
- Intermediate files can be deleted and regenerated
- Database imports should be wrapped in transactions

---

## Testing Strategy

### Unit Tests (Future)
- Test parsing functions with known examples
- Test normalization logic with edge cases
- Test validation rules

### Integration Tests (Future)
- End-to-end pipeline test with sample data
- Verify output matches expected structure
- Performance benchmarks

### Manual Validation
- Review sample records after each phase
- Check validation reports
- Run SQL queries to verify relationships

---

## Maintenance

### Regular Tasks
- Monitor 5etools GitHub for new releases
- Update pipeline when data structure changes
- Keep documentation synchronized with code
- Archive old database versions before updates

### Code Quality
- Scripts are self-documenting with docstrings
- Progress output shows what's happening
- Validation reports catch issues early
- Git commits track all changes

---

## Future Enhancements

### Pipeline Improvements
- [ ] Single master script: `run_pipeline.py`
- [ ] Parallel processing for large files
- [ ] Incremental updates (only changed records)
- [ ] Web UI for monitoring pipeline progress
- [ ] Automated testing suite

### Data Enhancements
- [ ] Additional entity types (races, backgrounds, classes)
- [ ] Expanded cross-reference extraction
- [ ] Full-text search optimization
- [ ] Data versioning and history tracking

---

## Questions?

See `PLAN.md` for detailed phase descriptions and `README.md` for project overview.
