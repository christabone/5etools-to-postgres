# 5etools Data Analysis Summary

**Analysis Date**: 2025-11-05
**Data Version**: 5etools v2.15.0

## Executive Summary

✅ **Phase 0 Complete**: All analysis scripts executed successfully
📊 **Total Unique Fields**: 741 field paths identified
⚠️  **Polymorphic Fields**: 10 fields that can be multiple types
🎯 **Controlled Vocabularies**: 4,841 fields identified as potential lookups
📦 **Sample Records**: Extracted simple, complex, and edge case examples

---

## Key Findings

### 1. Data Scale
- **Items**: 2,722 total (196 base items + 2,526 magic items)
- **Monsters**: 3,000+ across 100+ bestiary files
- **Spells**: 1,000+ across multiple spell files

### 2. Critical Polymorphic Fields ⚠️

These fields require special handling as they can be multiple types:

| Field | Types | Notes |
|-------|-------|-------|
| `monster.type` | str, dict | Can be `"humanoid"` OR `{"type": "humanoid", "tags": ["orc"]}` |
| `monster.ac[]` | int, dict | Can be `13` OR `{"ac": 13, "from": ["hide armor"]}` |
| `monster.alignment[]` | str, dict | Can be `"C"` OR `{"alignment": ["C", "E"]}` |
| `monster.resist[]` | str, dict | Can be `"fire"` OR complex resistance object |
| `monster.speed.fly` | int, dict | Can be `60` OR `{"number": 60, "condition": "..."}` |
| `baseitem.entries[]` | str, dict | Mixed content - strings and nested objects |
| `baseitem.property[]` | str, dict | Can be `"F"` OR `{"uid": "2H|XPHB", "note": "..."}` |
| `baseitem.value` | int, float | Inconsistent numeric types |
| `baseitem.weight` | int, float | Inconsistent numeric types |

### 3. Foreign Key Candidates

**High Confidence** (should be lookup tables):

```
baseitem.source         → sources table (10 unique values)
baseitem.type           → item_types table (21 unique values)
baseitem.dmgType        → damage_types table (5 values: S, P, B, N, R)
baseitem.rarity         → rarity_levels table (2 values: none, unknown)
monster.size            → creature_sizes table
monster.type            → creature_types table
spell.school            → magic_schools table
```

### 4. Many-to-Many Relationships

Arrays that represent relationships:

```
baseitem.property[]     → item_properties (join table needed)
baseitem.mastery[]      → weapon_masteries (join table needed)
monster.languages[]     → languages (join table needed)
monster.resist[]        → damage resistances (join table needed)
monster.immune[]        → damage immunities (join table needed)
monster.conditionImmune[] → conditions (join table needed)
```

### 5. Complex Nested Structures

Fields that should likely be stored as JSONB:

- `baseitem.entries[]` - Rich text content with nested formatting
- `monster.action[]` - Action definitions with complex formatting
- `monster.trait[]` - Special abilities
- `monster.legendary[]` - Legendary actions
- `spell.entries[]` - Spell descriptions
- `spell.entriesHigherLevel[]` - Higher level casting effects

---

## Data Quality Issues

### Missing/Null Values
- Many optional fields (need default handling)
- Some items lack `rarity` field
- Some monsters lack certain stats

### Inconsistent Formats
- **Ranges**: Can be `"30"`, `"30/120"`, or missing
- **Values**: Sometimes in copper, sometimes needs conversion
- **Arrays**: Can be empty `[]` when not applicable

### Edge Cases Found
- Items with no damage type (non-weapons)
- Monsters with fractional CR (`"1/2"`, `"1/4"`)
- Spells with complex duration/range objects

---

## Schema Design Recommendations

### Core Tables Needed

1. **Lookup/CV Tables** (populate first):
   - `sources`
   - `damage_types`
   - `rarity_levels`
   - `magic_schools`
   - `creature_sizes`
   - `creature_types`
   - `alignments`
   - `conditions`
   - `languages`
   - `skills`
   - `item_types`
   - `item_properties`
   - `weapon_masteries`

2. **Main Entity Tables**:
   - `items` (with JSONB `data` column for full record)
   - `monsters` (with JSONB `data` column)
   - `spells` (with JSONB `data` column)

3. **Junction Tables** (many-to-many):
   - `item_property_map` (items ↔ properties)
   - `item_mastery_map` (items ↔ masteries)
   - `monster_languages` (monsters ↔ languages)
   - `monster_alignments` (monsters ↔ alignments)
   - `monster_damage_modifiers` (monsters ↔ damage types + modifier_type)
   - `monster_condition_immunities` (monsters ↔ conditions)
   - `spell_damage_types` (spells ↔ damage types)

### Handling Polymorphic Fields

**Strategy 1**: Type normalization (check type, handle accordingly)
```python
if isinstance(monster_type, str):
    type_name = monster_type
elif isinstance(monster_type, dict):
    type_name = monster_type.get('type')
    tags = monster_type.get('tags', [])  # Store separately
```

**Strategy 2**: Always store full JSON in `data` column
- Extract normalized fields for queries
- Keep full JSON for completeness

**Recommended**: Hybrid approach
- Normalize key queryable fields
- Store complete JSON in `data` column for reference

---

## Next Steps (Phase 1: Schema Design)

1. ✅ Review this analysis
2. ⏭️ Design normalized schema based on findings
3. ⏭️ Create `schema.sql` with:
   - All CV tables
   - Main entity tables with JSONB
   - Junction tables
   - Indexes on commonly queried fields
   - Views for common queries
4. ⏭️ Document field mappings (JSON → DB columns)

---

## Files Generated

```
analysis/
├── structure_report.json       # Complete field inventory (741 fields)
├── field_types_report.json     # Type info + 10 polymorphic fields
├── controlled_vocab.json       # 4,841 CV fields identified
├── relationships.json          # FK and relationship patterns
├── samples/
│   ├── items_simple.json      # 10 simple item examples
│   ├── items_complex.json     # 10 complex item examples
│   ├── monsters_simple.json   # 10 simple monster examples
│   └── monsters_complex.json  # 10 complex monster examples
└── SUMMARY.md                  # This file
```

---

## Critical Insights for Import Scripts

When we get to Phase 2 (Import), remember:

1. **Parse polymorphic fields carefully** - Type check before extraction
2. **Use lookup_or_create pattern** for referenced values
3. **Handle missing/null values** with defaults
4. **Batch inserts** for performance (500-1000 at a time)
5. **Store full JSON** in `data` column as backup
6. **Foreign key lookups** should be cached in memory
7. **Array relationships** need junction table inserts after main record
8. **Error handling** - Log failures, continue processing
9. **Progress tracking** - Use tqdm for visibility

---

**Status**: ✅ Phase 0 Complete - Ready for Schema Design
