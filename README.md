# 5etools to PostgreSQL Importer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

⚠️ **WORK IN PROGRESS** - Currently in development, not ready for use yet!

Import D&D 5th Edition data from [5etools](https://5e.tools/) JSON files into a structured PostgreSQL database for use in your own applications, campaigns, or tools.

## Current Status

**Phase 0: Data Analysis** ✅ COMPLETE
- Analyzed 741 unique JSON field paths
- Identified 10 polymorphic fields requiring normalization
- Discovered 4,841 controlled vocabulary candidates

**Phase 0.5: Data Cleaning** ✅ COMPLETE
- Normalized ALL polymorphic fields (100% validation pass)
- Cleaned 2,722 items, 4,445 monsters, 937 spells
- Created reproducible cleaning pipeline

**Phase 1: Schema Design** ✅ COMPLETE
- Designed hybrid normalized + JSONB schema
- Created 22 tables (12 CV, 3 core, 7 junction)
- Added full-text search and fuzzy matching support

**Phase 0.6: Markup Extraction** 🚧 IN PROGRESS
- Investigating 189,000+ instances of 5etools markup
- Identifying structured data to extract from text
- Planning relationship tables for conditions, damage, cross-references

**Phase 2: Import Implementation** ⏭️ PENDING

See [PLAN.md](PLAN.md) for detailed roadmap.

## What is this?

This project provides scripts to import comprehensive D&D 5th Edition reference data into PostgreSQL, including:

- **Items** - All weapons, armor, adventuring gear, magic items (2,500+ items)
- **Monsters** - Every creature from all sourcebooks with complete stat blocks (3,000+ monsters)
- **Spells** - All spells with components, effects, and scaling (1,000+ spells)
- **Reference Data** - Item properties, damage types, magic schools, etc.

The data comes from [5etools](https://5e.tools/), a fantastic community-maintained D&D reference that aggregates official content from Wizards of the Coast sourcebooks.

## Why use this?

- Build D&D companion apps with reliable, structured data
- Create custom DM tools with searchable databases
- Integrate D&D content into virtual tabletops
- Analyze game balance and statistics
- Keep campaign data separate from reference data

## Prerequisites

### Required Software

- **Python 3.8+** - [Download here](https://www.python.org/downloads/)
- **PostgreSQL 12+** - [Download here](https://www.postgresql.org/download/)
- **Git** - [Download here](https://git-scm.com/downloads)

### Check your versions

```bash
python3 --version  # Should be 3.8 or higher
psql --version     # Should be 12 or higher
git --version
```

## Installation

### 1. Clone this repository

```bash
git clone https://github.com/christabone/5etools-to-postgres.git
cd 5etools-to-postgres
```

### 2. Download 5etools data

Visit the [5etools-src releases page](https://github.com/5etools-mirror-3/5etools-src/releases) and download the latest release.

**Automated download (recommended):**

```bash
# Download and extract the latest version (v2.15.0)
wget https://github.com/5etools-mirror-3/5etools-src/archive/refs/tags/v2.15.0.tar.gz -O 5etools.tar.gz
tar -xzf 5etools.tar.gz
```

**Manual download:**

1. Go to https://github.com/5etools-mirror-3/5etools-src/releases
2. Download the latest release (e.g., `v2.15.0`)
3. Extract the archive into this directory
4. You should have a folder like `5etools-src-2.15.0/`

### 3. Set up Python environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Linux/Mac
# OR
.\venv\Scripts\activate   # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 4. Set up PostgreSQL database

Create a new database for the D&D reference data:

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE dnd_reference;
CREATE USER dnd_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE dnd_reference TO dnd_user;
\q
```

### 5. Configure database connection

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your database credentials
nano .env  # or use your preferred editor
```

Update these values in `.env`:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=dnd_reference
DB_USER=dnd_user
DB_PASSWORD=your_secure_password
```

## Usage

### Import all data (recommended)

```bash
python import_all.py
```

This will:
1. Create all necessary tables
2. Import items, monsters, and spells
3. Set up lookup tables and relationships
4. Show progress and summary

**Expected runtime:** 2-5 minutes depending on your machine

### Import specific categories

```bash
# Import only items
python import_items.py

# Import only monsters
python import_monsters.py

# Import only spells
python import_spells.py
```

### Verify the import

```bash
# Connect to your database
psql -U dnd_user -d dnd_reference

# Check what was imported
SELECT COUNT(*) FROM items;      -- Should be ~2,500+
SELECT COUNT(*) FROM monsters;   -- Should be ~3,000+
SELECT COUNT(*) FROM spells;     -- Should be ~1,000+

# Search for specific items
SELECT name, type, rarity FROM items WHERE name ILIKE '%sword%';

# Find monsters by CR
SELECT name, cr, type FROM monsters WHERE cr = '1/2';
```

## Database Schema

### Core Tables

#### `items`
All items, weapons, armor, and equipment.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| name | VARCHAR(255) | Item name |
| source | VARCHAR(50) | Sourcebook abbreviation |
| type | VARCHAR(10) | Item type code (M, R, LA, etc.) |
| rarity | VARCHAR(50) | Common, Uncommon, Rare, etc. |
| weight | NUMERIC | Weight in pounds |
| value | INTEGER | Cost in copper pieces |
| damage | VARCHAR(20) | Damage dice (e.g., "1d8") |
| damage_type | VARCHAR(20) | Bludgeoning, Slashing, etc. |
| properties | JSONB | Array of property codes |
| data | JSONB | Full 5etools JSON data |

#### `monsters`
All creatures with complete stat blocks.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| name | VARCHAR(255) | Monster name |
| source | VARCHAR(50) | Sourcebook abbreviation |
| size | VARCHAR(10) | Tiny, Small, Medium, etc. |
| type | VARCHAR(50) | Humanoid, Beast, etc. |
| cr | VARCHAR(10) | Challenge Rating |
| ac | INTEGER | Armor Class |
| hp_avg | INTEGER | Average hit points |
| hp_formula | VARCHAR(50) | HP dice formula |
| str, dex, con, int, wis, cha | INTEGER | Ability scores |
| actions | JSONB | Array of actions |
| traits | JSONB | Array of traits/abilities |
| data | JSONB | Full 5etools JSON data |

#### `spells`
All spells with metadata.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| name | VARCHAR(255) | Spell name |
| source | VARCHAR(50) | Sourcebook abbreviation |
| level | INTEGER | Spell level (0-9) |
| school | VARCHAR(10) | Evocation, Conjuration, etc. |
| casting_time | VARCHAR(100) | Action, bonus action, etc. |
| range | VARCHAR(100) | Range in feet |
| components | JSONB | V, S, M components |
| duration | VARCHAR(100) | Instantaneous, concentration, etc. |
| description | TEXT | Spell description |
| higher_levels | TEXT | At Higher Levels text |
| data | JSONB | Full 5etools JSON data |

### Lookup Tables

- `item_types` - Item type codes and names
- `item_properties` - Weapon/armor properties (Heavy, Finesse, etc.)
- `damage_types` - All damage types
- `schools` - Magic schools
- `sizes` - Creature sizes
- `alignments` - Alignment options

## Example Queries

### Find all magic swords

```sql
SELECT name, rarity, value/100 as gold_cost
FROM items
WHERE name ILIKE '%sword%'
  AND rarity != 'none'
ORDER BY rarity, name;
```

### Get monsters for a CR 5 encounter

```sql
SELECT name, type, ac, hp_avg, cr
FROM monsters
WHERE cr IN ('4', '5', '6')
ORDER BY cr, name;
```

### Find all fire damage spells

```sql
SELECT name, level, school
FROM spells
WHERE data->'damageInflict' @> '["fire"]'
ORDER BY level, name;
```

### List all martial melee weapons

```sql
SELECT name, damage, damage_type, properties
FROM items
WHERE type = 'M'
  AND data->>'weaponCategory' = 'martial'
ORDER BY name;
```

## Updating Data

When a new version of 5etools is released:

```bash
# Download new version
wget https://github.com/5etools-mirror-3/5etools-src/archive/refs/tags/vX.X.X.tar.gz -O 5etools.tar.gz
tar -xzf 5etools.tar.gz

# Drop and recreate database
psql -U dnd_user -d postgres -c "DROP DATABASE dnd_reference;"
psql -U dnd_user -d postgres -c "CREATE DATABASE dnd_reference;"

# Re-import
python import_all.py
```

## Troubleshooting

### "psycopg2" installation fails

```bash
# On Ubuntu/Debian
sudo apt-get install python3-dev libpq-dev

# On macOS
brew install postgresql

# Then reinstall
pip install psycopg2-binary
```

### Permission denied when creating database

Make sure your PostgreSQL user has `CREATEDB` permission:

```sql
ALTER USER dnd_user CREATEDB;
```

### Import is very slow

- Ensure PostgreSQL has adequate memory (`shared_buffers` in `postgresql.conf`)
- Run imports with indexes created AFTER data insertion (modify scripts)
- Use an SSD for the database storage

## Data Source & Legal

### Data Source

All data is sourced from [5etools](https://5e.tools/), specifically the [5etools-src](https://github.com/5etools-mirror-3/5etools-src) repository, which aggregates official D&D 5th Edition content.

### Legal Notice

Dungeons & Dragons, D&D, and all related content are owned by Wizards of the Coast LLC. This project is not affiliated with, endorsed, sponsored, or specifically approved by Wizards of the Coast.

This tool is for personal use and development purposes. Users are responsible for ensuring their use complies with Wizards of the Coast's [Fan Content Policy](https://company.wizards.com/en/legal/fancontentpolicy) and applicable laws.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Format code
black .
```

## Support

- 🐛 **Bug reports:** [Open an issue](https://github.com/christabone/5etools-to-postgres/issues)
- 💡 **Feature requests:** [Open an issue](https://github.com/christabone/5etools-to-postgres/issues)
- 💬 **Questions:** [Discussions](https://github.com/christabone/5etools-to-postgres/discussions)

## Acknowledgments

- [5etools](https://5e.tools/) - For maintaining comprehensive D&D data
- [5etools-src](https://github.com/5etools-mirror-3/5etools-src) - Data source repository
- All contributors to the D&D community tools ecosystem

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Happy adventuring! 🎲**
