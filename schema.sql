-- =============================================================================
-- 5etools PostgreSQL Schema
-- =============================================================================
-- Database: dnd5e_reference
-- Purpose: Import D&D 5e data from 5etools JSON files
-- Design: Hybrid normalization + JSONB for flexibility
-- =============================================================================

-- Clean start (development only - remove in production)
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;

-- =============================================================================
-- EXTENSIONS
-- =============================================================================

-- Enable trigram extension for fuzzy text search (must be created before use)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- =============================================================================
-- CONTROLLED VOCABULARY TABLES
-- =============================================================================
-- These enforce referential integrity and provide canonical lookup values

-- Sources (PHB, MM, XGE, etc.)
CREATE TABLE sources (
  id SERIAL PRIMARY KEY,
  code VARCHAR(20) UNIQUE NOT NULL,
  name TEXT NOT NULL,
  type VARCHAR(20),
  published_date DATE,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sources_code ON sources(code);

-- Item Types (M=Melee, R=Ranged, A=Armor, etc.)
CREATE TABLE item_types (
  id SERIAL PRIMARY KEY,
  code VARCHAR(10) UNIQUE NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Item Rarities
CREATE TABLE item_rarities (
  id SERIAL PRIMARY KEY,
  name VARCHAR(20) UNIQUE NOT NULL,
  sort_order INTEGER,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Damage Types (fire, cold, slashing, piercing, etc.)
CREATE TABLE damage_types (
  id SERIAL PRIMARY KEY,
  name VARCHAR(30) UNIQUE NOT NULL,
  category VARCHAR(20),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Creature Types (humanoid, beast, dragon, etc.)
CREATE TABLE creature_types (
  id SERIAL PRIMARY KEY,
  name VARCHAR(30) UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Creature Sizes
CREATE TABLE creature_sizes (
  id SERIAL PRIMARY KEY,
  code CHAR(1) UNIQUE NOT NULL,
  name VARCHAR(20) NOT NULL,
  space_feet INTEGER,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Alignment Values
CREATE TABLE alignment_values (
  id SERIAL PRIMARY KEY,
  code VARCHAR(5) UNIQUE NOT NULL,
  name VARCHAR(30) NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Spell Schools
CREATE TABLE spell_schools (
  id SERIAL PRIMARY KEY,
  code CHAR(1) UNIQUE NOT NULL,
  name VARCHAR(30) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Condition Types
CREATE TABLE condition_types (
  id SERIAL PRIMARY KEY,
  name VARCHAR(30) UNIQUE NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Skills
CREATE TABLE skills (
  id SERIAL PRIMARY KEY,
  name VARCHAR(30) UNIQUE NOT NULL,
  ability VARCHAR(10),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Item Properties (Finesse, Two-Handed, Versatile, etc.)
CREATE TABLE item_properties (
  id SERIAL PRIMARY KEY,
  code VARCHAR(10) UNIQUE NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Classes (for spell relationships)
CREATE TABLE classes (
  id SERIAL PRIMARY KEY,
  name VARCHAR(50) UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================================================
-- CORE ENTITY TABLES
-- =============================================================================

-- Items Table
CREATE TABLE items (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  source_id INTEGER REFERENCES sources(id),
  type_id INTEGER REFERENCES item_types(id),
  rarity_id INTEGER REFERENCES item_rarities(id),

  -- Normalized fields (frequently queried)
  value_cp INTEGER DEFAULT 0,
  weight_lbs NUMERIC(10,2) DEFAULT 0,
  requires_attunement BOOLEAN DEFAULT false,
  attunement_description TEXT DEFAULT '',

  -- Weapon/armor specific
  ac INTEGER,
  strength_requirement INTEGER DEFAULT 0,

  -- Normalized nested structures
  range_normal INTEGER DEFAULT 0,
  range_long INTEGER DEFAULT 0,

  -- SRD flags
  is_srd BOOLEAN DEFAULT false,
  is_srd52 BOOLEAN DEFAULT false,

  -- Full original JSON (for complex fields like entries, damage, etc.)
  data JSONB NOT NULL,

  -- Metadata
  source_file TEXT,
  created_at TIMESTAMP DEFAULT NOW(),

  -- Full-text search
  search_vector tsvector
);

CREATE INDEX idx_items_name ON items USING gin(to_tsvector('english', name));
CREATE INDEX idx_items_name_trgm ON items USING gin(name gin_trgm_ops);
CREATE INDEX idx_items_data ON items USING gin(data);
CREATE INDEX idx_items_search ON items USING gin(search_vector);
CREATE INDEX idx_items_rarity ON items(rarity_id);
CREATE INDEX idx_items_type ON items(type_id);
CREATE INDEX idx_items_source ON items(source_id);
CREATE INDEX idx_items_value ON items(value_cp);

-- Monsters Table
CREATE TABLE monsters (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  source_id INTEGER REFERENCES sources(id),
  type_id INTEGER REFERENCES creature_types(id),
  size_id INTEGER REFERENCES creature_sizes(id),

  -- Normalized stats
  cr NUMERIC(5,2) NOT NULL,
  hp_average INTEGER NOT NULL,
  hp_formula TEXT,
  ac_primary INTEGER NOT NULL,

  -- Speeds (in feet)
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

  -- SRD flags
  is_srd BOOLEAN DEFAULT false,
  is_srd52 BOOLEAN DEFAULT false,

  -- Full original JSON (for traits, actions, spellcasting, etc.)
  data JSONB NOT NULL,

  -- Metadata
  source_file TEXT,
  created_at TIMESTAMP DEFAULT NOW(),

  -- Full-text search
  search_vector tsvector
);

CREATE INDEX idx_monsters_name ON monsters USING gin(to_tsvector('english', name));
CREATE INDEX idx_monsters_name_trgm ON monsters USING gin(name gin_trgm_ops);
CREATE INDEX idx_monsters_cr ON monsters(cr);
CREATE INDEX idx_monsters_data ON monsters USING gin(data);
CREATE INDEX idx_monsters_search ON monsters USING gin(search_vector);
CREATE INDEX idx_monsters_type ON monsters(type_id);
CREATE INDEX idx_monsters_size ON monsters(size_id);
CREATE INDEX idx_monsters_source ON monsters(source_id);

-- Spells Table
CREATE TABLE spells (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  source_id INTEGER REFERENCES sources(id),
  school_id INTEGER REFERENCES spell_schools(id),

  -- Core properties
  level INTEGER NOT NULL CHECK (level >= 0 AND level <= 9),
  is_ritual BOOLEAN DEFAULT false,

  -- Casting time
  casting_time_number INTEGER,
  casting_time_unit TEXT,

  -- Range
  range_type TEXT,
  range_value INTEGER DEFAULT 0,
  range_unit TEXT DEFAULT '',

  -- Duration
  duration_type TEXT,
  duration_value INTEGER DEFAULT 0,
  duration_unit TEXT DEFAULT '',
  requires_concentration BOOLEAN DEFAULT false,

  -- Components
  component_v BOOLEAN DEFAULT false,
  component_s BOOLEAN DEFAULT false,
  component_m BOOLEAN DEFAULT false,
  component_m_text TEXT DEFAULT '',

  -- SRD flags
  is_srd BOOLEAN DEFAULT false,
  is_srd52 BOOLEAN DEFAULT false,

  -- Full original JSON (for entries, damage, scaling, etc.)
  data JSONB NOT NULL,

  -- Metadata
  source_file TEXT,
  created_at TIMESTAMP DEFAULT NOW(),

  -- Full-text search
  search_vector tsvector
);

CREATE INDEX idx_spells_name ON spells USING gin(to_tsvector('english', name));
CREATE INDEX idx_spells_name_trgm ON spells USING gin(name gin_trgm_ops);
CREATE INDEX idx_spells_level ON spells(level);
CREATE INDEX idx_spells_school ON spells(school_id);
CREATE INDEX idx_spells_data ON spells USING gin(data);
CREATE INDEX idx_spells_search ON spells USING gin(search_vector);
CREATE INDEX idx_spells_source ON spells(source_id);
CREATE INDEX idx_spells_concentration ON spells(requires_concentration);
CREATE INDEX idx_spells_ritual ON spells(is_ritual);

-- =============================================================================
-- JUNCTION TABLES (Many-to-Many Relationships)
-- =============================================================================

-- Item Properties (junction)
CREATE TABLE item_item_properties (
  item_id INTEGER REFERENCES items(id) ON DELETE CASCADE,
  property_id INTEGER REFERENCES item_properties(id),
  note TEXT DEFAULT '',
  PRIMARY KEY (item_id, property_id)
);

CREATE INDEX idx_item_props_item ON item_item_properties(item_id);
CREATE INDEX idx_item_props_property ON item_item_properties(property_id);

-- Monster Alignments (junction)
CREATE TABLE monster_alignments (
  monster_id INTEGER REFERENCES monsters(id) ON DELETE CASCADE,
  alignment_id INTEGER REFERENCES alignment_values(id),
  PRIMARY KEY (monster_id, alignment_id)
);

CREATE INDEX idx_monster_align_monster ON monster_alignments(monster_id);
CREATE INDEX idx_monster_align_alignment ON monster_alignments(alignment_id);

-- Monster Damage Resistances (junction)
CREATE TABLE monster_resistances (
  monster_id INTEGER REFERENCES monsters(id) ON DELETE CASCADE,
  damage_type_id INTEGER REFERENCES damage_types(id),
  PRIMARY KEY (monster_id, damage_type_id)
);

CREATE INDEX idx_monster_resist_monster ON monster_resistances(monster_id);
CREATE INDEX idx_monster_resist_damage ON monster_resistances(damage_type_id);

-- Monster Damage Immunities (junction)
CREATE TABLE monster_immunities (
  monster_id INTEGER REFERENCES monsters(id) ON DELETE CASCADE,
  damage_type_id INTEGER REFERENCES damage_types(id),
  PRIMARY KEY (monster_id, damage_type_id)
);

CREATE INDEX idx_monster_immune_monster ON monster_immunities(monster_id);
CREATE INDEX idx_monster_immune_damage ON monster_immunities(damage_type_id);

-- Monster Damage Vulnerabilities (junction)
CREATE TABLE monster_vulnerabilities (
  monster_id INTEGER REFERENCES monsters(id) ON DELETE CASCADE,
  damage_type_id INTEGER REFERENCES damage_types(id),
  PRIMARY KEY (monster_id, damage_type_id)
);

CREATE INDEX idx_monster_vuln_monster ON monster_vulnerabilities(monster_id);
CREATE INDEX idx_monster_vuln_damage ON monster_vulnerabilities(damage_type_id);

-- Monster Condition Immunities (junction)
CREATE TABLE monster_condition_immunities (
  monster_id INTEGER REFERENCES monsters(id) ON DELETE CASCADE,
  condition_id INTEGER REFERENCES condition_types(id),
  PRIMARY KEY (monster_id, condition_id)
);

CREATE INDEX idx_monster_cond_monster ON monster_condition_immunities(monster_id);
CREATE INDEX idx_monster_cond_condition ON monster_condition_immunities(condition_id);

-- Spell Classes (junction)
CREATE TABLE spell_classes (
  spell_id INTEGER REFERENCES spells(id) ON DELETE CASCADE,
  class_id INTEGER REFERENCES classes(id),
  PRIMARY KEY (spell_id, class_id)
);

CREATE INDEX idx_spell_class_spell ON spell_classes(spell_id);
CREATE INDEX idx_spell_class_class ON spell_classes(class_id);

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- Complete Items View
CREATE VIEW v_items_complete AS
SELECT
  i.id,
  i.name,
  s.code as source,
  it.name as item_type,
  r.name as rarity,
  i.value_cp,
  i.weight_lbs,
  i.requires_attunement,
  i.attunement_description,
  i.ac,
  i.strength_requirement,
  i.range_normal,
  i.range_long,
  i.is_srd,
  COALESCE(array_agg(DISTINCT ip.code) FILTER (WHERE ip.code IS NOT NULL), ARRAY[]::VARCHAR[]) as properties,
  i.data
FROM items i
LEFT JOIN sources s ON i.source_id = s.id
LEFT JOIN item_types it ON i.type_id = it.id
LEFT JOIN item_rarities r ON i.rarity_id = r.id
LEFT JOIN item_item_properties iip ON i.id = iip.item_id
LEFT JOIN item_properties ip ON iip.property_id = ip.id
GROUP BY i.id, s.code, it.name, r.name;

-- Complete Monsters View
CREATE VIEW v_monsters_complete AS
SELECT
  m.id,
  m.name,
  s.code as source,
  ct.name as creature_type,
  cs.name as size,
  m.cr,
  m.hp_average,
  m.hp_formula,
  m.ac_primary,
  m.speed_walk,
  m.speed_fly,
  m.speed_swim,
  m.speed_climb,
  m.speed_burrow,
  m.str, m.dex, m.con, m.int, m.wis, m.cha,
  m.passive_perception,
  m.is_srd,
  COALESCE(array_agg(DISTINCT av.code) FILTER (WHERE av.code IS NOT NULL), ARRAY[]::VARCHAR[]) as alignments,
  COALESCE(array_agg(DISTINCT dt_r.name) FILTER (WHERE dt_r.name IS NOT NULL), ARRAY[]::VARCHAR[]) as resistances,
  COALESCE(array_agg(DISTINCT dt_i.name) FILTER (WHERE dt_i.name IS NOT NULL), ARRAY[]::VARCHAR[]) as immunities,
  COALESCE(array_agg(DISTINCT dt_v.name) FILTER (WHERE dt_v.name IS NOT NULL), ARRAY[]::VARCHAR[]) as vulnerabilities,
  COALESCE(array_agg(DISTINCT cond.name) FILTER (WHERE cond.name IS NOT NULL), ARRAY[]::VARCHAR[]) as condition_immunities,
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
LEFT JOIN monster_vulnerabilities mv ON m.id = mv.monster_id
LEFT JOIN damage_types dt_v ON mv.damage_type_id = dt_v.id
LEFT JOIN monster_condition_immunities mci ON m.id = mci.monster_id
LEFT JOIN condition_types cond ON mci.condition_id = cond.id
GROUP BY m.id, s.code, ct.name, cs.name;

-- Complete Spells View
CREATE VIEW v_spells_complete AS
SELECT
  sp.id,
  sp.name,
  s.code as source,
  sch.name as school,
  sp.level,
  sp.is_ritual,
  sp.casting_time_number,
  sp.casting_time_unit,
  sp.range_type,
  sp.range_value,
  sp.range_unit,
  sp.duration_type,
  sp.duration_value,
  sp.duration_unit,
  sp.requires_concentration,
  sp.component_v,
  sp.component_s,
  sp.component_m,
  sp.component_m_text,
  sp.is_srd,
  COALESCE(array_agg(DISTINCT c.name) FILTER (WHERE c.name IS NOT NULL), ARRAY[]::VARCHAR[]) as classes,
  sp.data
FROM spells sp
LEFT JOIN sources s ON sp.source_id = s.id
LEFT JOIN spell_schools sch ON sp.school_id = sch.id
LEFT JOIN spell_classes sc ON sp.id = sc.spell_id
LEFT JOIN classes c ON sc.class_id = c.id
GROUP BY sp.id, s.code, sch.name;

-- =============================================================================
-- USEFUL QUERY FUNCTIONS
-- =============================================================================

-- Function to search items by name (fuzzy)
CREATE OR REPLACE FUNCTION search_items(search_term TEXT)
RETURNS TABLE (
  id INTEGER,
  name TEXT,
  similarity REAL
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    i.id,
    i.name,
    similarity(i.name, search_term) as sim
  FROM items i
  WHERE i.name % search_term
  ORDER BY sim DESC, i.name
  LIMIT 20;
END;
$$ LANGUAGE plpgsql;

-- Function to search monsters by name (fuzzy)
CREATE OR REPLACE FUNCTION search_monsters(search_term TEXT)
RETURNS TABLE (
  id INTEGER,
  name TEXT,
  similarity REAL
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    m.id,
    m.name,
    similarity(m.name, search_term) as sim
  FROM monsters m
  WHERE m.name % search_term
  ORDER BY sim DESC, m.name
  LIMIT 20;
END;
$$ LANGUAGE plpgsql;

-- Function to search spells by name (fuzzy)
CREATE OR REPLACE FUNCTION search_spells(search_term TEXT)
RETURNS TABLE (
  id INTEGER,
  name TEXT,
  similarity REAL
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    s.id,
    s.name,
    similarity(s.name, search_term) as sim
  FROM spells s
  WHERE s.name % search_term
  ORDER BY sim DESC, s.name
  LIMIT 20;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- GRANTS
-- =============================================================================

-- Grant SELECT to dndbot user (for cross-project queries)
GRANT SELECT ON ALL TABLES IN SCHEMA public TO dndbot;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO dndbot;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE items IS 'All D&D 5e items (base items + magic items)';
COMMENT ON TABLE monsters IS 'All D&D 5e monster stat blocks';
COMMENT ON TABLE spells IS 'All D&D 5e spell definitions';

COMMENT ON COLUMN items.data IS 'Full original JSON from 5etools (entries, damage, special properties)';
COMMENT ON COLUMN monsters.data IS 'Full original JSON from 5etools (traits, actions, legendary actions, spellcasting)';
COMMENT ON COLUMN spells.data IS 'Full original JSON from 5etools (entries, damage, scaling, higher levels)';

COMMENT ON COLUMN items.value_cp IS 'Item value in copper pieces (gp * 100)';
COMMENT ON COLUMN items.weight_lbs IS 'Item weight in pounds';

COMMENT ON COLUMN monsters.cr IS 'Challenge Rating (0.125 to 30+)';
COMMENT ON COLUMN monsters.hp_average IS 'Average hit points';
COMMENT ON COLUMN monsters.hp_formula IS 'HP dice formula (e.g., "2d8+6")';

COMMENT ON COLUMN spells.level IS 'Spell level: 0 (cantrip) through 9';
