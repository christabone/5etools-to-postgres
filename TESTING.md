# Database Testing and Validation

This document describes the comprehensive testing and validation infrastructure for the D&D 5e PostgreSQL database.

## Overview

We have two complementary tools for ensuring database quality:

1. **validate_import.py** - Comprehensive validation script that checks data integrity, schema correctness, and matches against expected counts
2. **test_database.py** - Complete test suite with 46 tests covering queries, performance, and data integrity

## Validation Script (validate_import.py)

### Purpose
Permanent validation script that can be run anytime to verify database integrity and correctness.

### Features
- 8 validation categories with severity classification (CRITICAL, MAJOR, MINOR, INFO)
- JSON output option for automation/CI/CD integration
- Exit codes: 0 (pass), 1 (critical), 2 (major), 3 (minor)
- Detailed fix suggestions for each issue found
- Comprehensive metrics collection

### Validation Categories

1. **Entity Count Validation**
   - Verifies all tables match documented expected counts
   - Checks: items (2722), monsters (4445), spells (937), all lookup tables

2. **Foreign Key Integrity**
   - Checks for orphaned records in 18 FK relationships
   - Ensures all references point to valid parent records

3. **Duplicate Detection**
   - Scans 6 tables for unexpected duplicates
   - Catches issues like the item_damage/spell_damage bug we fixed

4. **NULL Value Validation**
   - Verifies required fields have no NULLs
   - Checks entity names, sources, and critical attributes

5. **Data Range Validation**
   - CR values: 0-30
   - Spell levels: 0-9
   - HP values: positive integers

6. **Schema Validation**
   - 141 indexes present
   - 54 foreign keys configured
   - Required UNIQUE constraints (item_damage, spell_damage)

7. **Source Data Comparison**
   - Database counts match source JSON files
   - Verifies no data loss during import

8. **Metrics Collection**
   - Database size
   - Total record count
   - Table statistics

### Usage

```bash
# Basic validation
python3 validate_import.py

# Verbose output
python3 validate_import.py -v

# JSON output for automation
python3 validate_import.py --json

# Verbose + JSON
python3 validate_import.py -v --json
```

### Exit Codes
- `0`: All checks passed
- `1`: Critical issues found (data loss, corruption, missing required constraints)
- `2`: Major issues found (orphaned records, schema problems)
- `3`: Minor issues found (warnings, non-critical discrepancies)

### When to Run
- After any data import or update
- Before deploying to production
- As part of CI/CD pipeline
- Periodically to verify data integrity

## Test Suite (test_database.py)

### Purpose
Comprehensive pytest-based test suite covering real-world queries, performance benchmarks, and data integrity checks.

### Test Statistics
- **46 total tests** across 9 test classes
- **4 performance benchmarks** using pytest-benchmark
- **100% pass rate** (all 46 tests passing)

### Test Categories

#### 1. TestItemQueries (6 tests)
Tests item-related queries:
- Get all items (2722 items)
- Get item by name
- Filter by rarity
- Items with damage
- Versatile weapons (146 items)
- Items with specific properties (using array operations)

#### 2. TestMonsterQueries (6 tests)
Tests monster-related queries:
- Get all monsters (4445 monsters)
- Filter by CR range (CR 10-15)
- Spellcasting monsters (>5 spells)
- Monster attacks
- Filter by type
- Monsters with conditions

#### 3. TestSpellQueries (8 tests)
Tests spell-related queries:
- Get all spells (937 spells)
- Filter by level
- Cantrips (level 0)
- Ritual spells (78 spells)
- Concentration spells (405 spells)
- Filter by school (Evocation, etc.)
- Damage-dealing spells (499 damage records)
- Spell summons

#### 4. TestRelationshipQueries (4 tests)
Tests cross-reference relationships:
- Items granting spells
- Spells referencing other spells
- Monsters with magic items
- Cross-reference completeness (all 9 tables)

#### 5. TestAggregationQueries (5 tests)
Tests aggregation and statistics:
- Spell count by level distribution
- Monster count by CR distribution
- Item count by rarity distribution
- Average monster stats (HP, AC, etc.)
- Damage type frequency

#### 6. TestSearchQueries (3 tests)
Tests search functionality:
- Case-insensitive name search
- Search by source
- Multi-criteria monster search

#### 7. TestEdgeCases (6 tests)
Tests boundary conditions:
- Level 0 cantrips
- CR 0 monsters
- Items without rarity
- Items without type
- Spell max level (9)
- Highest CR monster (30)

#### 8. TestPerformance (4 tests - BENCHMARKED)
Performance benchmarks with pytest-benchmark:

| Test | Mean Time | OPS | Description |
|------|-----------|-----|-------------|
| test_index_on_item_name | 229 μs | 4,374 ops/s | Index effectiveness on item.name |
| test_aggregation_performance | 414 μs | 2,415 ops/s | Complex aggregation query |
| test_join_performance_monster_spells | 992 μs | 1,008 ops/s | Multi-table join performance |
| test_complex_join_performance | 2,407 μs | 416 ops/s | Complex 5-table join |

All queries complete in under 3ms, demonstrating excellent index effectiveness.

#### 9. TestDataIntegrity (4 tests)
Tests data integrity constraints:
- No duplicate entity names within same source
- All entities have sources
- Referential integrity (no orphaned records)
- UNIQUE constraints enforced

### Usage

```bash
# Run all tests with verbose output
./run_tests.sh -v

# Run specific test class
./run_tests.sh -v -k "TestItemQueries"

# Run specific test
./run_tests.sh -v -k "test_get_all_items"

# Run only performance benchmarks
./run_tests.sh --benchmark-only

# Run all except benchmarks
./run_tests.sh --benchmark-skip

# Run with detailed benchmark statistics
./run_tests.sh -v --benchmark-only --benchmark-verbose
```

### Permissions

The `run_tests.sh` wrapper automatically handles postgres user permissions:
- Detects current user
- Automatically uses `sudo -u postgres` if needed
- No manual user switching required

### Performance Benchmark Results

Latest benchmark results (all times in microseconds):

```
Name                                      Min       Max      Mean    Median    OPS
test_index_on_item_name                   182μs    1,180μs   229μs    188μs   4,374/s
test_aggregation_performance              365μs    1,261μs   414μs    378μs   2,415/s
test_join_performance_monster_spells      769μs    4,432μs   992μs    870μs   1,008/s
test_complex_join_performance           2,034μs    6,659μs  2,407μs  2,278μs    416/s
```

Key takeaways:
- Simple lookups: <250μs (sub-millisecond)
- Aggregations: ~400μs (excellent)
- Multi-table joins: <1ms (very good)
- Complex 5-table joins: ~2.4ms (acceptable)
- All indexes working effectively

## Test Infrastructure

### Fixtures

**db_connection** (session-scoped)
- Creates single database connection for all tests
- Reused across all tests for efficiency
- Automatically closed at session end

**cursor** (function-scoped)
- Creates new cursor for each test
- Uses RealDictCursor for dict-based results
- Automatically handles failed transaction rollbacks
- Prevents transaction failure cascades

### Dependencies

```bash
# Required packages (installed via apt)
sudo apt-get install python3-pytest python3-pytest-benchmark

# Or via pip (if not externally-managed environment)
pip3 install pytest pytest-benchmark
```

### Test File Structure

```
test_database.py
├── Imports & Setup
├── Fixtures (db_connection, cursor)
├── TestItemQueries (6 tests)
├── TestMonsterQueries (6 tests)
├── TestSpellQueries (8 tests)
├── TestRelationshipQueries (4 tests)
├── TestAggregationQueries (5 tests)
├── TestSearchQueries (3 tests)
├── TestEdgeCases (6 tests)
├── TestPerformance (4 benchmarked tests)
└── TestDataIntegrity (4 tests)
```

## Testing Best Practices

### 1. Run Validation First
Always run `validate_import.py` before running tests to catch any data integrity issues.

### 2. Check Test Coverage
Ensure tests cover:
- All major query patterns
- All relationship types
- Edge cases and boundary conditions
- Performance critical paths

### 3. Monitor Performance
Regularly run benchmarks to detect performance regressions:
```bash
./run_tests.sh --benchmark-only --benchmark-compare
```

### 4. Use Appropriate Test Isolation
- Tests are independent (can run in any order)
- Each test gets fresh cursor
- Failed transactions automatically rolled back
- No test pollution between runs

### 5. Verify After Changes
After any schema or data changes:
1. Run validation: `python3 validate_import.py -v`
2. Run all tests: `./run_tests.sh -v`
3. Check benchmarks: `./run_tests.sh --benchmark-only`

## Continuous Integration

### Recommended CI Pipeline

```yaml
# Example CI configuration
test:
  script:
    # Step 1: Validation
    - python3 validate_import.py --json > validation_results.json
    - if [ $? -gt 0 ]; then exit 1; fi

    # Step 2: Run all tests
    - ./run_tests.sh -v --junitxml=test_results.xml

    # Step 3: Run benchmarks
    - ./run_tests.sh --benchmark-only --benchmark-json=benchmark_results.json

  artifacts:
    - validation_results.json
    - test_results.xml
    - benchmark_results.json
```

## Troubleshooting

### Permission Errors
If you see permission errors:
```bash
# Make sure postgres user can read test files
chmod +r test_database.py
chmod o+rx /path/to/project

# Use the wrapper script (handles permissions automatically)
./run_tests.sh -v
```

### Failed Transactions
If tests fail with "transaction aborted" errors:
- The cursor fixture should handle this automatically
- If issues persist, check that the fixture rollback logic is working
- Each test should start with clean transaction state

### Benchmark Variability
If benchmark results vary significantly:
- System load affects benchmarks
- Run on idle system for consistent results
- Use `--benchmark-min-rounds=10` for more samples
- Disk I/O and cache warmth affect results

### Test Failures
If a test fails:
1. Check validation first: `python3 validate_import.py -v`
2. Verify database connection: `psql -d dnd5e_reference -c "SELECT 1"`
3. Check data integrity: Look for orphaned records or missing data
4. Review test expectations: Ensure documented counts are current

## Bug Discovery History

### Bug #13: Missing UNIQUE Constraints (CRITICAL)
**Discovered by**: Neutral validation agent
**Impact**: 100% systematic duplication in item_damage and spell_damage tables
**Evidence**: 1,299 duplicate records (758 + 541)
**Fix**: Added UNIQUE constraints, removed duplicates
**Lesson**: Always validate after "successful" imports; missing constraints break ON CONFLICT DO NOTHING

This bug demonstrates why comprehensive validation is essential. The import appeared successful but had hidden data corruption that only validation detected.

## Summary

Our testing infrastructure provides:
- **Comprehensive validation** with 8 categories of checks
- **46 tests** covering all query patterns
- **4 performance benchmarks** showing sub-3ms query times
- **100% test pass rate** demonstrating data quality
- **Automated tooling** for easy repeated validation
- **CI/CD ready** with JSON output and exit codes

Both tools work together to ensure database quality:
- `validate_import.py` catches data issues and schema problems
- `test_database.py` verifies real-world query functionality and performance

Run both after any changes to maintain database integrity and quality.
