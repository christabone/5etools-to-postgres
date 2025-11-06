# Database Index Strategy for dnd5e_reference

## Overview

This document outlines the comprehensive indexing strategy for optimal query performance in the `dnd5e_reference` database. Indexes are critical for a read-heavy reference database that will be queried frequently.

**Database Size**: ~8,000 entities (2,722 items + 4,445 monsters + 937 spells) + 26,619 relationships

---

## Index Categories

### 1. Primary Keys (Automatic)
Every table has a `SERIAL PRIMARY KEY` which automatically creates a unique B-tree index.

### 2. Foreign Keys
**Strategy**: Index all foreign key columns for JOIN performance.
- Enables fast lookups when joining tables
- Critical for relationship queries

### 3. Full-Text Search (GIN indexes)
**Strategy**: Use GIN (Generalized Inverted Index) for text search.
- `to_tsvector('english', name)` - Full-text search on names
- `gin_trgm_ops` - Trigram matching for fuzzy/partial name searches
- `search_vector` - Pre-computed tsvector for complex searches
- JSONB columns - For querying nested data

### 4. Filtered Queries (B-tree indexes)
**Strategy**: Index frequently filtered columns.
- Rarity, CR, spell level, etc.
- Boolean flags (concentration, ritual, attunement)
- Numeric ranges (value, AC, HP)

### 5. Unique Constraints
**Strategy**: Enforce data integrity and enable fast lookups.
- Junction tables use composite UNIQUE constraints
- Lookup tables use UNIQUE on code fields

---

## Index Breakdown by Table

### Core Entity Tables

#### Items Table (2,722 records)
```sql
-- Full-text search (GIN)
CREATE INDEX idx_items_name ON items USING gin(to_tsvector('english', name));
CREATE INDEX idx_items_name_trgm ON items USING gin(name gin_trgm_ops);
CREATE INDEX idx_items_data ON items USING gin(data);
CREATE INDEX idx_items_search ON items USING gin(search_vector);

-- Foreign keys (B-tree)
CREATE INDEX idx_items_rarity ON items(rarity_id);
CREATE INDEX idx_items_type ON items(type_id);
CREATE INDEX idx_items_source ON items(source_id);

-- Filtered queries (B-tree)
CREATE INDEX idx_items_value ON items(value_cp);
CREATE INDEX idx_items_attunement ON items(requires_attunement);

-- Added in Phase 1 update (GIN for new text fields)
CREATE INDEX idx_items_base_name ON items USING gin(to_tsvector('english', base_name));
```

**Query Patterns**:
- "Find all rare magic items" → `idx_items_rarity`
- "Search for 'longsword'" → `idx_items_name_trgm`
- "Find items under 100 GP" → `idx_items_value`
- "Find items from PHB" → `idx_items_source`

---

#### Monsters Table (4,445 records)
```sql
-- Full-text search (GIN)
CREATE INDEX idx_monsters_name ON monsters USING gin(to_tsvector('english', name));
CREATE INDEX idx_monsters_name_trgm ON monsters USING gin(name gin_trgm_ops);
CREATE INDEX idx_monsters_data ON monsters USING gin(data);
CREATE INDEX idx_monsters_search ON monsters USING gin(search_vector);

-- Foreign keys (B-tree)
CREATE INDEX idx_monsters_type ON monsters(type_id);
CREATE INDEX idx_monsters_size ON monsters(size_id);
CREATE INDEX idx_monsters_source ON monsters(source_id);

-- Filtered queries (B-tree)
CREATE INDEX idx_monsters_cr ON monsters(cr);
CREATE INDEX idx_monsters_hp ON monsters(hp_average);
CREATE INDEX idx_monsters_ac ON monsters(ac_primary);

-- Added in Phase 1 update (GIN for new text fields)
CREATE INDEX idx_monsters_base_name ON monsters USING gin(to_tsvector('english', base_name));
```

**Query Patterns**:
- "Find CR 5-10 dragons" → `idx_monsters_cr` + `idx_monsters_type`
- "Find large undead" → `idx_monsters_size` + `idx_monsters_type`
- "Search for 'goblin'" → `idx_monsters_name_trgm`

---

#### Spells Table (937 records)
```sql
-- Full-text search (GIN)
CREATE INDEX idx_spells_name ON spells USING gin(to_tsvector('english', name));
CREATE INDEX idx_spells_name_trgm ON spells USING gin(name gin_trgm_ops);
CREATE INDEX idx_spells_data ON spells USING gin(data);
CREATE INDEX idx_spells_search ON spells USING gin(search_vector);

-- Foreign keys (B-tree)
CREATE INDEX idx_spells_school ON spells(school_id);
CREATE INDEX idx_spells_source ON spells(source_id);

-- Filtered queries (B-tree)
CREATE INDEX idx_spells_level ON spells(level);
CREATE INDEX idx_spells_concentration ON spells(requires_concentration);
CREATE INDEX idx_spells_ritual ON spells(is_ritual);
CREATE INDEX idx_spells_casting_time ON spells(casting_time_number);
```

**Query Patterns**:
- "Find 3rd level evocation spells" → `idx_spells_level` + `idx_spells_school`
- "Find ritual spells" → `idx_spells_ritual`
- "Find concentration spells" → `idx_spells_concentration`

---

### Junction Tables (Many-to-Many Relationships)

#### General Pattern
```sql
-- Foreign keys for JOINs
CREATE INDEX idx_<table>_<entity1> ON <table>(<entity1>_id);
CREATE INDEX idx_<table>_<entity2> ON <table>(<entity2>_id);

-- Composite UNIQUE constraint (prevents duplicates)
UNIQUE (<entity1>_id, <entity2>_id)
```

#### Example: item_item_properties
```sql
CREATE INDEX idx_item_props_item ON item_item_properties(item_id);
CREATE INDEX idx_item_props_property ON item_item_properties(property_id);
```

**Query Patterns**:
- "Find all finesse weapons" → `idx_item_props_property` JOIN items
- "Get properties for longsword" → `idx_item_props_item`

---

### Condition Tables (Phase 1 Addition)

#### item_conditions (508 records expected)
```sql
CREATE INDEX idx_item_conditions_item ON item_conditions(item_id);
CREATE INDEX idx_item_conditions_condition ON item_conditions(condition_id);
CREATE INDEX idx_item_conditions_inflicts ON item_conditions(inflicts);
```

**Query Patterns**:
- "Find items that inflict paralyzed" → `idx_item_conditions_condition` + `inflicts`
- "What conditions does this item inflict?" → `idx_item_conditions_item`

#### monster_action_conditions (5,074 records expected)
```sql
CREATE INDEX idx_monster_action_conditions_monster ON monster_action_conditions(monster_id);
CREATE INDEX idx_monster_action_conditions_condition ON monster_action_conditions(condition_id);
CREATE INDEX idx_monster_action_conditions_action ON monster_action_conditions(monster_id, action_name);
```

**Query Patterns**:
- "Find monsters that can stun" → `idx_monster_action_conditions_condition`
- "What conditions does this monster inflict?" → `idx_monster_action_conditions_monster`

#### spell_conditions (531 records expected)
```sql
CREATE INDEX idx_spell_conditions_spell ON spell_conditions(spell_id);
CREATE INDEX idx_spell_conditions_condition ON spell_conditions(condition_id);
CREATE INDEX idx_spell_conditions_inflicts ON spell_conditions(inflicts);
```

---

### Damage Tables (Phase 1 Addition)

#### monster_attacks (4,364 records expected)
```sql
CREATE INDEX idx_monster_attacks_monster ON monster_attacks(monster_id);
CREATE INDEX idx_monster_attacks_type ON monster_attacks(attack_type_id);
CREATE INDEX idx_monster_attacks_damage_type ON monster_attacks(damage_type_id);
CREATE INDEX idx_monster_attacks_to_hit ON monster_attacks(to_hit_bonus);
CREATE INDEX idx_monster_attacks_action ON monster_attacks(monster_id, action_name);
```

**Query Patterns**:
- "Find monsters with fire attacks" → `idx_monster_attacks_damage_type`
- "Find monsters with +10 to hit" → `idx_monster_attacks_to_hit`
- "Get all attacks for this monster" → `idx_monster_attacks_monster`

#### spell_damage (520 records expected)
```sql
CREATE INDEX idx_spell_damage_spell ON spell_damage(spell_id);
CREATE INDEX idx_spell_damage_type ON spell_damage(damage_type_id);
CREATE INDEX idx_spell_damage_level ON spell_damage(spell_level);
```

**Query Patterns**:
- "Find spells that deal fire damage" → `idx_spell_damage_type`
- "Get spell damage scaling by level" → `idx_spell_damage_spell` + `spell_level`

#### item_damage (734 records expected)
```sql
CREATE INDEX idx_item_damage_item ON item_damage(item_id);
CREATE INDEX idx_item_damage_type ON item_damage(damage_type_id);
```

---

### Cross-Reference Tables (Phase 1 Addition)

#### spell_summons (105 records expected - 42 summons + 63 general creature refs)
```sql
CREATE INDEX idx_spell_summons_spell ON spell_summons(spell_id);
CREATE INDEX idx_spell_summons_creature ON spell_summons(creature_id);
CREATE INDEX idx_spell_summons_is_summon ON spell_summons(is_summon);
```

**Query Patterns**:
- "What creatures can this spell summon?" → `idx_spell_summons_spell` + `is_summon=true`
- "What spells summon this creature?" → `idx_spell_summons_creature`

#### monster_spells (10,979 records expected)
```sql
CREATE INDEX idx_monster_spells_monster ON monster_spells(monster_id);
CREATE INDEX idx_monster_spells_spell ON monster_spells(spell_id);
CREATE INDEX idx_monster_spells_frequency ON monster_spells(frequency);
```

**Query Patterns**:
- "What spells can this monster cast?" → `idx_monster_spells_monster`
- "What monsters can cast fireball?" → `idx_monster_spells_spell`
- "Find innate spellcasters" → `idx_monster_spells_frequency`

#### Other Cross-Reference Tables
Similar patterns for:
- `item_related_items` (564 records)
- `item_spells` (1,157 records)
- `item_creatures` (401 records)
- `monster_items` (1,086 records)
- `monster_creatures` (321 records)
- `spell_items` (13 records)
- `spell_related_spells` (143 records)

---

### Lookup Tables (Controlled Vocabulary)

#### General Pattern
```sql
-- Primary key (automatic B-tree)
id SERIAL PRIMARY KEY

-- Unique constraint on code (automatic B-tree)
code VARCHAR UNIQUE NOT NULL
```

**Lookup Tables**:
- `sources` (115 values)
- `item_types` (63 values)
- `item_rarities` (10 values)
- `damage_types` (13 values)
- `condition_types` (15 values)
- `creature_types` (14 values)
- `creature_sizes` (6 values)
- `spell_schools` (8 values)
- `alignment_values` (7 values)
- `attack_types` (6 values)
- `skills` (18 values)
- `item_properties` (varies)

**Note**: Small lookup tables don't need additional indexes beyond PRIMARY KEY and UNIQUE constraints. PostgreSQL will use these efficiently.

---

## Index Maintenance Strategy

### After Data Load
```sql
-- Rebuild all indexes for optimal performance
REINDEX DATABASE dnd5e_reference;

-- Analyze tables to update statistics
ANALYZE;

-- Vacuum to reclaim space
VACUUM ANALYZE;
```

### Regular Maintenance (if data updates)
```sql
-- Update statistics (run after significant data changes)
ANALYZE;

-- Check for index bloat
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## Index Performance Considerations

### When Indexes Help
✅ **Highly selective queries** - "Find CR 20 monsters" (few results)
✅ **JOIN operations** - Foreign key indexes are critical
✅ **ORDER BY clauses** - B-tree indexes help sorting
✅ **Text search** - GIN indexes for full-text and JSONB queries
✅ **UNIQUE constraints** - Enforce data integrity

### When Indexes Don't Help
❌ **Full table scans** - "SELECT * FROM monsters" (no WHERE)
❌ **Low selectivity** - Queries returning >15% of table
❌ **Small tables** - Lookup tables with <100 rows
❌ **Infrequent queries** - Index maintenance cost > query benefit

### Index Size Impact
- **GIN indexes**: Larger size, slower inserts, excellent for text search
- **B-tree indexes**: Smaller size, fast inserts, good for equality/range queries
- **Composite indexes**: Can serve multiple query patterns

---

## Performance Benchmarks (Post-Import)

### Queries to Test
```sql
-- 1. Name search (should use idx_monsters_name_trgm)
EXPLAIN ANALYZE
SELECT * FROM monsters WHERE name ILIKE '%dragon%';

-- 2. CR range (should use idx_monsters_cr)
EXPLAIN ANALYZE
SELECT * FROM monsters WHERE cr BETWEEN 5 AND 10;

-- 3. Complex JOIN (should use foreign key indexes)
EXPLAIN ANALYZE
SELECT m.name, STRING_AGG(ct.name, ', ') as conditions
FROM monsters m
JOIN monster_action_conditions mac ON m.id = mac.monster_id
JOIN condition_types ct ON mac.condition_id = ct.id
WHERE mac.inflicts = true
GROUP BY m.name;

-- 4. Spell search by level and school (should use both indexes)
EXPLAIN ANALYZE
SELECT s.name, ss.name as school
FROM spells s
JOIN spell_schools ss ON s.school_id = ss.id
WHERE s.level = 3 AND ss.code = 'V';

-- 5. JSONB query (should use idx_items_data)
EXPLAIN ANALYZE
SELECT name FROM items WHERE data @> '{"weapon": true}';
```

### Expected Performance
- Name searches: <10ms (with GIN trigram index)
- Filtered queries: <5ms (with B-tree indexes)
- Complex JOINs: <50ms (with foreign key indexes)
- JSONB queries: <20ms (with GIN index on data column)

---

## Index Summary Statistics

### Total Indexes: 77+

**By Type**:
- Primary Keys: 38 (automatic)
- Foreign Keys: ~45 (B-tree)
- Full-Text Search: 12 (GIN - name search)
- JSONB: 3 (GIN - data columns)
- tsvector: 3 (GIN - search_vector)
- Filtered Queries: ~20 (B-tree - CR, level, booleans, etc.)
- Composite UNIQUE: ~15 (junction tables)

**By Table Category**:
- Core entities (items, monsters, spells): 27 indexes
- Junction tables: ~30 indexes
- Condition tables: 9 indexes
- Damage tables: 12 indexes
- Cross-reference tables: 27 indexes
- Lookup tables: 38 PRIMARY KEY + UNIQUE indexes

---

## PostgreSQL Extensions Required

### pg_trgm (Trigram matching)
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```
**Purpose**: Enables fuzzy name matching with `gin_trgm_ops`

**Usage**: Allows queries like:
```sql
SELECT * FROM items WHERE name ILIKE '%sword%';  -- Uses idx_items_name_trgm
```

---

## Index Creation Order

### Recommended Sequence:
1. **Create tables** (schema.sql includes PRIMARY KEYs automatically)
2. **Import data** (faster without indexes)
3. **Create foreign key indexes** (critical for JOINs)
4. **Create GIN indexes** (text search)
5. **Create filtered query indexes** (CR, level, etc.)
6. **ANALYZE** (update statistics)

**Note**: Our schema.sql creates indexes inline with table definitions, which is fine for initial setup.

---

## Monitoring Index Usage

### Check Index Usage
```sql
-- Find unused indexes
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0 AND indexname NOT LIKE '%_pkey'
ORDER BY pg_relation_size(indexrelid) DESC;

-- Find most-used indexes
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC
LIMIT 20;
```

---

## Conclusion

This index strategy provides:
- ✅ **Fast text search** via GIN indexes on name fields
- ✅ **Efficient JOINs** via foreign key indexes
- ✅ **Quick filtered queries** via B-tree indexes on common filter fields
- ✅ **JSONB query support** via GIN indexes on data columns
- ✅ **Data integrity** via UNIQUE constraints on junction tables

The 77+ indexes are justified for a **read-heavy reference database** where query performance is critical and data updates are infrequent (only when 5etools releases new versions).

---

**Document Version**: 1.0
**Last Updated**: 2025-11-06
**Schema Version**: 869 lines, 38 tables
**Data Version**: 5etools v2.15.0
