# Special Characters & Markup Normalization Report

## Executive Summary

After investigating all special characters in the cleaned data, we found **256,208 occurrences** of 34 unique special characters. The most significant finding is the extensive use of **5etools markup syntax** (`{@...}`) that contains valuable structured data we should extract and normalize into database relationships.

---

## 1. 5etools Markup Syntax (`{@...}`)

### What It Is

5etools uses a custom markup language for cross-references and formatting:

```
{@type name|source|display}
```

**Examples:**
- `{@item longsword|phb}` - Reference to an item
- `{@creature goblin|mm}` - Reference to a monster
- `{@condition Charmed|XPHB}` - Reference to a condition
- `{@spell fireball|phb}` - Reference to a spell
- `{@damage 2d6}` - Damage expression
- `{@dice 1d20}` - Dice roll
- `{@hit +5}` - Attack bonus

### Occurrence: 189,000+ instances

### Current Location

**Primarily in descriptive text:**
- `items.entries[]` - Item descriptions
- `monsters.trait[].entries[]` - Monster traits
- `monsters.action[].entries[]` - Monster actions
- `spells.entries[]` - Spell descriptions

**Also in key fields (PROBLEM!):**
- `monsters.name` - 880 occurrences
- `items.name` - Some occurrences

---

## 2. Normalization Strategy by Markup Type

### 2A. `{@condition ...}` - Conditions Applied/Granted

**Extract to:** Many-to-many relationship tables

**Example:**
```json
// BEFORE (in entries[])
"A creature hit by this attack must succeed on a DC 15
Constitution saving throw or be {@condition poisoned|XPHB}."

// AFTER
items.id = 123
item_conditions:
  - item_id: 123, condition_id: 5 (poisoned), inflicts: true
```

**New Tables Needed:**
```sql
-- Already have: condition_types

CREATE TABLE item_conditions (
  item_id INTEGER REFERENCES items(id),
  condition_id INTEGER REFERENCES condition_types(id),
  inflicts BOOLEAN DEFAULT true,  -- vs grants immunity/resistance
  PRIMARY KEY (item_id, condition_id)
);

CREATE TABLE monster_action_conditions (
  monster_id INTEGER REFERENCES monsters(id),
  action_name TEXT,
  condition_id INTEGER REFERENCES condition_types(id),
  save_dc INTEGER,
  save_ability TEXT,
  PRIMARY KEY (monster_id, action_name, condition_id)
);

CREATE TABLE spell_conditions (
  spell_id INTEGER REFERENCES spells(id),
  condition_id INTEGER REFERENCES condition_types(id),
  save_dc_type TEXT,  -- "spell save DC"
  PRIMARY KEY (spell_id, condition_id)
);
```

---

### 2B. `{@damage ...}` - Damage Expressions

**Extract to:** Structured damage data

**Example:**
```json
// BEFORE
"{@damage 2d6 + 4} fire damage"

// AFTER
monster_attacks:
  - monster_id: 123
  - action_name: "Fire Breath"
  - damage_dice: "2d6"
  - damage_bonus: 4
  - damage_type_id: 3 (fire)
```

**New Tables Needed:**
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
  target TEXT,
  damage_dice TEXT,
  damage_bonus INTEGER,
  damage_type_id INTEGER REFERENCES damage_types(id),
  additional_effects JSONB  -- Other effects from the attack
);

CREATE TABLE spell_damage (
  id SERIAL PRIMARY KEY,
  spell_id INTEGER REFERENCES spells(id),
  level INTEGER,  -- What level this damage applies (for scaling)
  damage_dice TEXT,
  damage_type_id INTEGER REFERENCES damage_types(id),
  save_type TEXT,  -- "half", "none"
  PRIMARY KEY (spell_id, level, damage_type_id)
);
```

---

### 2C. `{@item ...}`, `{@spell ...}`, `{@creature ...}` - Cross-References

**Extract to:** Many-to-many relationship tables

**Example:**
```json
// Spell that creates a creature
"{@spell conjure animals|phb} to summon {@creature wolf|mm|wolves}"

// AFTER
spell_summons:
  - spell_id: 45, creature_id: 123
```

**New Tables Needed:**
```sql
-- Items that reference other items (e.g., ammunition for weapons)
CREATE TABLE item_related_items (
  item_id INTEGER REFERENCES items(id),
  related_item_id INTEGER REFERENCES items(id),
  relationship_type TEXT,  -- "requires", "uses", "creates", "contains"
  PRIMARY KEY (item_id, related_item_id, relationship_type)
);

-- Spells that summon creatures
CREATE TABLE spell_summons (
  spell_id INTEGER REFERENCES spells(id),
  creature_id INTEGER REFERENCES monsters(id),
  quantity_dice TEXT,  -- "1d4+1"
  PRIMARY KEY (spell_id, creature_id)
);

-- Monsters that can cast spells
-- (Already tracked in spellcasting JSONB, but could extract)
CREATE TABLE monster_spells (
  monster_id INTEGER REFERENCES monsters(id),
  spell_id INTEGER REFERENCES spells(id),
  frequency TEXT,  -- "at will", "1/day", "3/day"
  spell_level INTEGER,
  PRIMARY KEY (monster_id, spell_id)
);
```

---

### 2D. `{@dice ...}`, `{@hit ...}`, `{@dc ...}` - Game Mechanics

**Keep in descriptive text** - These are formatting hints, not data

**Example:**
```
"The target must make a {@dc 15} Dexterity saving throw"
"Make a {@hit +5} attack roll"
"Roll {@dice 1d20}"
```

These should stay in JSONB `entries[]` as they're part of the natural language description.

---

### 2E. `{@quickref ...}`, `{@book ...}` - Documentation References

**Keep in descriptive text** - These are external references

**Example:**
```
"{@quickref Cover||3||half cover}"
"{@book Player's Handbook|PHB|9|Mounted Combat}"
```

Keep in JSONB for rendering links in UIs.

---

## 3. Other Special Characters

### 3A. Mathematical/Bonus Notation

#### Parentheses in Names: `()`

**Item names:**
- `"Arrow (20)"` → quantity should be in separate field
- `"Longsword (+1)"` → bonus should be in `bonus_weapon` field
- `"Acid (vial)"` → container type could be in separate field

**Recommendation:**
```sql
ALTER TABLE items ADD COLUMN base_name TEXT;
ALTER TABLE items ADD COLUMN container_type TEXT;  -- "vial", "flask", "pouch"
ALTER TABLE items ADD COLUMN default_quantity INTEGER;

-- Clean during import:
"Arrow (20)" → base_name="Arrow", default_quantity=20
"Acid (vial)" → base_name="Acid", container_type="vial"
"Longsword (+1)" → base_name="Longsword", bonus_weapon=1
```

#### Plus Signs: `+`

**In bonus fields:** Already normalized ✅
- `bonusWeapon: "+1"` → should be `1` (integer)
- `bonusAc: "+2"` → should be `2` (integer)

**In HP formulas:** Keep as-is ✅
- `hp.formula: "8d10 + 16"` → this is correct format

**Recommendation:**
Strip `+` prefix from bonus fields, convert to integers.

---

### 3B. Item Type Codes with `$`

**Current:**
```
type: "$G"  // Generic variant
type: "$A"  // Alternate version
type: "$C"  // Custom/crafted
```

**Recommendation:**
These are metadata flags. Add a boolean field:

```sql
ALTER TABLE items ADD COLUMN is_generic_variant BOOLEAN DEFAULT false;
ALTER TABLE items ADD COLUMN is_alternate_version BOOLEAN DEFAULT false;

-- During import:
if type.startswith('$'):
    is_generic_variant = True
    type = type[1:]  // Remove $
```

---

### 3C. Monster Names with Markup

**CRITICAL ISSUE:**

**Current:**
```
monster.name: "Empyrean (Maimed){@note maimed}"
monster.name: "{@creature Aboleth|MM} Spawn"
```

**Recommendation:**
```sql
ALTER TABLE monsters ADD COLUMN base_name TEXT;
ALTER TABLE monsters ADD COLUMN variant_name TEXT;
ALTER TABLE monsters ADD COLUMN notes TEXT;

-- Parse during import:
"{@creature Aboleth|MM} Spawn" → base_name="Aboleth", variant_name="Spawn"
"Empyrean (Maimed)" → base_name="Empyrean", variant_name="Maimed"
```

---

### 3D. Fractions and Special Math

**Fractions:** `½`, `¼`, `¾`
- Appear in descriptive text
- Keep as-is in JSONB

**Math symbols:** `×`, `−`, `÷`
- Used in formulas and descriptions
- Keep as-is in JSONB

---

### 3E. Typography

**Em dash (—), En dash (–):**
- Used in prose
- Keep in JSONB entries

**Accented characters (é, ô, û, æ):**
- Used in proper nouns (French/fantasy names)
- **MUST PRESERVE** - these are correct spellings
- Ensure database uses UTF-8 encoding ✅

---

## 4. Extraction Priority

### HIGH PRIORITY (Phase 0.6 - Markup Extraction)

1. **Extract `{@condition}` tags**
   - Creates searchable relationships
   - "Find all items that inflict poisoned condition"
   - "Find all spells that grant frightened condition"

2. **Extract `{@damage}` expressions**
   - Normalize attack/damage data
   - Enable queries like "weapons that deal fire damage"
   - Better than searching JSONB text

3. **Clean monster/item names**
   - Remove markup from `name` field
   - Extract variants to separate field
   - Essential for clean searching

4. **Normalize bonuses**
   - Strip `+` prefix, convert to integers
   - Already mostly done, just validate

5. **Extract item quantities/containers**
   - Separate "Arrow (20)" → name + quantity
   - Separate "Acid (vial)" → name + container type

### MEDIUM PRIORITY (Phase 0.7 - Cross-References)

6. **Extract cross-references**
   - `{@item}`, `{@spell}`, `{@creature}` relationships
   - Build relationship tables
   - Enable "what spells summon this creature?"

### LOW PRIORITY (Keep in JSONB)

7. **Formatting markup**
   - `{@dice}`, `{@hit}`, `{@dc}` - presentation hints
   - `{@book}`, `{@quickref}` - documentation links
   - Keep in text for UI rendering

---

## 5. Implementation Plan

### Phase 0.6: Markup Extraction & Normalization

**New Scripts:**
1. `extract_conditions.py` - Parse `{@condition}` tags, populate junction tables
2. `extract_damage.py` - Parse `{@damage}` tags, populate attack/damage tables
3. `clean_names.py` - Remove markup from names, extract variants
4. `normalize_bonuses.py` - Clean bonus fields
5. `extract_cross_refs.py` - Build relationship tables

**Schema Updates:**
Add all tables mentioned above to `schema.sql`

**Cleaning Updates:**
Update existing cleaning scripts to:
- Remove `+` prefix from bonus fields
- Parse `$` prefix in type codes
- Separate quantities from names

### Validation

Run new validation that checks:
- ✅ No `{@...}` markup in `name` fields
- ✅ No `{@...}` markup in normalized fields (type, rarity, etc.)
- ✅ All bonus fields are integers (no `+` prefix)
- ✅ All extracted conditions/damage map to valid IDs
- ⚠️ `{@...}` markup still present in `entries[]` (expected for display)

---

## 6. Benefits

**After normalization:**

```sql
-- Find all items that inflict the poisoned condition
SELECT i.name FROM items i
JOIN item_conditions ic ON i.id = ic.item_id
JOIN condition_types ct ON ic.condition_id = ct.id
WHERE ct.name = 'poisoned';

-- Find all fire damage spells
SELECT s.name FROM spells s
JOIN spell_damage sd ON s.id = sd.spell_id
JOIN damage_types dt ON sd.damage_type_id = dt.id
WHERE dt.name = 'fire';

-- Find weapons that deal 2d6 damage
SELECT * FROM monster_attacks
WHERE damage_dice = '2d6';

-- Clean name searching (no markup pollution)
SELECT name FROM monsters WHERE name LIKE '%goblin%';
-- Won't return "{@creature Goblin Boss|MM}"
```

---

## 7. Open Questions

1. **Should we extract ALL cross-references or just high-value ones?**
   - Conditions: YES
   - Damage: YES
   - Item references: MAYBE
   - Spell summons: MAYBE
   - Book references: NO

2. **How to handle display names from markup?**
   - `{@item longsword|phb|long sword}` - third part is display override
   - Store in separate `display_name` field?

3. **Versioning of extracted data?**
   - If 5etools updates, how do we re-extract?
   - Keep extraction scripts idempotent

4. **Performance trade-offs?**
   - More normalized tables = more JOINs
   - But better indexing and querying
   - Recommendation: Extract high-value relationships, keep rest in JSONB

---

## 8. Next Steps

**Tomorrow's Tasks:**

1. Review this report and decide extraction priorities
2. Update `schema.sql` with new relationship tables
3. Create extraction scripts for Phase 0.6
4. Update PLAN.md with Phase 0.6 details
5. Test extraction on sample records
6. Run full extraction and validate
7. Update validation to check for clean names and no markup pollution

**Files to Create:**
- `extract_markup.py` - Main extraction orchestrator
- `parsers/condition_parser.py` - Extract conditions from text
- `parsers/damage_parser.py` - Extract damage expressions
- `parsers/name_cleaner.py` - Clean names, extract variants
- `mappings/5etools_markup_spec.json` - Document all markup types

**Schema Changes:**
- Add ~10 new tables for relationships
- Add fields: `base_name`, `variant_name`, `container_type`, `default_quantity`
- Update views to use clean names
