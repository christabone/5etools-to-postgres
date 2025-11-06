# 5etools-to-postgres

> A production-ready data pipeline that transforms D&D 5th Edition JSON data from 5etools into a normalized, queryable PostgreSQL database.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-46%20passing-brightgreen)]()
[![Database](https://img.shields.io/badge/database-PostgreSQL%2012%2B-blue)]()
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)]()

**28,149+ records | 38 tables | 141 indexes | 46 automated tests | Sub-3ms query performance**

---

## What This Does

Converts comprehensive D&D 5th Edition reference data from [5etools](https://5e.tools/) JSON files into a **fully normalized PostgreSQL database** for use in your applications, campaigns, virtual tabletops, or analysis tools.

This isn't just a simple JSON-to-SQL converter. It's a **complete data pipeline** that:
- Normalizes polymorphic data structures
- Extracts structured data from 189,000+ markup tags
- Builds rich relationship tables (conditions, damage, cross-references)
- Validates data integrity with comprehensive testing
- Provides production-ready performance (sub-3ms queries)

### Key Features

- **Comprehensive Data Coverage**: 2,722 items, 4,445 monsters, 937 spells, 305 lookup values
- **Advanced Normalization**: Extracts 12,459 relationships from markup (conditions, damage, cross-refs)
- **Production-Ready**: 46 automated tests with performance benchmarks
- **Fast Import**: Complete pipeline runs in 5-8 minutes
- **Drop-and-Replace**: Clean updates when 5etools releases new data
- **Well-Documented**: Extensive documentation for architecture, testing, and usage

---

## Quick Start

Get a fully populated D&D database in under 10 minutes:

### Prerequisites

```bash
# Required software
sudo apt-get install postgresql python3 python3-pytest python3-pytest-benchmark

# Verify versions
python3 --version  # 3.8+
psql --version     # 12+
```

### Installation

```bash
# 1. Clone repository
git clone https://github.com/christabone/5etools-to-postgres.git
cd 5etools-to-postgres

# 2. Download 5etools data (v2.15.0)
wget https://github.com/5etools-mirror-3/5etools-src/archive/refs/tags/v2.15.0.tar.gz -O 5etools.tar.gz
tar -xzf 5etools.tar.gz

# 3. Create PostgreSQL database
sudo -u postgres psql -c "CREATE DATABASE dnd5e_reference;"

# 4. Run the complete pipeline
python3 run_pipeline.py --mode full --drop --skip-analysis --verbose
```

That's it! In 5-8 minutes you'll have a fully populated, validated database.

### What Gets Imported

| Category | Count | Description |
|----------|-------|-------------|
| **Core Entities** | **8,104** | Items, monsters, and spells |
| Items | 2,722 | Weapons, armor, magic items, equipment |
| Monsters | 4,445 | Complete stat blocks from all sources |
| Spells | 937 | All spells with components and effects |
| **Lookup Tables** | **305** | Sources, types, rarities, schools, etc. |
| **Relationships** | **12,459** | Extracted from markup |
| Condition Refs | 4,823 | Items/spells/monsters that inflict conditions |
| Damage Records | 5,613 | Structured damage data with types |
| Cross-References | 2,023 | Item→spell, monster→spell, summons |
| **TOTAL** | **28,149** | Fully validated, indexed, and tested |

---

## Why Use This?

### For Application Developers
- **Rich, Queryable Data**: No more parsing JSON in your app
- **Normalized Structure**: Easy JOINs, no nested data headaches
- **Fast Performance**: Sub-millisecond queries with proper indexes
- **Relationship Tables**: Query "all spells that deal fire damage" instantly

### For DMs and Campaign Managers
- **Searchable Reference**: Build custom DM tools with SQL queries
- **Cross-Reference Discovery**: Find all items that grant spells
- **Data Analysis**: Analyze game balance, CR distribution, etc.
- **Integration-Ready**: Use with virtual tabletops, Discord bots, web apps

### For Data Scientists
- **Clean, Normalized Data**: Perfect for analysis and visualization
- **28K+ Records**: Comprehensive dataset for ML or statistics
- **Reproducible Pipeline**: Update when 5etools releases new data
- **Full Metadata**: All sources, variants, and relationships preserved

---

## Database Schema

### Core Tables (38 total)

**Controlled Vocabulary** (10 tables)
- `sources` - All D&D sourcebooks (126 records)
- `item_rarities`, `damage_types`, `condition_types`, `creature_types`, `creature_sizes`, `spell_schools`, `alignment_values`, `skills`, `attack_types`

**Core Entities** (3 tables)
- `items` - All items, weapons, armor, magic items
- `monsters` - All creatures with complete stat blocks
- `spells` - All spells with metadata and effects

**Relationship Tables** (16 tables)
- Condition relationships: `item_conditions`, `monster_conditions`, `spell_conditions`
- Damage relationships: `item_damage`, `monster_attacks`, `spell_damage`
- Cross-references: `item_related_items`, `item_grants_spells`, `monster_spells`, `spell_summons`, etc.

**Junction Tables** (9 tables)
- Many-to-many: properties, alignments, resistances, immunities, etc.

### Performance

- **141 indexes** for optimal query performance
- **54 foreign keys** ensuring referential integrity
- **Sub-3ms queries** on properly indexed fields:
  - Simple lookups: ~229 μs (4,374 ops/sec)
  - Aggregations: ~414 μs (2,415 ops/sec)
  - Multi-table joins: ~992 μs (1,008 ops/sec)
  - Complex 5-table joins: ~2,407 μs (416 ops/sec)

---

## Usage Examples

### Basic Queries

```sql
-- Find all magic swords
SELECT name, rarity, value_cp/100 as gold_cost
FROM items
WHERE base_name LIKE '%sword%' AND rarity != 'none'
ORDER BY rarity, name;

-- Get CR 10-15 monsters for encounter building
SELECT name, type, cr, hp_average, ac_primary
FROM monsters
WHERE cr BETWEEN 10 AND 15
ORDER BY cr, name;

-- Find all fire damage spells
SELECT s.name, s.level, dt.name as damage_type
FROM spells s
JOIN spell_damage sd ON s.id = sd.spell_id
JOIN damage_types dt ON sd.damage_type_id = dt.id
WHERE dt.name = 'fire'
ORDER BY s.level, s.name;
```

### Advanced Queries

```sql
-- Find all items that inflict the poisoned condition
SELECT i.name, ic.save_dc, ic.save_ability, ic.duration_text
FROM items i
JOIN item_conditions ic ON i.id = ic.item_id
JOIN condition_types ct ON ic.condition_id = ct.id
WHERE ct.name = 'poisoned' AND ic.inflicts = true;

-- Get monsters with spellcasting (5+ spells)
SELECT m.name, COUNT(ms.spell_id) as spell_count
FROM monsters m
JOIN monster_spells ms ON m.id = ms.monster_id
GROUP BY m.id, m.name
HAVING COUNT(ms.spell_id) >= 5
ORDER BY spell_count DESC;

-- Find versatile weapons (two-handed option)
SELECT name, dmg1, dmg2, dmgtype
FROM items
WHERE dmg2 IS NOT NULL
ORDER BY name;

-- Spell damage scaling by level
SELECT s.name, sd.damage_at_level, sd.damage_dice, dt.name as damage_type
FROM spells s
JOIN spell_damage sd ON s.id = sd.spell_id
JOIN damage_types dt ON sd.damage_type_id = dt.id
WHERE s.name = 'Fireball'
ORDER BY sd.damage_at_level;
```

---

## Pipeline Architecture

The import process follows a **data-driven development** approach:

```
Phase 0: Analysis (optional)
    ↓
Phase 0.5: Data Cleaning (~23 sec)
    ↓
Phase 0.6: Markup Extraction (~18 sec)
    ↓
Phase 1: Schema Creation (~3 sec)
    ↓
Phase 2: Import Entities + Relationships (~4 min)
    ↓
Phase 3: Validation + Testing (~35 sec)
    ↓
Ready to Use!
```

### Pipeline Features

- **Repeatable**: Run anytime to refresh data from new 5etools releases
- **Idempotent**: Safe to re-run, produces same results
- **Validated**: Automatic checkpoints verify data integrity
- **Fast**: Complete pipeline in 5-8 minutes
- **Resumable**: Resume from any phase if interrupted

### Run Options

```bash
# Full pipeline (recommended for updates)
python3 run_pipeline.py --mode full --drop --skip-analysis --verbose

# Dry run (validate without changes)
python3 run_pipeline.py --mode dry-run

# Resume from specific phase
python3 run_pipeline.py --mode resume --from-phase 2

# Run tests only
./run_tests.sh -v

# Run performance benchmarks only
./run_tests.sh --benchmark-only
```

---

## Testing & Validation

### Comprehensive Test Suite

**46 tests** covering all functionality:
- ✅ 6 item queries
- ✅ 6 monster queries
- ✅ 8 spell queries
- ✅ 4 relationship queries
- ✅ 5 aggregation queries
- ✅ 3 search queries
- ✅ 6 edge case tests
- ✅ 4 performance benchmarks
- ✅ 4 data integrity checks

**100% pass rate** - all tests passing

### Validation Categories

The `validate_import.py` script checks 8 categories:
1. Entity counts match expected (2722 items, 4445 monsters, 937 spells)
2. Foreign key integrity (zero orphaned records)
3. Duplicate detection (no unexpected duplicates)
4. NULL value validation (required fields populated)
5. Data range validation (CR 0-30, spell levels 0-9)
6. Schema validation (141 indexes, 54 foreign keys)
7. Source data comparison (no data loss during import)
8. Metrics collection (database size, record counts)

```bash
# Run validation
python3 validate_import.py -v

# Output validation report in JSON
python3 validate_import.py --json
```

---

## Documentation

Comprehensive documentation included:

- **[QUICKSTART.md](QUICKSTART.md)** - Quick reference for common commands
- **[docs/architecture/FLOW.md](docs/architecture/FLOW.md)** - Complete pipeline documentation with diagrams
- **[TESTING.md](TESTING.md)** - Testing framework and validation details
- **[docs/architecture/PLAN.md](docs/architecture/PLAN.md)** - Project roadmap and implementation phases
- **[docs/architecture/INDEX_PLAN.md](docs/architecture/INDEX_PLAN.md)** - Index optimization strategy
- **[docs/architecture/IMPORT_PLAN.md](docs/architecture/IMPORT_PLAN.md)** - Import implementation details

---

## Requirements

### System Requirements
- **PostgreSQL 12+** - Database server
- **Python 3.8+** - Import scripts
- **4GB RAM** - Recommended for import process
- **500MB disk space** - For database

### Python Packages
```bash
# Automatically handled by pipeline
sudo apt-get install python3-pytest python3-pytest-benchmark python3-psycopg2
```

---

## Updating Data

When 5etools releases a new version:

```bash
# 1. Download new 5etools data
wget https://github.com/5etools-mirror-3/5etools-src/archive/refs/tags/vX.X.X.tar.gz -O 5etools.tar.gz
tar -xzf 5etools.tar.gz

# 2. Run pipeline (drop and replace)
python3 run_pipeline.py --mode full --drop --skip-analysis --verbose

# 3. Verify results
python3 validate_import.py -v
./run_tests.sh -v
```

The **drop-and-replace** strategy ensures:
- No orphaned data
- No migration scripts needed
- Guaranteed consistency
- Clean slate with each update

---

## Performance Benchmarks

Latest benchmark results (all times in microseconds):

| Test | Mean Time | OPS/sec | Description |
|------|-----------|---------|-------------|
| Simple lookup | 229 μs | 4,374 | Index effectiveness on item.name |
| Aggregation | 414 μs | 2,415 | Complex aggregation query |
| Multi-table join | 992 μs | 1,008 | 3-table join performance |
| Complex join | 2,407 μs | 416 | 5-table join with aggregation |

All queries complete in **under 3 milliseconds**, demonstrating excellent index effectiveness.

---

## Data Source & Legal

### Data Source

All data is sourced from [5etools](https://5e.tools/), specifically the [5etools-src](https://github.com/5etools-mirror-3/5etools-src) repository (v2.15.0), which aggregates official D&D 5th Edition content.

### Legal Notice

Dungeons & Dragons, D&D, and all related content are owned by Wizards of the Coast LLC. This project is not affiliated with, endorsed, sponsored, or specifically approved by Wizards of the Coast.

This tool is for personal use and development purposes. Users are responsible for ensuring their use complies with Wizards of the Coast's [Fan Content Policy](https://company.wizards.com/en/legal/fancontentpolicy) and applicable laws.

---

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`./run_tests.sh -v`)
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

### Development Setup

```bash
# Run tests
./run_tests.sh -v

# Run validation
python3 validate_import.py -v

# Check performance
./run_tests.sh --benchmark-only
```

---

## Troubleshooting

### Permission Errors

```bash
# Make scripts executable
chmod +x run_pipeline.py run_tests.sh

# Ensure postgres user can read project files
chmod o+rx /path/to/5etools-to-postgres
```

### Database Connection Errors

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
sudo -u postgres psql -c "SELECT 1"
```

### Pipeline Fails During Import

```bash
# Resume from failed phase
python3 run_pipeline.py --mode resume --from-phase 2

# Or restart with verbose output
python3 run_pipeline.py --mode full --drop --verbose
```

---

## Support

- 🐛 **Bug reports**: [Open an issue](https://github.com/christabone/5etools-to-postgres/issues)
- 💡 **Feature requests**: [Open an issue](https://github.com/christabone/5etools-to-postgres/issues)
- 💬 **Questions**: [Discussions](https://github.com/christabone/5etools-to-postgres/discussions)

---

## Acknowledgments

- [5etools](https://5e.tools/) - For maintaining comprehensive D&D data
- [5etools-src](https://github.com/5etools-mirror-3/5etools-src) - Data source repository
- All contributors to the D&D community tools ecosystem

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Project Stats

- **Lines of SQL**: 869 (schema.sql)
- **Python Scripts**: 25+ (analysis, cleaning, extraction, import)
- **Total Records**: 28,149
- **Tables**: 38
- **Indexes**: 141
- **Foreign Keys**: 54
- **Tests**: 46 (100% passing)
- **Pipeline Time**: 5-8 minutes
- **Query Performance**: Sub-3ms

**Built with a data-driven development approach. Clean, tested, production-ready.**

---

Happy adventuring!
