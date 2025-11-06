# 5etools-to-postgres Implementation Plan

## Project Overview
Import D&D 5e data from 5etools JSON files into a PostgreSQL database for use by other applications.

## Project Philosophy: Data-Driven Development
**DO NOT write import code until we understand the actual data structure.**

This project follows a data-first approach:
1. **Analyze** - Understand the actual JSON structure
2. **Document** - Create comprehensive data maps
3. **Design** - Build schema based on real data
4. **Implement** - Write imports with confidence
5. **Validate** - Verify against known edge cases

## Current Status: 📐 Phase 1 - Schema Design

### 5etools Data Location
- **Path**: `/home/ctabone/dnd_bot/5etools-src-2.15.0/`
- **Version**: v2.15.0
- **Key Data Files**:
  - `data/items-base.json` - Base items
  - `data/items.json` - All items including magic items
  - `data/bestiary/*.json` - Monster stat blocks
  - `data/spells/*.json` - Spell definitions
  - `data/class/*.json` - Class features
  - `data/races.json` - Race data
  - `data/backgrounds.json` - Background data

## Phase 0: Data Structure Analysis

### Objectives
Before writing ANY import code, we need to:
1. Understand actual field names and data types in the JSON
2. Identify all edge cases and data variations
3. Map JSON fields to potential database columns
4. Discover nested structures and arrays
5. Find all controlled vocabulary values (enums)
6. Document data relationships

### Analysis Scripts to Create

#### 1. `analyze_json_structure.py`
**Purpose**: Deep inspection of JSON file structure

**Features**:
- Recursively walk through JSON files
- Identify all unique keys/fields
- Track data types for each field
- Count occurrences of each field
- Find optional vs required fields
- Detect nested structures
- Sample values for each field

**Output**: `analysis/structure_report.json`

#### 2. `analyze_field_types.py`
**Purpose**: Understand data type variations

**Features**:
- For each field, what types appear? (string, int, dict, array, etc.)
- Identify polymorphic fields (fields that can be multiple types)
- Find edge cases (null, empty arrays, etc.)
- Document array element types

**Output**: `analysis/field_types_report.json`

#### 3. `analyze_controlled_vocab.py`
**Purpose**: Extract all enumerated values

**Features**:
- Find fields with limited value sets
- Extract all unique values for enum-like fields
- Count frequency of each value
- Identify candidate lookup tables

**Output**: `analysis/controlled_vocab.json`

Example output:
```json
{
  "sources": {
    "count": 107,
    "values": ["PHB", "MM", "DMG", "XGE", ...]
  },
  "item_types": {
    "count": 45,
    "values": ["M", "R", "A", "LA", ...]
  }
}
```

#### 4. `analyze_relationships.py`
**Purpose**: Discover data relationships

**Features**:
- Identify foreign key relationships
- Find many-to-many relationships
- Map parent-child structures
- Document cross-references

**Output**: `analysis/relationships.json`

#### 5. `sample_records.py`
**Purpose**: Extract representative samples

**Features**:
- Save 10 simple examples
- Save 10 complex examples
- Save 10 edge case examples
- Pretty print for human review

**Output**: `analysis/samples/*.json`

### Analysis Deliverables

After running all analysis scripts, we should have:

```
analysis/
├── structure_report.json          # Complete field inventory
├── field_types_report.json        # Type information for every field
├── controlled_vocab.json          # All enum values
├── relationships.json             # Discovered relationships
├── samples/
│   ├── items_simple.json         # 10 simple items
│   ├── items_complex.json        # 10 complex items
│   ├── items_edge_cases.json     # 10 edge cases
│   ├── monsters_simple.json
│   ├── monsters_complex.json
│   ├── monsters_edge_cases.json
│   ├── spells_simple.json
│   ├── spells_complex.json
│   └── spells_edge_cases.json
└── SUMMARY.md                     # Human-readable summary
```

### Success Criteria for Phase 0

Before moving to Phase 0.5 (Data Cleaning), we must:
- ✅ Run all 5 analysis scripts
- ✅ Review all generated reports
- ✅ Manually inspect sample records
- ✅ Document surprising findings
- ✅ Create field mapping tables
- ✅ Identify all edge cases

**Status**: ✅ COMPLETE

---

## Phase 0.5: Data Cleaning & Normalization

**Prerequisites**: Complete Phase 0 ✅

### Philosophy
Don't fight messy data in import scripts. Clean it first, import it easily.

**Pipeline**: `Raw 5etools JSON → Cleaning Scripts → Normalized JSON → Import Scripts → Database`

### Objectives
1. Eliminate all polymorphic fields (normalize to single structure)
2. Apply consistent data types
3. Fill in missing/default values
4. Validate foreign key references exist
5. Create reproducible, versioned cleaned data

### Cleaning Scripts to Create

#### 1. `clean_items.py`
**Purpose**: Normalize item data structure

**Transformations**:
- ✅ Convert `value` to always be int (copper pieces)
- ✅ Convert `weight` to always be float
- ✅ Flatten `property` array - convert dict entries to strings
- ✅ Default missing `rarity` to "none"
- ✅ Parse `range` into consistent `{normal: int, long: int}` format
- ✅ Normalize `damage` types
- ✅ Extract `mastery` to always be array of strings

**Input**: `data/items-base.json`, `data/items.json`
**Output**: `cleaned_data/items.json`

**Example Transformation**:
```python
# BEFORE:
{
  "value": 5,              # or {"gp": 5} or missing
  "weight": 2,             # or 2.5 or missing
  "property": ["F", {"uid": "2H|XPHB", "note": "unless mounted"}]
}

# AFTER:
{
  "value": 500,            # always copper (int)
  "weight": 2.0,           # always float
  "property": ["F", "2H"], # always simple string array
  "property_notes": {"2H": "unless mounted"}  # notes extracted
}
```

#### 2. `clean_monsters.py`
**Purpose**: Normalize monster data structure

**Transformations**:
- ✅ Normalize `type`: Always `{"type": "...", "tags": [...]}`
- ✅ Normalize `ac`: Always array of `[{"ac": int, "from": [...]}]`
- ✅ Normalize `alignment`: Always array of abbreviation strings `["L", "G"]`
- ✅ Normalize `speed`: Always dict with all movement types (null if not present)
- ✅ Convert `cr` from fraction strings to decimal numbers
- ✅ Parse `hp` into `{average: int, formula: str}`
- ✅ Normalize `resist`, `immune`, `vulnerable` to simple string arrays
- ✅ Extract `size` as single character (take first if array)

**Input**: `data/bestiary/*.json`
**Output**: `cleaned_data/monsters.json`

**Example Transformation**:
```python
# BEFORE:
{
  "type": "humanoid"  # OR {"type": "humanoid", "tags": ["orc"]}
  "ac": 13            # OR [{"ac": 13, "from": ["hide armor"]}]
  "alignment": ["C", "E"]  # OR "any alignment" OR {"alignment": ["L", "G"]}
  "cr": "1/2"         # string fraction
}

# AFTER:
{
  "type": {"type": "humanoid", "tags": []},  # always this structure
  "ac": [{"ac": 13, "from": null}],          # always array of dicts
  "alignment": ["C", "E"],                    # always simple string array
  "cr": 0.5                                   # always decimal number
}
```

#### 3. `clean_spells.py`
**Purpose**: Normalize spell data structure

**Transformations**:
- ✅ Normalize `time`: Always `{number: int, unit: str}`
- ✅ Normalize `range`: Always `{type: str, value: int, unit: str}`
- ✅ Normalize `duration`: Always `{type: str, value: int, unit: str, concentration: bool}`
- ✅ Flatten `components`: `{v: bool, s: bool, m: bool, m_text: str}`
- ✅ Extract `damageInflict` array for damage types
- ✅ Flatten `entries` to simple text string (for full-text search)

**Input**: `data/spells/*.json`
**Output**: `cleaned_data/spells.json`

**Example Transformation**:
```python
# BEFORE:
{
  "time": [{"number": 1, "unit": "action"}],
  "range": {"type": "point", "distance": {"type": "feet", "amount": 150}},
  "components": {"v": true, "s": true, "m": "bat guano and sulfur"}
}

# AFTER:
{
  "time": {"number": 1, "unit": "action"},
  "range": {"type": "point", "value": 150, "unit": "feet"},
  "components": {"v": true, "s": true, "m": true, "m_text": "bat guano and sulfur"}
}
```

#### 4. `validate_cleaned.py`
**Purpose**: Verify cleaning was successful

**Validations**:
- ✅ No polymorphic fields remain (all fields have single type)
- ✅ All foreign key values exist in controlled vocab
- ✅ No null values in required fields
- ✅ All numeric fields are correct type (int vs float)
- ✅ All arrays contain expected element types
- ✅ Generate validation report with pass/fail counts

**Output**: `cleaned_data/VALIDATION_REPORT.md`

#### 5. `clean_all.py`
**Purpose**: Master script to run all cleaning

**Features**:
- Run all 3 cleaning scripts in order
- Track timing and statistics
- Generate summary report
- Compare cleaned vs raw record counts

**Output**: `cleaned_data/CLEANING_REPORT.md`

### Deliverables

After Phase 0.5, we should have:

```
cleaned_data/
├── items.json                  # All items (2,722 records)
├── monsters.json               # All monsters (3,000+ records)
├── spells.json                 # All spells (1,000+ records)
├── CLEANING_REPORT.md          # Summary of transformations
└── VALIDATION_REPORT.md        # Validation results
```

### Success Criteria

Before moving to Phase 1 (Schema Design):
- ✅ Run all 4 cleaning scripts
- ✅ Validation report shows 100% pass rate (0 polymorphic fields!)
- ✅ Manually inspect sample cleaned records
- ✅ No polymorphic fields remain
- ✅ All FKs validated

**Status**: ✅ COMPLETE

### Benefits

1. **Simple Import Scripts**: No complex type checking
2. **Guaranteed Consistency**: Data structure is predictable
3. **Easy Updates**: Re-run cleaning when 5etools updates
4. **Transparent**: All transformations documented
5. **Testable**: Validation ensures quality

---

## Phase 1: Schema Design

**Prerequisites**: Complete Phase 0 ✅, Complete Phase 0.5 ✅

### Philosophy
Design a schema that balances normalization with practical querying needs. Use JSONB for complex nested structures while normalizing frequently-queried fields.

### Objectives
1. Create normalized tables for core entities (items, monsters, spells)
2. Design controlled vocabulary (lookup) tables
3. Create junction tables for many-to-many relationships
4. Determine which fields to normalize vs store in JSONB
5. Define indexes for performance
6. Create helpful views for common queries

### Schema Design Principles

1. **Normalize Core Fields**: Frequently searched/filtered fields get columns
2. **JSONB for Flexibility**: Complex nested data stays in JSONB
3. **Controlled Vocabulary Tables**: Enums become lookup tables with referential integrity
4. **Many-to-Many via Junction Tables**: Properties, tags, damage types, etc.
5. **Preserve Original**: Store complete original JSON for data loss prevention

### Tables to Create

#### Controlled Vocabulary Tables
These enforce referential integrity and provide canonical values:

1. **sources** - PHB, MM, XGE, etc.
   ```sql
   CREATE TABLE sources (
     id SERIAL PRIMARY KEY,
     code VARCHAR(20) UNIQUE NOT NULL,  -- "PHB", "MM"
     name TEXT NOT NULL,                 -- "Player's Handbook"
     type VARCHAR(20),                   -- "core", "supplement"
     published_date DATE
   );
   ```

2. **item_types** - M (melee), R (ranged), A (armor), etc.
3. **item_rarities** - common, uncommon, rare, very rare, legendary, artifact
4. **damage_types** - fire, cold, slashing, piercing, etc.
5. **creature_types** - humanoid, beast, dragon, etc.
6. **creature_sizes** - T, S, M, L, H, G
7. **alignment_values** - L, N, C, G, E, U, A
8. **spell_schools** - A (abjuration), C (conjuration), etc.
9. **condition_types** - blinded, charmed, deafened, etc.
10. **skills** - Acrobatics, Arcana, etc.

#### Core Entity Tables

##### Items Table
```sql
CREATE TABLE items (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  source_id INTEGER REFERENCES sources(id),
  type_id INTEGER REFERENCES item_types(id),
  rarity_id INTEGER REFERENCES item_rarities(id),

  -- Normalized fields (frequently queried)
  value_cp INTEGER DEFAULT 0,           -- Value in copper pieces
  weight_lbs NUMERIC(10,2) DEFAULT 0,   -- Weight in pounds
  requires_attunement BOOLEAN DEFAULT false,
  attunement_description TEXT,

  -- Weapon/armor specific
  ac INTEGER,                            -- For armor
  strength_requirement INTEGER,          -- Strength req for armor

  -- Normalized nested structures
  range_normal INTEGER,                  -- Normal range in feet
  range_long INTEGER,                    -- Long range in feet

  -- Full original JSON (for complex fields)
  data JSONB NOT NULL,

  -- Metadata
  source_file TEXT,                      -- Which file it came from
  created_at TIMESTAMP DEFAULT NOW(),

  -- Search
  search_vector tsvector
);

CREATE INDEX idx_items_name ON items USING gin(to_tsvector('english', name));
CREATE INDEX idx_items_data ON items USING gin(data);
CREATE INDEX idx_items_search ON items USING gin(search_vector);
```

##### Monsters Table
```sql
CREATE TABLE monsters (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  source_id INTEGER REFERENCES sources(id),
  type_id INTEGER REFERENCES creature_types(id),
  size_id INTEGER REFERENCES creature_sizes(id),

  -- Normalized stats
  cr NUMERIC(5,2) NOT NULL,              -- Challenge Rating (0.125 to 30)
  hp_average INTEGER NOT NULL,
  hp_formula TEXT,
  ac_primary INTEGER NOT NULL,           -- Primary AC value

  -- Speeds
  speed_walk INTEGER DEFAULT 30,
  speed_fly INTEGER DEFAULT 0,
  speed_swim INTEGER DEFAULT 0,
  speed_climb INTEGER DEFAULT 0,
  speed_burrow INTEGER DEFAULT 0,

  -- Ability scores
  str INTEGER NOT NULL,
  dex INTEGER NOT NULL,
  con INTEGER NOT NULL,
  int INTEGER NOT NULL,
  wis INTEGER NOT NULL,
  cha INTEGER NOT NULL,

  -- Senses
  passive_perception INTEGER DEFAULT 10,

  -- Full original JSON
  data JSONB NOT NULL,

  -- Metadata
  source_file TEXT,
  created_at TIMESTAMP DEFAULT NOW(),

  -- Search
  search_vector tsvector
);

CREATE INDEX idx_monsters_name ON monsters USING gin(to_tsvector('english', name));
CREATE INDEX idx_monsters_cr ON monsters(cr);
CREATE INDEX idx_monsters_data ON monsters USING gin(data);
```

##### Spells Table
```sql
CREATE TABLE spells (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  source_id INTEGER REFERENCES sources(id),
  school_id INTEGER REFERENCES spell_schools(id),

  -- Normalized fields
  level INTEGER NOT NULL,                -- 0 (cantrip) to 9
  casting_time_number INTEGER,
  casting_time_unit TEXT,                -- "action", "bonus", "minute"

  range_type TEXT,                       -- "self", "touch", "point"
  range_value INTEGER,                   -- Distance in feet

  duration_type TEXT,                    -- "instant", "timed", "concentration"
  duration_value INTEGER,
  duration_unit TEXT,                    -- "minute", "hour", "round"
  requires_concentration BOOLEAN DEFAULT false,

  -- Components
  component_v BOOLEAN DEFAULT false,
  component_s BOOLEAN DEFAULT false,
  component_m BOOLEAN DEFAULT false,
  component_m_text TEXT,

  -- Ritual
  is_ritual BOOLEAN DEFAULT false,

  -- Full original JSON
  data JSONB NOT NULL,

  -- Metadata
  source_file TEXT,
  created_at TIMESTAMP DEFAULT NOW(),

  -- Search
  search_vector tsvector
);

CREATE INDEX idx_spells_name ON spells USING gin(to_tsvector('english', name));
CREATE INDEX idx_spells_level ON spells(level);
CREATE INDEX idx_spells_school ON spells(school_id);
CREATE INDEX idx_spells_data ON spells USING gin(data);
```

#### Junction Tables (Many-to-Many)

##### Item Properties
```sql
CREATE TABLE item_properties (
  id SERIAL PRIMARY KEY,
  code VARCHAR(10) UNIQUE NOT NULL,     -- "F", "2H", "V"
  name TEXT NOT NULL,                    -- "Finesse", "Two-Handed"
  description TEXT
);

CREATE TABLE item_item_properties (
  item_id INTEGER REFERENCES items(id) ON DELETE CASCADE,
  property_id INTEGER REFERENCES item_properties(id),
  note TEXT,                             -- Optional notes like "unless mounted"
  PRIMARY KEY (item_id, property_id)
);
```

##### Monster Alignments
```sql
CREATE TABLE monster_alignments (
  monster_id INTEGER REFERENCES monsters(id) ON DELETE CASCADE,
  alignment_id INTEGER REFERENCES alignment_values(id),
  PRIMARY KEY (monster_id, alignment_id)
);
```

##### Monster Damage Modifiers
```sql
CREATE TABLE monster_resistances (
  monster_id INTEGER REFERENCES monsters(id) ON DELETE CASCADE,
  damage_type_id INTEGER REFERENCES damage_types(id),
  PRIMARY KEY (monster_id, damage_type_id)
);

CREATE TABLE monster_immunities (
  monster_id INTEGER REFERENCES monsters(id) ON DELETE CASCADE,
  damage_type_id INTEGER REFERENCES damage_types(id),
  PRIMARY KEY (monster_id, damage_type_id)
);

CREATE TABLE monster_vulnerabilities (
  monster_id INTEGER REFERENCES monsters(id) ON DELETE CASCADE,
  damage_type_id INTEGER REFERENCES damage_types(id),
  PRIMARY KEY (monster_id, damage_type_id)
);
```

##### Spell Classes
```sql
CREATE TABLE classes (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL
);

CREATE TABLE spell_classes (
  spell_id INTEGER REFERENCES spells(id) ON DELETE CASCADE,
  class_id INTEGER REFERENCES classes(id),
  PRIMARY KEY (spell_id, class_id)
);
```

### Views for Common Queries

#### Complete Item View
```sql
CREATE VIEW v_items_complete AS
SELECT
  i.id,
  i.name,
  s.code as source,
  it.name as type,
  r.name as rarity,
  i.value_cp,
  i.weight_lbs,
  i.requires_attunement,
  array_agg(DISTINCT ip.code) as properties,
  i.data
FROM items i
LEFT JOIN sources s ON i.source_id = s.id
LEFT JOIN item_types it ON i.type_id = it.id
LEFT JOIN item_rarities r ON i.rarity_id = r.id
LEFT JOIN item_item_properties iip ON i.id = iip.item_id
LEFT JOIN item_properties ip ON iip.property_id = ip.id
GROUP BY i.id, s.code, it.name, r.name;
```

#### Complete Monster View
```sql
CREATE VIEW v_monsters_complete AS
SELECT
  m.id,
  m.name,
  s.code as source,
  ct.name as type,
  cs.name as size,
  m.cr,
  m.hp_average,
  m.ac_primary,
  array_agg(DISTINCT av.code) as alignment,
  array_agg(DISTINCT dt_r.name) FILTER (WHERE dt_r.name IS NOT NULL) as resistances,
  array_agg(DISTINCT dt_i.name) FILTER (WHERE dt_i.name IS NOT NULL) as immunities,
  m.data
FROM monsters m
LEFT JOIN sources s ON m.source_id = s.id
LEFT JOIN creature_types ct ON m.type_id = ct.id
LEFT JOIN creature_sizes cs ON m.size_id = cs.id
LEFT JOIN monster_alignments ma ON m.id = ma.monster_id
LEFT JOIN alignment_values av ON ma.alignment_id = av.id
LEFT JOIN monster_resistances mr ON m.id = mr.monster_id
LEFT JOIN damage_types dt_r ON mr.damage_type_id = dt_r.id
LEFT JOIN monster_immunities mi ON m.id = mi.monster_id
LEFT JOIN damage_types dt_i ON mi.damage_type_id = dt_i.id
GROUP BY m.id, s.code, ct.name, cs.name;
```

### Deliverables

After Phase 1, we should have:

```
schema.sql                      # Complete DDL
schema_diagram.md               # Visual schema documentation
field_mappings.md               # JSON → DB column mappings
```

### Success Criteria

Before moving to Phase 0.6 (Markup Extraction):
- ✅ schema.sql created with all tables
- ✅ All controlled vocabulary tables defined
- ✅ All junction tables for M:M relationships
- ✅ Indexes defined for performance
- ✅ Views created for common queries
- ✅ Schema successfully applies to empty database

**Status**: ✅ COMPLETE

---

## Phase 0.6: Markup Extraction & Advanced Normalization

**Prerequisites**: Complete Phase 0 ✅, Complete Phase 0.5 ✅, Complete Phase 1 ✅

### Philosophy

The cleaned data still contains valuable structured information hidden in text markup and special characters. We must extract this into proper database relationships before import.

### Critical Discovery: 5etools Markup System

Investigation revealed **256,208 special character occurrences** including **189,000+ instances of 5etools markup tags**.

**Markup Format:**
```
{@type name|source|display}
```

**Examples:**
- `{@item longsword|phb}` - Item reference
- `{@creature goblin|mm}` - Monster reference
- `{@condition Charmed|XPHB}` - Condition reference
- `{@spell fireball|phb}` - Spell reference
- `{@damage 2d6}` - Damage expression
- `{@dice 1d20}` - Dice roll
- `{@hit +5}` - Attack bonus
- `{@dc 15}` - Save DC

### Problem: Structured Data Hidden in Text

Currently, this valuable data is buried in JSONB `entries[]` fields as free text. This makes it impossible to:
- Query "all items that inflict the poisoned condition"
- Find "all spells that deal fire damage"
- List "all monsters with attacks dealing 2d6 damage"

**Example of Current Problem:**
```json
{
  "name": "Dagger of Venom",
  "entries": [
    "On a hit, the target takes an extra {@damage 2d10} poison damage and must succeed on a {@dc 15} Constitution saving throw or be {@condition poisoned|XPHB} for 1 minute."
  ]
}
```

**What We Need to Extract:**
- Condition inflicted: "poisoned"
- Damage: 2d10 poison
- Save: DC 15, Constitution

### Investigation Results

#### 1. Markup in KEY FIELDS (CRITICAL BUG!)

**Monster Names Have Markup (880 occurrences):**
```json
"name": "{@creature Aboleth|MM} Spawn"
"name": "Empyrean (Maimed){@note maimed}"
```

This breaks searching! `SELECT * FROM monsters WHERE name = 'Aboleth Spawn'` will fail.

**Must Fix:**
- Strip all `{@...}` markup from `name` fields
- Extract base name and variant to separate columns

#### 2. Parentheses in Names (37k occurrences)

**Item Names:**
- `"Arrow (20)"` - contains quantity
- `"Acid (vial)"` - contains container type
- `"Longsword (+1)"` - contains bonus

**Must Extract:**
- `base_name`: "Arrow"
- `default_quantity`: 20
- `container_type`: "vial"
- `bonus_weapon`: 1

#### 3. Plus Signs (20k occurrences)

**In Bonus Fields:**
```json
"bonusWeapon": "+1"  // Should be integer: 1
"bonusAc": "+2"      // Should be integer: 2
```

**In HP Formulas (keep as-is):**
```json
"hp.formula": "8d10 + 16"  // This is correct
```

#### 4. Dollar Signs (273 occurrences)

**In Item Type:**
```json
"type": "$G"  // Generic variant
"type": "$A"  // Alternate version
"type": "$C"  // Custom/crafted
```

**Must Extract:**
- `is_generic_variant`: true/false
- `type`: "G" (without $)

### Objectives

1. **Clean Key Fields**
   - Remove ALL markup from `name` fields
   - Extract variants to separate columns
   - Parse quantities/containers from parentheses
   - Strip `+` prefix from bonus fields
   - Handle `$` prefix in type codes

2. **Extract Conditions**
   - Parse `{@condition ...}` tags from all text
   - Create junction tables linking items/monsters/spells to conditions
   - Track whether condition is inflicted, granted immunity, etc.

3. **Extract Damage Data**
   - Parse `{@damage ...}` expressions
   - Extract dice, bonus, damage type
   - Create structured damage tables
   - Enable queries like "find all 2d6 fire damage sources"

4. **Extract Cross-References**
   - Parse `{@item ...}`, `{@spell ...}`, `{@creature ...}` tags
   - Build relationship tables
   - Track dependencies (e.g., "Arrows require a bow")

5. **Preserve Display Markup**
   - Keep `{@book ...}`, `{@quickref ...}` in JSONB
   - These are for UI rendering, not data

### Data to Extract

#### HIGH PRIORITY

##### 1. Condition References

**Tables to Create:**
```sql
CREATE TABLE item_conditions (
  item_id INTEGER REFERENCES items(id),
  condition_id INTEGER REFERENCES condition_types(id),
  inflicts BOOLEAN DEFAULT true,  -- vs grants immunity
  save_dc INTEGER,
  save_ability VARCHAR(10),  -- "Constitution", "Wisdom"
  duration_text TEXT,  -- "1 minute", "until end of next turn"
  PRIMARY KEY (item_id, condition_id)
);

CREATE TABLE monster_action_conditions (
  monster_id INTEGER REFERENCES monsters(id),
  action_name TEXT,
  condition_id INTEGER REFERENCES condition_types(id),
  save_dc INTEGER,
  save_ability VARCHAR(10),
  duration_text TEXT,
  PRIMARY KEY (monster_id, action_name, condition_id)
);

CREATE TABLE spell_conditions (
  spell_id INTEGER REFERENCES spells(id),
  condition_id INTEGER REFERENCES condition_types(id),
  save_type TEXT,  -- "negates", "half duration"
  duration_text TEXT,
  PRIMARY KEY (spell_id, condition_id)
);
```

**Extraction Pattern:**
```python
import re

pattern = r'\{@condition ([^|}]+)(?:\|([^}]+))?\}'
# Matches: {@condition poisoned|XPHB}
# Group 1: "poisoned"
# Group 2: "XPHB" (optional)

# Also extract context:
# "must succeed on a DC 15 Constitution saving throw"
# "for 1 minute"
```

##### 2. Damage Expressions

**Tables to Create:**
```sql
CREATE TABLE monster_attacks (
  id SERIAL PRIMARY KEY,
  monster_id INTEGER REFERENCES monsters(id),
  action_name TEXT NOT NULL,
  attack_type TEXT,  -- "melee", "ranged", "spell"
  to_hit_bonus INTEGER,
  reach_ft INTEGER,
  range_normal_ft INTEGER,
  range_long_ft INTEGER,
  target TEXT,  -- "one target", "15-foot cone"

  -- Primary damage
  damage_dice TEXT,
  damage_bonus INTEGER,
  damage_type_id INTEGER REFERENCES damage_types(id),

  -- Additional damage (poison, fire, etc.)
  extra_damage_dice TEXT,
  extra_damage_bonus INTEGER,
  extra_damage_type_id INTEGER REFERENCES damage_types(id),

  -- Conditions and effects stored in action data JSONB
  save_dc INTEGER,
  save_ability VARCHAR(10),

  UNIQUE (monster_id, action_name)
);

CREATE TABLE spell_damage (
  id SERIAL PRIMARY KEY,
  spell_id INTEGER REFERENCES spells(id),
  damage_at_level INTEGER NOT NULL,  -- Which spell level
  damage_dice TEXT,
  damage_bonus INTEGER DEFAULT 0,
  damage_type_id INTEGER REFERENCES damage_types(id),
  save_for_half BOOLEAN DEFAULT false,
  PRIMARY KEY (spell_id, damage_at_level, damage_type_id)
);

CREATE TABLE item_damage (
  id SERIAL PRIMARY KEY,
  item_id INTEGER REFERENCES items(id),
  damage_dice TEXT,
  damage_bonus INTEGER DEFAULT 0,
  damage_type_id INTEGER REFERENCES damage_types(id),
  PRIMARY KEY (item_id, damage_type_id)
);
```

**Extraction Pattern:**
```python
# Match: {@damage 2d6 + 4}
pattern = r'\{@damage ([^}]+)\}'

# Parse damage string: "2d6 + 4"
def parse_damage(damage_str):
    # "2d6 + 4" → dice="2d6", bonus=4
    # "3d8" → dice="3d8", bonus=0
    # "10" → dice=None, bonus=10
    parts = damage_str.split('+')
    # ... parsing logic
```

##### 3. Clean Monster/Item Names

**Schema Changes:**
```sql
-- Add to items table
ALTER TABLE items ADD COLUMN base_name TEXT;
ALTER TABLE items ADD COLUMN variant_name TEXT;
ALTER TABLE items ADD COLUMN container_type TEXT;
ALTER TABLE items ADD COLUMN default_quantity INTEGER;
ALTER TABLE items ADD COLUMN bonus_display TEXT;

-- Add to monsters table
ALTER TABLE monsters ADD COLUMN base_name TEXT;
ALTER TABLE monsters ADD COLUMN variant_name TEXT;
ALTER TABLE monsters ADD COLUMN variant_notes TEXT;
```

**Cleaning Logic:**
```python
# Monster name: "{@creature Aboleth|MM} Spawn"
# Extract: base_name="Aboleth", variant_name="Spawn"

# Item name: "Arrow (20)"
# Extract: base_name="Arrow", default_quantity=20

# Item name: "Longsword (+1)"
# Extract: base_name="Longsword", bonus_weapon=1

# Item name: "Acid (vial)"
# Extract: base_name="Acid", container_type="vial"
```

##### 4. Normalize Bonus Fields

**Current State:**
```json
{
  "bonusWeapon": "+1",
  "bonusAc": "+2",
  "bonusSpellAttack": "+3"
}
```

**Target State:**
```json
{
  "bonusWeapon": 1,
  "bonusAc": 2,
  "bonusSpellAttack": 3
}
```

**Cleaning Logic:**
```python
def normalize_bonus(bonus_str):
    if isinstance(bonus_str, int):
        return bonus_str
    if isinstance(bonus_str, str):
        return int(bonus_str.replace('+', ''))
    return 0
```

##### 5. Handle Item Type Prefixes

**Current State:**
```json
{"type": "$G"}
{"type": "$A"}
{"type": "M"}
```

**Target State:**
```json
{"type": "G", "is_generic_variant": true}
{"type": "A", "is_generic_variant": true}
{"type": "M", "is_generic_variant": false}
```

**Schema Change:**
```sql
ALTER TABLE items ADD COLUMN is_generic_variant BOOLEAN DEFAULT false;
```

#### MEDIUM PRIORITY

##### 6. Cross-Reference Extraction

**Tables to Create:**
```sql
-- Items that reference other items
CREATE TABLE item_related_items (
  item_id INTEGER REFERENCES items(id),
  related_item_id INTEGER REFERENCES items(id),
  relationship_type TEXT,  -- "requires", "uses", "creates", "contains"
  quantity INTEGER,
  PRIMARY KEY (item_id, related_item_id, relationship_type)
);

-- Spells that summon creatures
CREATE TABLE spell_summons (
  spell_id INTEGER REFERENCES spells(id),
  creature_id INTEGER REFERENCES monsters(id),
  quantity_dice TEXT,  -- "1d4+1"
  duration TEXT,
  PRIMARY KEY (spell_id, creature_id)
);

-- Monsters that can cast spells (from spellcasting blocks)
CREATE TABLE monster_spells (
  monster_id INTEGER REFERENCES monsters(id),
  spell_id INTEGER REFERENCES spells(id),
  frequency TEXT,  -- "at will", "1/day", "3/day"
  spell_level INTEGER,
  PRIMARY KEY (monster_id, spell_id)
);
```

**Extraction Patterns:**
```python
# {@item crossbow bolt|phb} - Arrow requires bolts
# {@spell conjure animals|phb} - Reference to spell
# {@creature wolf|mm|wolves} - Summons wolves
```

#### LOW PRIORITY (Keep in JSONB)

##### 7. Formatting/Display Markup

**These stay in JSONB `entries[]`:**
- `{@dice 1d20}` - Presentation hint
- `{@hit +5}` - Formatting
- `{@dc 15}` - Display formatting
- `{@book PHB|9|Mounted Combat}` - Documentation link
- `{@quickref Cover||3}` - Rules reference

**Reason:** These are for UI rendering, not data queries.

### Scripts to Create

#### 1. extract_names.py
Clean all name fields, extract variants and metadata.

**What it does:**
```python
# For each item/monster/spell:
# 1. Strip ALL {@...} markup from name field
# 2. Extract base name and variant from parentheses
# 3. Parse quantities, bonuses, containers
# 4. Store in new columns

# Before:
{"name": "{@creature Aboleth|MM} Spawn"}

# After:
{"name": "Aboleth Spawn", "base_name": "Aboleth", "variant_name": "Spawn"}

# Before:
{"name": "Arrow (20)"}

# After:
{"name": "Arrow", "base_name": "Arrow", "default_quantity": 20}
```

#### 2. extract_conditions.py
Parse condition tags, populate junction tables.

**What it does:**
```python
# Parse all entries[] text
# Find {@condition name} tags
# Extract save DC and ability from context
# Create records in item_conditions, spell_conditions, etc.

# Example:
# "target must succeed on a DC 15 Constitution saving throw
#  or be {@condition poisoned|XPHB} for 1 minute"

# Creates:
item_conditions(
  item_id=123,
  condition_id=5,  # poisoned
  save_dc=15,
  save_ability="Constitution",
  duration_text="1 minute"
)
```

#### 3. extract_damage.py
Parse damage expressions, populate damage tables.

**What it does:**
```python
# Find {@damage ...} tags in action entries
# Parse dice notation and damage types
# Extract "fire damage", "piercing damage" from text
# Create records in monster_attacks, spell_damage

# Example:
# "{@atk mw} {@hit +5} to hit, reach 5 ft., one target.
#  {@h}7 ({@damage 1d6 + 4}) slashing damage."

# Creates:
monster_attacks(
  monster_id=123,
  action_name="Scimitar",
  attack_type="melee",
  to_hit_bonus=5,
  reach_ft=5,
  damage_dice="1d6",
  damage_bonus=4,
  damage_type_id=1  # slashing
)
```

#### 4. normalize_bonuses.py
Strip + prefixes, convert to integers.

**What it does:**
```python
# For all items with bonus fields:
# bonusWeapon: "+1" → 1
# bonusAc: "+2" → 2
# bonusSpellAttack: "+3" → 3

# Validation: ensure all bonus fields are now integers
```

#### 5. normalize_type_codes.py
Handle $ prefixes in type codes.

**What it does:**
```python
# For all items:
# type: "$G" → type="G", is_generic_variant=true
# type: "M" → type="M", is_generic_variant=false
```

#### 6. extract_cross_refs.py
Build relationship tables.

**What it does:**
```python
# Find {@item ...}, {@spell ...}, {@creature ...} tags
# Look up referenced entities in database
# Create junction table records
# Track relationship types (requires, uses, summons, etc.)
```

#### 7. extract_all.py
Master orchestration script (like clean_all.py).

**What it runs:**
1. extract_names.py
2. normalize_bonuses.py
3. normalize_type_codes.py
4. extract_conditions.py
5. extract_damage.py
6. extract_cross_refs.py
7. validate_extraction.py

#### 8. validate_extraction.py
Ensure extraction was successful.

**Validation checks:**
- ✅ No `{@...}` markup in any `name` field
- ✅ No `+` prefix in any bonus field (all integers)
- ✅ No `$` prefix in type codes
- ✅ All extracted condition_ids map to valid conditions
- ✅ All extracted damage_type_ids map to valid types
- ✅ All cross-references point to existing records
- ⚠️ `{@...}` markup still present in `entries[]` (expected)

### Updated Schema

Phase 0.6 requires schema additions:

```sql
-- Add to items table
ALTER TABLE items ADD COLUMN base_name TEXT;
ALTER TABLE items ADD COLUMN variant_name TEXT;
ALTER TABLE items ADD COLUMN container_type TEXT;
ALTER TABLE items ADD COLUMN default_quantity INTEGER;
ALTER TABLE items ADD COLUMN is_generic_variant BOOLEAN DEFAULT false;

-- Add to monsters table
ALTER TABLE monsters ADD COLUMN base_name TEXT;
ALTER TABLE monsters ADD COLUMN variant_name TEXT;
ALTER TABLE monsters ADD COLUMN variant_notes TEXT;

-- New junction tables (conditions, damage, cross-refs)
-- See detailed schema definitions above
```

### Deliverables

After Phase 0.6, we should have:

```
cleaned_data/
├── items_extracted.json           # Names cleaned, variants extracted
├── monsters_extracted.json        # Names cleaned, markup removed
├── spells_extracted.json          # Clean (minimal changes)
├── EXTRACTION_REPORT.md           # What was extracted
└── EXTRACTION_VALIDATION.md       # Validation results

extraction_data/
├── conditions_extracted.json      # All condition references found
├── damage_extracted.json          # All damage expressions parsed
└── cross_refs_extracted.json      # All entity relationships
```

### Success Criteria

Before moving to Phase 2 (Import Implementation):
- ✅ All `name` fields clean (no markup, extracted variants)
- ✅ All bonus fields are integers (438 fields normalized)
- ✅ All type codes normalized (271 codes processed)
- ✅ Condition extraction complete (6,113 references extracted)
- ⏭️ Damage extraction complete (15,000+ expressions expected)
- ⏭️ Cross-reference extraction complete
- ⏭️ Validation shows 100% pass rate
- ⏭️ Sample queries work: "find items that inflict poisoned"

**Status**: 🔄 IN PROGRESS - Basic extraction complete, advanced extraction pending

### Benefits After Phase 0.6

**Query Examples:**
```sql
-- Find all items that inflict the poisoned condition
SELECT i.name, ic.save_dc, ic.save_ability
FROM items i
JOIN item_conditions ic ON i.id = ic.item_id
JOIN condition_types ct ON ic.condition_id = ct.id
WHERE ct.name = 'poisoned';

-- Find all fire damage spells at level 3
SELECT s.name, sd.damage_dice
FROM spells s
JOIN spell_damage sd ON s.id = sd.spell_id
JOIN damage_types dt ON sd.damage_type_id = dt.id
WHERE dt.name = 'fire' AND s.level = 3;

-- Find monsters with attacks dealing 2d6 damage
SELECT m.name, ma.action_name, ma.damage_dice, dt.name
FROM monsters m
JOIN monster_attacks ma ON m.id = ma.monster_id
JOIN damage_types dt ON ma.damage_type_id = dt.id
WHERE ma.damage_dice = '2d6';

-- Find weapons that deal slashing damage
SELECT i.name, id.damage_dice
FROM items i
JOIN item_damage id ON i.id = id.item_id
JOIN damage_types dt ON id.damage_type_id = dt.id
WHERE dt.name = 'slashing';

-- Clean name search (no more markup pollution!)
SELECT name FROM monsters WHERE name LIKE '%goblin%';
-- Returns: "Goblin", "Goblin Boss", "Goblin King"
-- NOT: "{@creature Goblin|MM}", "{@creature Goblin Boss|MM} (Variant)"
```

### Design Decisions

#### Q1: Extract ALL cross-references or just high-value ones?

**Decision:** Start with high-value, expand later if needed.

**High-value (YES):**
- Conditions (enables condition queries)
- Damage (enables damage queries)
- Spell summons (useful for summoning spells)

**Low-value (MAYBE):**
- Item references in text (less useful)
- Book/quickref links (just display)

**Defer to Phase 2+:**
- Complete spell list extraction from monster blocks
- Equipment lists for monsters

#### Q2: How to handle display name overrides?

**Format:** `{@item longsword|phb|long sword}`
- Part 1: "longsword" (reference name)
- Part 2: "phb" (source)
- Part 3: "long sword" (display override)

**Decision:** Ignore display overrides for now. Use reference name.

**Rationale:** Display is UI concern, not data concern. Can add later if needed.

#### Q3: Store original text with markup removed?

**Decision:** NO. Keep original in `data` JSONB, store cleaned in `name`.

**Rationale:**
- `data` field preserves complete original JSON
- `name` field is clean for searching
- No need for third field with "markup removed text"

#### Q4: Performance concerns with extraction?

**Concern:** Parsing 189k markup tags could be slow.

**Mitigation:**
- Batch processing (process 100 records at a time)
- Progress bars with tqdm
- Compile regex patterns once
- Expected runtime: 5-10 minutes for full extraction

### Next Steps

1. Review and approve this plan
2. Create extraction scripts (8 total)
3. Update schema.sql with new columns and tables
4. Run extraction on cleaned data
5. Validate extraction (100% pass required)
6. Update PLAN.md to mark Phase 0.6 complete
7. Move to Phase 2: Import Implementation

---

## Phase 2: Import Implementation (Not Started)

**Prerequisites**: Complete Phase 0 ✅, Complete Phase 0.5 ✅, Complete Phase 1 ✅, Complete Phase 0.6 ⏭️

Details TBD after extraction is complete.

## Phase 3: Validation & Testing (Not Started)

**Prerequisites**: Complete Phase 0 ✅, Complete Phase 1 ✅, Complete Phase 2 ✅

Details TBD.

---

## Notes

- **Database**: `dnd5e_reference` (fresh, empty)
- **User**: `dnd5e_user` (has full access)
- **Additional User**: `dndbot` (will have SELECT access for cross-project use)
- **Python Environment**: `venv/` with psycopg2-binary, python-dotenv, tqdm

## Resources

- 5etools data: https://github.com/5etools-mirror-3/5etools-src
- 5etools schema docs: https://github.com/5etools-mirror-3/5etools-utils
