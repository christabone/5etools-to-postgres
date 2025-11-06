# Import Plan - Phase 2

## Overview

This document outlines the complete import strategy for loading cleaned 5etools data into PostgreSQL.

**Current Status**: Phase 2 in progress - Controlled vocabulary complete ✅

---

## Import Order (Critical!)

Imports must follow this order due to foreign key dependencies:

```
1. Controlled Vocabulary (lookup tables) ✅ COMPLETE
   ↓
2. Core Entities (items, monsters, spells)
   ↓
3. Junction Tables (properties, alignments, etc.)
   ↓
4. Extracted Relationships (conditions, damage, cross-refs)
```

---

## Phase 2.1: Controlled Vocabulary Import ✅

**Status**: COMPLETE
**File**: `import_controlled_vocab.sql`
**Records Imported**: 223

### How to Run
```bash
sudo -u postgres psql -d dnd5e_reference -f import_controlled_vocab.sql
```

### Tables Populated
| Table | Records | Source |
|-------|---------|--------|
| sources | 126 | analysis/controlled_vocab.json |
| item_rarities | 10 | Hardcoded D&D rules |
| damage_types | 13 | Hardcoded D&D rules |
| condition_types | 15 | Hardcoded D&D rules |
| creature_types | 14 | Hardcoded D&D rules |
| creature_sizes | 6 | Hardcoded D&D rules |
| spell_schools | 8 | Hardcoded D&D rules |
| alignment_values | 7 | Hardcoded D&D rules |
| skills | 18 | Hardcoded D&D rules |
| attack_types | 6 | Populated via schema.sql |

**Note**: `item_types` and `item_properties` will be populated dynamically during entity import as they require extracting from the actual data files.

### Re-run Safety
✅ All inserts use `ON CONFLICT DO NOTHING` - safe to re-run
✅ No dependencies - can run independently
✅ Idempotent - running multiple times produces same result

---

## Phase 2.2: Core Entity Import (TODO)

**Status**: NOT STARTED
**Estimated Records**: 8,104 entities (2,722 items + 4,445 monsters + 937 spells)

### Import Scripts to Create

#### 1. `import_items.py`
**Input**: `cleaned_data/items_extracted.json`
**Output**: Populates `items` table + junction tables

**Process**:
1. Load all items from JSON
2. For each item:
   - Resolve `source` code → `source_id` (lookup in sources table)
   - Resolve `type` code → `type_id` (create in item_types if new)
   - Resolve `rarity` → `rarity_id` (lookup in item_rarities table)
   - Extract normalized fields (name, value_cp, weight_lbs, ac, etc.)
   - Store full original JSON in `data` JSONB column
   - Generate `search_vector` for full-text search
3. Insert into `items` table
4. Insert properties into `item_item_properties` junction table
5. Handle weapon/armor specific fields

**Key Challenges**:
- Type codes may have source suffixes (e.g., "M|XPHB") - need to handle
- $ prefix indicates generic variant - strip and set flag
- Bonus values already normalized to integers
- Damage type codes (B, P, S) need expansion to full names

**Foreign Key Lookups**:
```python
# Example pseudo-code
source_id = lookup_or_create('sources', 'code', item['source'])
type_id = lookup_or_create('item_types', 'code', clean_type_code(item['type']))
rarity_id = lookup('item_rarities', 'name', item.get('rarity', 'none'))
```

---

#### 2. `import_monsters.py`
**Input**: `cleaned_data/monsters_extracted.json`
**Output**: Populates `monsters` table + junction tables

**Process**:
1. Load all monsters from JSON
2. For each monster:
   - Resolve foreign keys (source_id, type_id, size_id)
   - Extract normalized fields (CR, HP, AC, ability scores, speeds, etc.)
   - Store full original JSON in `data` column
   - Generate `search_vector`
3. Insert into `monsters` table
4. Insert alignments into `monster_alignments` junction table
5. Insert resistances/immunities/vulnerabilities into respective tables
6. Insert condition immunities

**Key Challenges**:
- CR can be fractional (0.125, 0.25, 0.5, 1, 2, etc.)
- Alignment is array of codes that need to be inserted as multiple rows
- Speed can have multiple types (walk, fly, swim, climb, burrow)
- HP formula parsing if needed

---

#### 3. `import_spells.py`
**Input**: `cleaned_data/spells_extracted.json`
**Output**: Populates `spells` table

**Process**:
1. Load all spells from JSON
2. For each spell:
   - Resolve foreign keys (source_id, school_id)
   - Extract normalized fields (level, casting time, range, duration, etc.)
   - Parse boolean flags (concentration, ritual, verbal, somatic, material)
   - Store full original JSON in `data` column
   - Generate `search_vector`
3. Insert into `spells` table

**Key Challenges**:
- Spell level 0 = cantrip
- Casting time parsing (action, bonus action, reaction, minutes, hours)
- Range parsing (self, touch, feet, miles, special)
- Duration parsing (instantaneous, concentration, minutes, hours, days)

---

### Database Connection Strategy

All Python import scripts will use peer authentication as postgres user:

```python
import psycopg2

DB_PARAMS = {
    'dbname': 'dnd5e_reference',
}

# Run with: sudo -u postgres python3 import_items.py
conn = psycopg2.connect(**DB_PARAMS)
```

### Error Handling Strategy

All import scripts should:
1. **Use transactions** - Rollback on error
2. **Batch inserts** - Use `execute_values()` for performance
3. **Progress reporting** - Print every 100 records
4. **Validation** - Check foreign key references exist
5. **Logging** - Log all warnings/errors to file
6. **Idempotency** - Support `--skip-existing` flag to avoid duplicates

**Example structure**:
```python
try:
    conn = psycopg2.connect(**DB_PARAMS)

    with conn.cursor() as cur:
        # Import items
        for i, item in enumerate(items, 1):
            try:
                import_item(cur, item)
                if i % 100 == 0:
                    print(f"Processed {i}/{len(items)} items...")
            except Exception as e:
                print(f"ERROR on item {item['name']}: {e}")
                # Continue or rollback based on --strict flag

    conn.commit()
    print(f"✅ Successfully imported {len(items)} items")

except Exception as e:
    conn.rollback()
    print(f"❌ Import failed: {e}")
    raise
finally:
    conn.close()
```

---

## Phase 2.3: Extracted Relationship Import (TODO)

**Status**: NOT STARTED
**Estimated Records**: 26,619 relationships

### Import Script to Create

#### `import_extracted_data.py`
**Inputs**:
- `extraction_data/conditions_extracted.json` (6,113 records)
- `extraction_data/damage_extracted.json` (5,618 records)
- `extraction_data/cross_refs_extracted.json` (14,769 records)

**Output**: Populates relationship tables

**Process**:

1. **Import Conditions** (3 tables)
   - For each condition reference:
     - Lookup entity by name+source → get ID
     - Lookup condition by name → get condition_id
     - Insert into appropriate table (item_conditions, monster_action_conditions, spell_conditions)
   - Tables populated: item_conditions (508), monster_action_conditions (5,074), spell_conditions (531)

2. **Import Damage** (3 tables)
   - For each damage record:
     - Lookup entity by name+source → get ID
     - Lookup damage type by name → get damage_type_id
     - Lookup attack type by code → get attack_type_id
     - Insert into appropriate table (monster_attacks, spell_damage, item_damage)
   - Tables populated: monster_attacks (4,364), spell_damage (520), item_damage (734)

3. **Import Cross-References** (9 tables)
   - For each cross-reference:
     - Lookup both entities by name+source → get IDs
     - Insert into appropriate table based on relationship type
   - Tables: item_related_items (564), item_spells (1,157), item_creatures (401),
             monster_items (1,086), monster_spells (10,979), monster_creatures (321),
             spell_items (13), spell_related_spells (143), spell_summons (105)

**Key Challenge**: Name resolution
- Extraction files have entity names, not IDs
- Need to lookup: `SELECT id FROM items WHERE name = ? AND source_id = (SELECT id FROM sources WHERE code = ?)`
- Handle missing references gracefully (log warning, skip record)
- Some entities may not have been imported (e.g., UA content)

**Example name resolution**:
```python
def resolve_entity_id(conn, table, name, source_code):
    """Resolve entity name + source to database ID."""
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT id FROM {table}
            WHERE name = %s
            AND source_id = (SELECT id FROM sources WHERE code = %s)
        """, (name, source_code))
        result = cur.fetchone()
        if result:
            return result[0]
        else:
            print(f"WARNING: {table} not found: {name} ({source_code})")
            return None
```

---

## Phase 2.4: Post-Import Validation (TODO)

**Status**: NOT STARTED

### Validation Script to Create

#### `validate_import.py`
**Purpose**: Verify data integrity after import

**Checks**:
1. **Record counts match expected**
   - Items: 2,722
   - Monsters: 4,445
   - Spells: 937
   - Conditions: 6,113
   - Damage: 5,618
   - Cross-refs: 14,769

2. **Foreign key integrity**
   - No orphaned records
   - All foreign keys resolve

3. **Search vectors generated**
   - All items/monsters/spells have non-null search_vector

4. **JSONB data preserved**
   - All records have non-empty data column
   - JSON is valid and parseable

5. **Normalized fields populated**
   - Items have value_cp, weight_lbs
   - Monsters have CR, HP, AC
   - Spells have level, school_id

6. **Sample queries**
   - "Find all legendary magic items" - should return results
   - "Find CR 10-15 dragons" - should return results
   - "Find 3rd level evocation spells" - should return results

**Output**: Validation report with ✅/❌ for each check

---

## Phase 2.5: Index Optimization (TODO)

**Status**: NOT STARTED

After data import, optimize indexes:

```sql
-- Rebuild all indexes
REINDEX DATABASE dnd5e_reference;

-- Update statistics
ANALYZE;

-- Vacuum to reclaim space
VACUUM ANALYZE;
```

**Rationale**: Indexes created before data load may be suboptimal. Rebuilding after import ensures optimal structure.

---

## Master Import Script (TODO)

**File**: `import_all.sh`

```bash
#!/bin/bash
# Master import script - runs all imports in order

set -e  # Exit on error

echo "================================================================================"
echo "5ETOOLS TO POSTGRES - MASTER IMPORT"
echo "================================================================================"

# Phase 2.1: Controlled Vocabulary
echo ""
echo "Phase 2.1: Importing controlled vocabulary..."
sudo -u postgres psql -d dnd5e_reference -f import_controlled_vocab.sql

# Phase 2.2: Core Entities
echo ""
echo "Phase 2.2: Importing core entities..."
sudo -u postgres python3 import_items.py
sudo -u postgres python3 import_monsters.py
sudo -u postgres python3 import_spells.py

# Phase 2.3: Extracted Relationships
echo ""
echo "Phase 2.3: Importing extracted relationships..."
sudo -u postgres python3 import_extracted_data.py

# Phase 2.4: Validation
echo ""
echo "Phase 2.4: Running validation..."
python3 validate_import.py

# Phase 2.5: Index Optimization
echo ""
echo "Phase 2.5: Optimizing indexes..."
sudo -u postgres psql -d dnd5e_reference -c "REINDEX DATABASE dnd5e_reference;"
sudo -u postgres psql -d dnd5e_reference -c "ANALYZE;"

echo ""
echo "================================================================================"
echo "✅ IMPORT COMPLETE"
echo "================================================================================"
echo ""
echo "Database: dnd5e_reference"
echo "Connection: psql -U dndbot -d dnd5e_reference"
echo ""
echo "Next steps:"
echo "  - Review validation report"
echo "  - Test sample queries"
echo "  - Document any warnings/errors"
echo ""
```

---

## Re-run Strategy

### Full Pipeline Re-run
To completely reset and re-import all data:

```bash
# 1. Drop and recreate database
sudo -u postgres psql -c "DROP DATABASE dnd5e_reference;"
sudo -u postgres psql -c "CREATE DATABASE dnd5e_reference OWNER dnd5e_user;"

# 2. Grant permissions
sudo -u postgres psql -d dnd5e_reference -c "GRANT CONNECT ON DATABASE dnd5e_reference TO dndbot; GRANT USAGE ON SCHEMA public TO dndbot; ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT SELECT ON TABLES TO dndbot;"

# 3. Load schema
sudo -u postgres psql -d dnd5e_reference -f schema.sql

# 4. Run master import
./import_all.sh
```

### Partial Re-run
To re-import specific entities without dropping database:

```bash
# Delete specific entity type
sudo -u postgres psql -d dnd5e_reference -c "TRUNCATE items CASCADE;"

# Re-import
sudo -u postgres python3 import_items.py
```

⚠️ **Warning**: `TRUNCATE CASCADE` will delete all related records in junction tables!

---

## Performance Considerations

### Expected Import Times
Based on record counts:
- Controlled vocab: <1 second (223 records)
- Items: ~5-10 seconds (2,722 records)
- Monsters: ~10-20 seconds (4,445 records)
- Spells: ~2-5 seconds (937 records)
- Relationships: ~30-60 seconds (26,619 records)
- Index rebuild: ~10-30 seconds
- **Total: ~2-3 minutes**

### Optimization Techniques
1. **Batch inserts** - Use `execute_values()` instead of individual inserts
2. **Disable triggers** - If needed for performance (currently none defined)
3. **Create indexes after import** - Already in schema, but could move to post-import
4. **Connection pooling** - Not needed for one-time import

---

## Troubleshooting

### Common Issues

#### 1. Permission Denied
**Error**: `psycopg2.OperationalError: FATAL: Peer authentication failed`

**Solution**: Run as postgres user:
```bash
sudo -u postgres python3 import_items.py
```

#### 2. Foreign Key Violation
**Error**: `psycopg2.errors.ForeignKeyViolation: insert or update on table "items" violates foreign key constraint`

**Cause**: Referenced entity doesn't exist (e.g., source_id not in sources table)

**Solution**:
- Check controlled vocabulary was imported first
- Verify lookup is returning valid ID
- Add error handling to skip invalid references

#### 3. Duplicate Key Violation
**Error**: `psycopg2.errors.UniqueViolation: duplicate key value violates unique constraint`

**Cause**: Trying to import same entity twice

**Solution**:
- Use `ON CONFLICT DO NOTHING` or `ON CONFLICT UPDATE`
- Run with `--skip-existing` flag
- Truncate table before re-import

#### 4. JSON Decode Error
**Error**: `json.decoder.JSONDecodeError: Expecting value`

**Cause**: Malformed JSON in source files

**Solution**:
- Validate JSON files: `python3 -m json.tool file.json > /dev/null`
- Check file encoding (should be UTF-8)
- Look for truncated files

---

## File Checklist

### Completed ✅
- [x] `schema.sql` - Database schema with all tables and indexes
- [x] `import_controlled_vocab.sql` - Controlled vocabulary import
- [x] `INDEX_PLAN.md` - Index strategy documentation
- [x] `IMPORT_PLAN.md` - This document

### To Create 🔲
- [ ] `import_items.py` - Items import script
- [ ] `import_monsters.py` - Monsters import script
- [ ] `import_spells.py` - Spells import script
- [ ] `import_extracted_data.py` - Relationships import script
- [ ] `validate_import.py` - Post-import validation
- [ ] `import_all.sh` - Master import orchestration
- [ ] `db_helpers.py` - Shared utility functions (lookups, connection, etc.)

---

## Next Steps

1. ✅ **Review and commit import plan** ← YOU ARE HERE
2. Create `db_helpers.py` with shared functions
3. Create `import_items.py`
4. Test items import with sample data
5. Create `import_monsters.py`
6. Create `import_spells.py`
7. Create `import_extracted_data.py`
8. Create `validate_import.py`
9. Create `import_all.sh`
10. Run full import and validate
11. Document any issues and update plan
12. Commit final working import pipeline

---

**Document Version**: 1.0
**Last Updated**: 2025-11-06
**Status**: Controlled vocab complete, entity imports TODO
