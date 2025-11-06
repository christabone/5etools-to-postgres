# Pipes and Abbreviations Report

## Executive Summary

After investigating the cleaned data, we have identified:

1. **9,248 values containing pipe characters (`|`)** across all datasets
2. **Multiple fields using abbreviations** that need human-readable mappings

## 1. PIPE CHARACTER USAGE

### What Pipes Mean in 5etools

The pipe character (`|`) serves as a **namespace separator** in 5etools, with the format:
```
{value}|{source}
```

### Common Patterns

#### Pattern 1: Item/Spell/Creature References with Source
- `plane shift|xphb` - spell "plane shift" from XPHB
- `studded leather armor|PHB|studded leather` - display name override
- `swarm of centipedes||swarm of insects (centipedes)` - creature with alternate display

#### Pattern 2: Property Codes with Source
- `V|XPHB` - Versatile property from XPHB
- `2H|XPHB` - Two-Handed property from XPHB
- `AF|DMG` - Ammunition (Firearm) from DMG

#### Pattern 3: Inline References (Should Stay in JSONB)
- `{@item studded leather armor|phb|studded leather}` - Markup tags
- `{@condition Charmed|XPHB}` - Condition references
- These appear in `entries[]`, `action[].entries[]`, etc.

### Distribution

| Dataset  | Pipe Count | Most Common Fields                           |
|----------|-----------|----------------------------------------------|
| Items    | 3,470     | `entries[]`, `lootTables[]`, `property[]`    |
| Monsters | 5,778     | `action[].entries[]`, `ac[].from[]`          |
| Spells   | 0         | None found ✅                                 |

### Decision: What to Clean

**CLEAN (normalize before DB import):**
- ✅ `property[]` - Strip source suffix: `V|XPHB` → `V`
- ✅ `baseItem` - Strip source: `sickle|PHB` → `sickle`
- ✅ `attachedSpells[]` - Strip source: `plane shift|xphb` → `plane shift`
- ✅ `attachedItems[]` - Strip source: `light crossbow|phb` → `light crossbow`
- ✅ `gear[]` - Strip source: `sling|xphb` → `sling`
- ✅ `packContents[].item` - Strip source

**PRESERVE (keep in JSONB):**
- ❌ `entries[]` - Contains rich markup, stay in JSONB
- ❌ `action[].entries[]` - Complex references, stay in JSONB
- ❌ `ac[].from[]` - Display text with formatting
- ❌ All `_versions[]` fields - Variant data

---

## 2. ABBREVIATION USAGE

### Fields Using Abbreviations

#### SOURCES (All datasets)
**Need full mapping table**

Examples:
- `PHB` → Player's Handbook
- `MM` → Monster Manual
- `XPHB` → 2024 Player's Handbook (revised)
- `XDMG` → 2024 Dungeon Master's Guide (revised)
- `XMM` → 2024 Monster Manual (revised)

**Total unique**: 100+ source codes

#### ITEM TYPES
**Need full mapping table**

Examples:
- `M` → Melee Weapon
- `R` → Ranged Weapon
- `A` → Armor
- `LA` → Light Armor
- `MA` → Medium Armor
- `HA` → Heavy Armor
- `$G` → Generic variant
- `SCF` → Spellcasting Focus

**Total unique**: 34 codes

#### ITEM PROPERTIES
**Need full mapping table**

Examples:
- `V` → Versatile
- `2H` → Two-Handed
- `F` → Finesse
- `L` → Light
- `T` → Thrown
- `H` → Heavy
- `A` → Ammunition
- `R` → Reach
- `LD` → Loading
- `RLD` → Reload
- `AF` → Ammunition (Firearm)
- `BF` → Burst Fire

**Total unique**: 27 codes (including pipe variants)

#### CREATURE SIZES
**Need mapping table**

- `T` → Tiny
- `S` → Small
- `M` → Medium
- `L` → Large
- `H` → Huge
- `G` → Gargantuan

#### ALIGNMENT VALUES
**Need mapping table**

- `L` → Lawful
- `N` → Neutral
- `C` → Chaotic
- `G` → Good
- `E` → Evil
- `U` → Unaligned
- `A` → Any
- `NX` → Neutral (Law/Chaos axis)
- `NY` → Neutral (Good/Evil axis)

#### SPELL SCHOOLS
**Need mapping table**

- `A` → Abjuration
- `C` → Conjuration
- `D` → Divination
- `E` → Enchantment
- `I` → Illusion
- `N` → Necromancy
- `T` → Transmutation
- `V` → Evocation

---

## 3. RECOMMENDED ACTIONS

### Phase 0.5b: Enhanced Cleaning

1. **Strip pipe suffixes from normalized fields**
   ```python
   # In clean_items.py
   if 'property' in item:
       cleaned['property'] = [p.split('|')[0] for p in item['property']]

   if 'baseItem' in item:
       cleaned['baseItem'] = item['baseItem'].split('|')[0]
   ```

2. **Create abbreviation mapping files**
   - `mappings/sources.json` - All source abbreviations
   - `mappings/item_types.json` - Item type codes
   - `mappings/item_properties.json` - Property codes
   - `mappings/sizes.json` - Size codes
   - `mappings/alignments.json` - Alignment codes
   - `mappings/schools.json` - Spell school codes

3. **Update schema.sql**
   - Add `display_name` column to all controlled vocabulary tables
   - Populate during import: code="V", name="Versatile"

### Phase 2: Import with Mappings

During import, use mapping files to populate lookup tables:

```python
# Load mapping
with open('mappings/item_properties.json') as f:
    prop_mapping = json.load(f)

# Import
for code, name in prop_mapping.items():
    cursor.execute(
        "INSERT INTO item_properties (code, name) VALUES (%s, %s)",
        (code, name)
    )
```

---

## 4. VALIDATION CHECKLIST

Before finalizing cleaning:

- [ ] Re-run `clean_all.py` with pipe stripping
- [ ] Verify `property[]` has no pipes: Should be `["V", "2H"]` not `["V|XPHB"]`
- [ ] Verify no duplicates after stripping (e.g., both `V` and `V|XPHB` → `V`)
- [ ] Create all mapping JSON files
- [ ] Update schema to include `display_name` columns
- [ ] Document which fields preserve pipes (JSONB text content)

---

## 5. QUESTIONS FOR USER

1. **Should we create the abbreviation mapping files now?**
   - We can extract them from the cleaned data
   - Need to research full names for codes

2. **Do we want to preserve source information?**
   - Option A: Strip entirely (`V|XPHB` → `V`)
   - Option B: Store separately (`property_sources` field)
   - **Recommendation**: Strip (source is already in `source` field)

3. **How to handle display name overrides?**
   - `studded leather armor|PHB|studded leather` - third part is display name
   - Should we extract this or ignore?
