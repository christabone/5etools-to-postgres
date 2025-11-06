# Controlled Vocabulary (Ontology) for 5etools Database

This document lists all controlled vocabularies (enums/lookup tables) needed for the database schema.

**Source**: Extracted from 5etools v2.15.0 data during Phase 0 and Phase 0.6

---

## 1. Sources (115 unique)

Source books and supplements. These are abbreviated codes.

**Usage**: Referenced by all entity types (items, monsters, spells)

**Sample values**:
- `PHB` - Player's Handbook
- `MM` - Monster Manual
- `DMG` - Dungeon Master's Guide
- `XPHB` - Player's Handbook (2024)
- `XMM` - Monster Manual (2024)
- `XDMG` - Dungeon Master's Guide (2024)
- `BAM` - Boo's Astral Menagerie
- `BGG` - Bigby Presents: Glory of the Giants
- Plus 107 more adventure modules and supplements

**Database Table**: `sources`

```sql
CREATE TABLE sources (
  id SERIAL PRIMARY KEY,
  code VARCHAR(20) UNIQUE NOT NULL,
  name TEXT,
  type VARCHAR(20),  -- 'core', 'supplement', 'adventure'
  published_date DATE
);
```

---

## 2. Rarities (10 unique)

Item rarity levels.

**Values**:
- `none` - Common/mundane items
- `common` - Common magic items
- `uncommon`
- `rare`
- `very rare`
- `legendary`
- `artifact`
- `unknown`
- `unknown (magic)`
- `varies`

**Database Table**: `item_rarities`

```sql
CREATE TABLE item_rarities (
  id SERIAL PRIMARY KEY,
  code VARCHAR(20) UNIQUE NOT NULL,
  name TEXT NOT NULL,
  sort_order INTEGER
);
```

---

## 3. Item Types (63 unique)

Equipment and item categories. Abbreviated codes with optional source suffix.

**Common values**:
- `M` - Melee weapon
- `R` - Ranged weapon
- `A` - Armor
- `LA` - Light armor
- `MA` - Medium armor
- `HA` - Heavy armor
- `S` - Shield
- `G` - Adventuring gear
- `INS` - Instrument
- `SCF` - Spellcasting focus
- `T` - Tool
- `AF` - Ammunition (firearm)
- Plus 51 more variants with source suffixes

**Database Table**: `item_types`

```sql
CREATE TABLE item_types (
  id SERIAL PRIMARY KEY,
  code VARCHAR(20) UNIQUE NOT NULL,
  name TEXT NOT NULL,
  category TEXT  -- 'weapon', 'armor', 'gear', etc.
);
```

---

## 4. Damage Types (13 unique)

Damage types from extracted damage records.

**Values**:
- Physical: `bludgeoning`, `piercing`, `slashing`
- Elemental: `acid`, `cold`, `fire`, `lightning`, `poison`, `thunder`
- Magical: `force`, `necrotic`, `psychic`, `radiant`

**Database Table**: `damage_types`

```sql
CREATE TABLE damage_types (
  id SERIAL PRIMARY KEY,
  code VARCHAR(20) UNIQUE NOT NULL,
  name TEXT NOT NULL,
  category TEXT  -- 'physical', 'elemental', 'magical'
);
```

**Note**: Also need short codes (B, P, S, etc.) for item damage type mapping:
- `B` → bludgeoning
- `P` → piercing
- `S` → slashing
- `N` → necrotic
- `R` → radiant
- `F` → fire
- `C` → cold
- `L` → lightning
- `T` → thunder
- `A` → acid
- `I` → poison (note: "I" not "P")
- `O` → force
- `Y` → psychic

---

## 5. Conditions (15 unique)

Status conditions from extracted condition references.

**Values**:
- `blinded`
- `charmed`
- `deafened`
- `exhaustion`
- `frightened`
- `grappled`
- `incapacitated`
- `invisible`
- `paralyzed`
- `petrified`
- `poisoned`
- `prone`
- `restrained`
- `stunned`
- `unconscious`

**Database Table**: `condition_types`

```sql
CREATE TABLE condition_types (
  id SERIAL PRIMARY KEY,
  code VARCHAR(20) UNIQUE NOT NULL,
  name TEXT NOT NULL,
  description TEXT
);
```

---

## 6. Creature Types (14 unique)

Monster/creature classifications.

**Values**:
- `aberration`
- `beast`
- `celestial`
- `construct`
- `dragon`
- `elemental`
- `fey`
- `fiend`
- `giant`
- `humanoid`
- `monstrosity`
- `ooze`
- `plant`
- `undead`

**Database Table**: `creature_types`

```sql
CREATE TABLE creature_types (
  id SERIAL PRIMARY KEY,
  code VARCHAR(20) UNIQUE NOT NULL,
  name TEXT NOT NULL
);
```

---

## 7. Creature Sizes (6 unique)

Monster size categories.

**Values**:
- `T` - Tiny
- `S` - Small
- `M` - Medium
- `L` - Large
- `H` - Huge
- `G` - Gargantuan

**Database Table**: `creature_sizes`

```sql
CREATE TABLE creature_sizes (
  id SERIAL PRIMARY KEY,
  code VARCHAR(1) UNIQUE NOT NULL,
  name TEXT NOT NULL,
  space_ft INTEGER  -- Space occupied in feet
);
```

---

## 8. Spell Schools (8 unique)

Schools of magic.

**Values**:
- `A` - Abjuration
- `C` - Conjuration
- `D` - Divination
- `E` - Enchantment
- `I` - Illusion
- `N` - Necromancy
- `T` - Transmutation
- `V` - Evocation

**Database Table**: `spell_schools`

```sql
CREATE TABLE spell_schools (
  id SERIAL PRIMARY KEY,
  code VARCHAR(1) UNIQUE NOT NULL,
  name TEXT NOT NULL,
  description TEXT
);
```

---

## 9. Alignment Values

Creature alignment components (extracted from monster data analysis).

**Values**:
- `L` - Lawful
- `N` - Neutral
- `C` - Chaotic
- `G` - Good
- `E` - Evil
- `U` - Unaligned
- `A` - Any alignment

**Database Table**: `alignment_values`

```sql
CREATE TABLE alignment_values (
  id SERIAL PRIMARY KEY,
  code VARCHAR(1) UNIQUE NOT NULL,
  name TEXT NOT NULL,
  axis TEXT  -- 'law-chaos', 'good-evil', 'special'
);
```

**Note**: Monsters can have multiple alignment values (e.g., "L,G" = Lawful Good)

---

## 10. Attack Types (7 unique)

Types of attacks from extracted monster attacks.

**Values**:
- `melee weapon`
- `ranged weapon`
- `melee or ranged weapon`
- `melee spell`
- `ranged spell`
- `melee or ranged spell`
- `m` (unknown/malformed)

**Database Table**: `attack_types`

```sql
CREATE TABLE attack_types (
  id SERIAL PRIMARY KEY,
  code VARCHAR(30) UNIQUE NOT NULL,
  name TEXT NOT NULL
);
```

---

## 11. Skills (18 standard D&D skills)

Character skills (needed for monster proficiencies).

**Values**:
- `Acrobatics`
- `Animal Handling`
- `Arcana`
- `Athletics`
- `Deception`
- `History`
- `Insight`
- `Intimidation`
- `Investigation`
- `Medicine`
- `Nature`
- `Perception`
- `Performance`
- `Persuasion`
- `Religion`
- `Sleight of Hand`
- `Stealth`
- `Survival`

**Database Table**: `skills`

```sql
CREATE TABLE skills (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  ability VARCHAR(3)  -- STR, DEX, CON, INT, WIS, CHA
);
```

---

## 12. Abilities (6 core ability scores)

The six ability scores.

**Values**:
- `STR` - Strength
- `DEX` - Dexterity
- `CON` - Constitution
- `INT` - Intelligence
- `WIS` - Wisdom
- `CHA` - Charisma

**Database Table**: Not needed (hardcoded in schema, only 6 values)

---

## 13. Item Properties

Weapon properties (from items with property arrays).

**Common values** (need to extract full list):
- `F` - Finesse
- `2H` - Two-handed
- `V` - Versatile
- `H` - Heavy
- `L` - Light
- `T` - Thrown
- `R` - Reach
- `LD` - Loading
- `A` - Ammunition
- `RLD` - Reload
- Plus more

**Database Table**: `item_properties`

```sql
CREATE TABLE item_properties (
  id SERIAL PRIMARY KEY,
  code VARCHAR(10) UNIQUE NOT NULL,
  name TEXT NOT NULL,
  description TEXT
);
```

---

## 14. Weapon Categories

Weapon proficiency categories.

**Values**:
- `simple`
- `martial`

**Database Table**: Not needed (can be VARCHAR field on items table)

---

## 15. Armor Categories

Armor proficiency categories.

**Values**:
- `light`
- `medium`
- `heavy`

**Database Table**: Not needed (can be derived from item type)

---

## Summary

**Total Controlled Vocabularies**: 15 categories

**Largest vocabularies**:
1. Sources: 115 values
2. Item Types: 63 values
3. Creature Types: 14 values
4. Damage Types: 13 values
5. Conditions: 15 values

**Smallest vocabularies**:
1. Creature Sizes: 6 values
2. Abilities: 6 values
3. Spell Schools: 8 values

**Next Steps**:
1. Create `import_controlled_vocab.py` to populate these lookup tables
2. Map short codes to full names (e.g., damage type codes)
3. Add descriptions/metadata where available
4. Create proper foreign key relationships in schema

---

**Generated from**: Phase 0 analysis + Phase 0.6 extraction
**Data Version**: 5etools v2.15.0
**Date**: 2025-11-06
