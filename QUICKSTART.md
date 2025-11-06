# Quick Start Guide

## TL;DR - Update Database with New 5etools Data

```bash
# The one command you need:
python3 run_pipeline.py --mode full --drop --skip-analysis --verbose
```

This command will:
- ✅ Clean and extract data (~40 seconds)
- ✅ Drop and recreate database (~3 seconds)
- ✅ Import all entities and relationships (~3-5 minutes)
- ✅ Validate data integrity (8 categories)
- ✅ Run 46 tests with performance benchmarks
- ⏱️  Total time: ~5-8 minutes

---

## Common Commands

### Check Everything (No Changes)
```bash
# Dry run - validate files and connections
python3 run_pipeline.py --mode dry-run
```

### Full Pipeline (Drop and Replace)
```bash
# Recommended for data updates
python3 run_pipeline.py --mode full --drop --skip-analysis --verbose

# With analysis (for major 5etools structure changes)
python3 run_pipeline.py --mode full --drop --verbose
```

### Resume After Failure
```bash
# If import failed, resume from Phase 2
python3 run_pipeline.py --mode resume --from-phase 2

# If only tests failed, resume from Phase 3
python3 run_pipeline.py --mode resume --from-phase 3
```

### Run Validation Only
```bash
# Validate database without re-importing
python3 validate_import.py -v

# Run tests only
./run_tests.sh -v
```

### Run Performance Benchmarks Only
```bash
# Just the 4 performance benchmarks
./run_tests.sh --benchmark-only
```

---

## What Each Phase Does

| Phase | What It Does | Duration | Skippable? |
|-------|--------------|----------|------------|
| **0: Analysis** | Analyze 5etools JSON structure | ~3 min | Yes (use `--skip-analysis`) |
| **0.5: Cleaning** | Normalize data types & structures | ~23 sec | Yes (use `--skip-cleaning`) |
| **0.6: Extraction** | Extract structured data from markup | ~18 sec | Yes (use `--skip-extraction`) |
| **1: Schema** | Create database schema & tables | ~3 sec | No |
| **2: Import** | Load all data into PostgreSQL | ~3-5 min | No |
| **3: Testing** | Validate & test database | ~30 sec | No |

**Typical update**: Skip phases 0, 0.5, 0.6 (use `--skip-analysis --skip-cleaning --skip-extraction`)

---

## Pipeline Output Example

```
================================================================================
5etools-to-postgres Data Pipeline
================================================================================
Start time: 2025-11-06 19:30:45
Mode: full
Project directory: /home/ctabone/dnd_bot/5etools-to-postgres
================================================================================

⏭️  Skipping Phase 0 (Analysis) - using existing analysis

================================================================================
PHASE 0.5: Data Cleaning & Normalization
================================================================================

▶️  Running: python3 clean_all.py
✅ Phase 0.5: Cleaning completed in 23.1s

--------------------------------------------------------------------------------
CHECKPOINT: Extracted Data Validation
--------------------------------------------------------------------------------
✅ cleaned_data/items.json: 2,722 records
✅ cleaned_data/monsters.json: 4,445 records
✅ cleaned_data/spells.json: 937 records

[... continues through all phases ...]

================================================================================
PIPELINE SUMMARY
================================================================================
Total duration: 347.2s (5.8 minutes)

Phase                                    Status       Duration
--------------------------------------------------------------------------------
Phase 0: Analysis                        ⏭️  skipped       0.0s
Phase 0.5: Cleaning                      ✅ success      23.1s
Phase 0.6: Extraction                    ✅ success      18.4s
Phase 1: Schema                          ✅ success       2.8s
Phase 2: Import Items                    ✅ success      45.2s
Phase 2: Import Monsters                 ✅ success      89.7s
Phase 2: Import Spells                   ✅ success      21.3s
Phase 2: Import Relationships            ✅ success     112.5s
Phase 3: Validation                      ✅ success       8.1s
Phase 3: Testing                         ✅ success      26.1s
--------------------------------------------------------------------------------
Total: 10 phases | Success: 9 | Warning: 0 | Failed: 0 | Skipped: 1
================================================================================
```

---

## Troubleshooting

### Permission Errors

```bash
# Make sure scripts are executable
chmod +x run_pipeline.py run_tests.sh

# Ensure postgres user can read project files
chmod o+rx /home/ctabone /home/ctabone/dnd_bot /home/ctabone/dnd_bot/5etools-to-postgres
```

### Database Connection Errors

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
sudo -u postgres psql -c "SELECT 1"
```

### Pipeline Fails at Import

```bash
# Check if database exists
sudo -u postgres psql -l | grep dnd5e_reference

# If database is corrupted, recreate it
sudo -u postgres psql -c "DROP DATABASE IF EXISTS dnd5e_reference; CREATE DATABASE dnd5e_reference;"

# Resume from Phase 1
python3 run_pipeline.py --mode resume --from-phase 1
```

### Test Failures

```bash
# Run tests with full output
./run_tests.sh -v --tb=long

# Run only failing tests
./run_tests.sh -v --lf  # last failed

# Run specific test
./run_tests.sh -v -k "test_get_all_items"
```

---

## File Locations

| Data | Location | Regenerated? |
|------|----------|--------------|
| Source JSON | `/home/ctabone/dnd_bot/5etools-src-2.15.0/data/` | No (from 5etools) |
| Cleaned data | `cleaned_data/*.json` | Yes (Phase 0.5) |
| Extracted data | `extraction_data/*.json` | Yes (Phase 0.6) |
| Database | PostgreSQL `dnd5e_reference` | Yes (Phase 1-2) |

---

## Expected Results

### Database Contents (After Full Import)

| Category | Count |
|----------|-------|
| **Core Entities** | 8,104 |
| - Items | 2,722 |
| - Monsters | 4,445 |
| - Spells | 937 |
| **Lookup Tables** | 305 |
| **Condition Relationships** | 4,823 |
| **Damage Relationships** | 5,613 |
| **Cross-References** | 2,023 |
| **TOTAL** | 28,149 |

### Test Results (Expected)

- **46 tests** - all passing ✅
- **4 performance benchmarks**:
  - Simple lookup: ~229 μs (4,374 ops/sec)
  - Aggregation: ~414 μs (2,415 ops/sec)
  - Multi-table join: ~992 μs (1,008 ops/sec)
  - Complex join: ~2,407 μs (416 ops/sec)

### Validation Results (Expected)

- ✅ Entity counts match documentation
- ✅ Zero orphaned records
- ✅ No unexpected duplicates
- ✅ All foreign keys valid
- ✅ Data ranges within bounds
- ✅ Schema correct (38 tables, 141 indexes)

---

## Next Steps

After successful import:

1. **Review the output**: Check for any warnings
2. **Test queries**: Try some sample queries in psql
3. **Backup if satisfied**: `pg_dump dnd5e_reference > backup.sql`
4. **Build your application**: Use the database in your D&D bot/app

---

## Full Documentation

- **FLOW.md** - Complete pipeline documentation
- **TESTING.md** - Testing and validation details
- **PHASE_2_PROGRESS.md** - Import statistics and bug tracking
- **PLAN.md** - Overall project roadmap

---

## Support

If you encounter issues:

1. Check the error message in pipeline output
2. Review relevant documentation (FLOW.md, TESTING.md)
3. Try `--verbose` mode for more details
4. Use `--mode dry-run` to check configuration
5. Check PHASE_2_PROGRESS.md for known issues

---

## One-Line Summary

**To update database with new 5etools data:**

```bash
python3 run_pipeline.py --mode full --drop --skip-analysis --verbose
```

That's it! ✨
