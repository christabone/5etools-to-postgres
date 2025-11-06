-- 5etools to PostgreSQL Schema
-- Normalized database with controlled vocabulary for D&D 5e reference data

-- ============================================================
-- CONTROLLED VOCABULARY / ONTOLOGY TABLES
-- ============================================================

-- Source books (PHB, MM, DMG, etc.)
CREATE TABLE sources (
    id SERIAL PRIMARY KEY,
    abbreviation VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sources_abbr ON sources(abbreviation);

-- Item types (M = Melee Weapon, R = Ranged Weapon, LA = Light Armor, etc.)
CREATE TABLE item_types (
    id SERIAL PRIMARY KEY,
    abbreviation VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50), -- weapon, armor, gear, treasure, vehicle
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_item_types_abbr ON item_types(abbreviation);
CREATE INDEX idx_item_types_category ON item_types(category);

-- Item properties (Light, Heavy, Finesse, Versatile, etc.)
CREATE TABLE item_properties (
    id SERIAL PRIMARY KEY,
    abbreviation VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_item_properties_abbr ON item_properties(abbreviation);

-- Weapon mastery types (Nick, Push, Sap, Topple, etc.)
CREATE TABLE weapon_masteries (
    id SERIAL PRIMARY KEY,
    abbreviation VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Damage types (Slashing, Piercing, Bludgeoning, Fire, etc.)
CREATE TABLE damage_types (
    id SERIAL PRIMARY KEY,
    abbreviation VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(50) NOT NULL,
    physical BOOLEAN DEFAULT FALSE, -- True for S, P, B
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_damage_types_abbr ON damage_types(abbreviation);

-- Rarity levels
CREATE TABLE rarity_levels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    sort_order INTEGER NOT NULL, -- none=0, common=1, uncommon=2, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rarity_levels_name ON rarity_levels(name);

-- Magic schools (Evocation, Conjuration, Abjuration, etc.)
CREATE TABLE magic_schools (
    id SERIAL PRIMARY KEY,
    abbreviation VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_magic_schools_abbr ON magic_schools(abbreviation);

-- Creature sizes (Tiny, Small, Medium, Large, Huge, Gargantuan)
CREATE TABLE creature_sizes (
    id SERIAL PRIMARY KEY,
    abbreviation VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(20) NOT NULL,
    space_feet NUMERIC(4,1), -- Space in feet (e.g., 5, 10, 15)
    sort_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_creature_sizes_abbr ON creature_sizes(abbreviation);

-- Creature types (Humanoid, Beast, Dragon, etc.)
CREATE TABLE creature_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_creature_types_name ON creature_types(name);

-- Alignments (LG, NG, CG, LN, N, CN, LE, NE, CE, U, A, etc.)
CREATE TABLE alignments (
    id SERIAL PRIMARY KEY,
    abbreviation VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alignments_abbr ON alignments(abbreviation);

-- Conditions (Blinded, Charmed, Deafened, etc.)
CREATE TABLE conditions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conditions_name ON conditions(name);

-- Senses (darkvision, blindsight, tremorsense, truesight)
CREATE TABLE sense_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Languages (Common, Elvish, Draconic, etc.)
CREATE TABLE languages (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    script VARCHAR(50),
    typical_speakers TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_languages_name ON languages(name);

-- Skills (Acrobatics, Animal Handling, etc.)
CREATE TABLE skills (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    ability_score VARCHAR(20) NOT NULL, -- STR, DEX, CON, INT, WIS, CHA
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_skills_name ON skills(name);


-- ============================================================
-- CORE DATA TABLES
-- ============================================================

-- Items (weapons, armor, gear, magic items)
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    source_id INTEGER REFERENCES sources(id),
    page INTEGER,

    -- Classification
    item_type_id INTEGER REFERENCES item_types(id),
    rarity_id INTEGER REFERENCES rarity_levels(id),

    -- Physical properties
    weight NUMERIC(10, 2), -- in pounds
    value INTEGER, -- in copper pieces

    -- Weapon-specific
    weapon_category VARCHAR(20), -- simple, martial
    damage VARCHAR(20), -- e.g., "1d8"
    damage2 VARCHAR(20), -- versatile damage
    damage_type_id INTEGER REFERENCES damage_types(id),
    range_normal INTEGER, -- in feet
    range_long INTEGER, -- in feet

    -- Armor-specific
    armor_class INTEGER, -- base AC
    strength_requirement INTEGER, -- minimum STR
    stealth_disadvantage BOOLEAN DEFAULT FALSE,

    -- Magic item specific
    requires_attunement BOOLEAN DEFAULT FALSE,
    charges INTEGER,
    recharge VARCHAR(50),

    -- Metadata
    srd BOOLEAN DEFAULT FALSE,
    basic_rules BOOLEAN DEFAULT FALSE,
    legacy BOOLEAN DEFAULT FALSE,

    -- Full JSON data for flexibility
    data JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_items_name ON items(name);
CREATE INDEX idx_items_source ON items(source_id);
CREATE INDEX idx_items_type ON items(item_type_id);
CREATE INDEX idx_items_rarity ON items(rarity_id);
CREATE INDEX idx_items_srd ON items(srd);
CREATE INDEX idx_items_data ON items USING GIN(data);

-- Item properties (many-to-many)
CREATE TABLE item_property_map (
    id SERIAL PRIMARY KEY,
    item_id INTEGER REFERENCES items(id) ON DELETE CASCADE,
    property_id INTEGER REFERENCES item_properties(id),
    UNIQUE(item_id, property_id)
);

CREATE INDEX idx_item_property_map_item ON item_property_map(item_id);
CREATE INDEX idx_item_property_map_property ON item_property_map(property_id);

-- Item masteries (many-to-many)
CREATE TABLE item_mastery_map (
    id SERIAL PRIMARY KEY,
    item_id INTEGER REFERENCES items(id) ON DELETE CASCADE,
    mastery_id INTEGER REFERENCES weapon_masteries(id),
    UNIQUE(item_id, mastery_id)
);

CREATE INDEX idx_item_mastery_map_item ON item_mastery_map(item_id);
CREATE INDEX idx_item_mastery_map_mastery ON item_mastery_map(mastery_id);


-- Monsters/Creatures
CREATE TABLE monsters (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    source_id INTEGER REFERENCES sources(id),
    page INTEGER,

    -- Basic info
    size_id INTEGER REFERENCES creature_sizes(id),
    type_id INTEGER REFERENCES creature_types(id),
    cr VARCHAR(10) NOT NULL, -- Challenge Rating (can be fraction like "1/2")

    -- Combat stats
    ac INTEGER,
    ac_special VARCHAR(255), -- e.g., "13 (natural armor)"
    hp_avg INTEGER,
    hp_formula VARCHAR(50),

    -- Ability scores
    str INTEGER NOT NULL,
    dex INTEGER NOT NULL,
    con INTEGER NOT NULL,
    int INTEGER NOT NULL,
    wis INTEGER NOT NULL,
    cha INTEGER NOT NULL,

    -- Movement
    speed_walk INTEGER,
    speed_fly INTEGER,
    speed_swim INTEGER,
    speed_burrow INTEGER,
    speed_climb INTEGER,
    speed_special JSONB, -- hover, etc.

    -- Senses
    passive_perception INTEGER,

    -- Metadata
    srd BOOLEAN DEFAULT FALSE,
    basic_rules BOOLEAN DEFAULT FALSE,
    legendary BOOLEAN DEFAULT FALSE,
    unique_creature BOOLEAN DEFAULT FALSE, -- Named NPCs

    -- Full JSON data
    data JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_monsters_name ON monsters(name);
CREATE INDEX idx_monsters_source ON monsters(source_id);
CREATE INDEX idx_monsters_cr ON monsters(cr);
CREATE INDEX idx_monsters_type ON monsters(type_id);
CREATE INDEX idx_monsters_size ON monsters(size_id);
CREATE INDEX idx_monsters_srd ON monsters(srd);
CREATE INDEX idx_monsters_data ON monsters USING GIN(data);

-- Monster alignments (many-to-many, as some monsters can be "any alignment")
CREATE TABLE monster_alignments (
    id SERIAL PRIMARY KEY,
    monster_id INTEGER REFERENCES monsters(id) ON DELETE CASCADE,
    alignment_id INTEGER REFERENCES alignments(id),
    UNIQUE(monster_id, alignment_id)
);

CREATE INDEX idx_monster_alignments_monster ON monster_alignments(monster_id);
CREATE INDEX idx_monster_alignments_alignment ON monster_alignments(alignment_id);

-- Monster languages (many-to-many)
CREATE TABLE monster_languages (
    id SERIAL PRIMARY KEY,
    monster_id INTEGER REFERENCES monsters(id) ON DELETE CASCADE,
    language_id INTEGER REFERENCES languages(id),
    notes VARCHAR(255), -- e.g., "can't speak"
    UNIQUE(monster_id, language_id)
);

CREATE INDEX idx_monster_languages_monster ON monster_languages(monster_id);
CREATE INDEX idx_monster_languages_language ON monster_languages(language_id);

-- Monster senses (many-to-many with range)
CREATE TABLE monster_senses (
    id SERIAL PRIMARY KEY,
    monster_id INTEGER REFERENCES monsters(id) ON DELETE CASCADE,
    sense_type_id INTEGER REFERENCES sense_types(id),
    range_feet INTEGER,
    UNIQUE(monster_id, sense_type_id)
);

CREATE INDEX idx_monster_senses_monster ON monster_senses(monster_id);

-- Monster skills (with proficiency bonus included)
CREATE TABLE monster_skills (
    id SERIAL PRIMARY KEY,
    monster_id INTEGER REFERENCES monsters(id) ON DELETE CASCADE,
    skill_id INTEGER REFERENCES skills(id),
    bonus INTEGER NOT NULL, -- Total bonus including proficiency
    UNIQUE(monster_id, skill_id)
);

CREATE INDEX idx_monster_skills_monster ON monster_skills(monster_id);
CREATE INDEX idx_monster_skills_skill ON monster_skills(skill_id);

-- Monster damage resistances/immunities/vulnerabilities
CREATE TABLE monster_damage_modifiers (
    id SERIAL PRIMARY KEY,
    monster_id INTEGER REFERENCES monsters(id) ON DELETE CASCADE,
    damage_type_id INTEGER REFERENCES damage_types(id),
    modifier_type VARCHAR(20) NOT NULL, -- resistance, immunity, vulnerability
    condition TEXT, -- e.g., "from nonmagical attacks"
    UNIQUE(monster_id, damage_type_id, modifier_type)
);

CREATE INDEX idx_monster_damage_mods_monster ON monster_damage_modifiers(monster_id);
CREATE INDEX idx_monster_damage_mods_type ON monster_damage_modifiers(damage_type_id);

-- Monster condition immunities (many-to-many)
CREATE TABLE monster_condition_immunities (
    id SERIAL PRIMARY KEY,
    monster_id INTEGER REFERENCES monsters(id) ON DELETE CASCADE,
    condition_id INTEGER REFERENCES conditions(id),
    UNIQUE(monster_id, condition_id)
);

CREATE INDEX idx_monster_condition_immunities_monster ON monster_condition_immunities(monster_id);


-- Spells
CREATE TABLE spells (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    source_id INTEGER REFERENCES sources(id),
    page INTEGER,

    -- Basic info
    level INTEGER NOT NULL CHECK (level >= 0 AND level <= 9),
    school_id INTEGER REFERENCES magic_schools(id),

    -- Casting
    casting_time VARCHAR(100),
    ritual BOOLEAN DEFAULT FALSE,

    -- Components
    component_verbal BOOLEAN DEFAULT FALSE,
    component_somatic BOOLEAN DEFAULT FALSE,
    component_material BOOLEAN DEFAULT FALSE,
    material_components TEXT,
    material_consumed BOOLEAN DEFAULT FALSE,
    material_cost INTEGER, -- in cp

    -- Range & Duration
    range_type VARCHAR(50), -- self, touch, point, special
    range_distance INTEGER, -- in feet
    duration_type VARCHAR(50), -- instant, time, concentration, special
    duration_amount INTEGER,
    duration_unit VARCHAR(20), -- round, minute, hour, day
    concentration BOOLEAN DEFAULT FALSE,

    -- Effects
    description TEXT NOT NULL,
    higher_levels TEXT,

    -- Metadata
    srd BOOLEAN DEFAULT FALSE,
    basic_rules BOOLEAN DEFAULT FALSE,

    -- Full JSON data
    data JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_spells_name ON spells(name);
CREATE INDEX idx_spells_source ON spells(source_id);
CREATE INDEX idx_spells_level ON spells(level);
CREATE INDEX idx_spells_school ON spells(school_id);
CREATE INDEX idx_spells_srd ON spells(srd);
CREATE INDEX idx_spells_data ON spells USING GIN(data);

-- Spell damage types (many-to-many)
CREATE TABLE spell_damage_types (
    id SERIAL PRIMARY KEY,
    spell_id INTEGER REFERENCES spells(id) ON DELETE CASCADE,
    damage_type_id INTEGER REFERENCES damage_types(id),
    UNIQUE(spell_id, damage_type_id)
);

CREATE INDEX idx_spell_damage_types_spell ON spell_damage_types(spell_id);
CREATE INDEX idx_spell_damage_types_damage ON spell_damage_types(damage_type_id);


-- ============================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_items_updated_at BEFORE UPDATE ON items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_monsters_updated_at BEFORE UPDATE ON monsters
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_spells_updated_at BEFORE UPDATE ON spells
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ============================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================

-- Full item details with lookups resolved
CREATE VIEW items_detailed AS
SELECT
    i.id,
    i.name,
    s.abbreviation as source,
    s.full_name as source_name,
    i.page,
    it.name as item_type,
    it.category as item_category,
    r.name as rarity,
    i.weight,
    i.value,
    i.weapon_category,
    i.damage,
    i.damage2,
    dt.name as damage_type,
    i.range_normal,
    i.range_long,
    i.armor_class,
    i.strength_requirement,
    i.stealth_disadvantage,
    i.requires_attunement,
    i.srd,
    i.basic_rules,
    -- Aggregate properties as array
    ARRAY_AGG(DISTINCT ip.name) FILTER (WHERE ip.name IS NOT NULL) as properties,
    -- Aggregate masteries as array
    ARRAY_AGG(DISTINCT wm.name) FILTER (WHERE wm.name IS NOT NULL) as masteries
FROM items i
LEFT JOIN sources s ON i.source_id = s.id
LEFT JOIN item_types it ON i.item_type_id = it.id
LEFT JOIN rarity_levels r ON i.rarity_id = r.id
LEFT JOIN damage_types dt ON i.damage_type_id = dt.id
LEFT JOIN item_property_map ipm ON i.id = ipm.item_id
LEFT JOIN item_properties ip ON ipm.property_id = ip.id
LEFT JOIN item_mastery_map imm ON i.id = imm.item_id
LEFT JOIN weapon_masteries wm ON imm.mastery_id = wm.id
GROUP BY i.id, s.abbreviation, s.full_name, it.name, it.category, r.name, dt.name;

-- Full monster details with lookups resolved
CREATE VIEW monsters_detailed AS
SELECT
    m.id,
    m.name,
    s.abbreviation as source,
    cs.name as size,
    ct.name as type,
    m.cr,
    m.ac,
    m.hp_avg,
    m.hp_formula,
    m.str, m.dex, m.con, m.int, m.wis, m.cha,
    m.speed_walk, m.speed_fly, m.speed_swim,
    m.passive_perception,
    m.srd,
    m.legendary,
    -- Aggregate alignments
    ARRAY_AGG(DISTINCT a.name) FILTER (WHERE a.name IS NOT NULL) as alignments,
    -- Aggregate languages
    ARRAY_AGG(DISTINCT l.name) FILTER (WHERE l.name IS NOT NULL) as languages
FROM monsters m
LEFT JOIN sources s ON m.source_id = s.id
LEFT JOIN creature_sizes cs ON m.size_id = cs.id
LEFT JOIN creature_types ct ON m.type_id = ct.id
LEFT JOIN monster_alignments ma ON m.id = ma.monster_id
LEFT JOIN alignments a ON ma.alignment_id = a.id
LEFT JOIN monster_languages ml ON m.id = ml.monster_id
LEFT JOIN languages l ON ml.language_id = l.id
GROUP BY m.id, s.abbreviation, cs.name, ct.name;

-- Full spell details with lookups resolved
CREATE VIEW spells_detailed AS
SELECT
    sp.id,
    sp.name,
    s.abbreviation as source,
    sp.level,
    ms.name as school,
    sp.casting_time,
    sp.ritual,
    sp.component_verbal,
    sp.component_somatic,
    sp.component_material,
    sp.material_components,
    sp.range_type,
    sp.range_distance,
    sp.duration_type,
    sp.concentration,
    sp.description,
    sp.higher_levels,
    sp.srd,
    -- Aggregate damage types
    ARRAY_AGG(DISTINCT dt.name) FILTER (WHERE dt.name IS NOT NULL) as damage_types
FROM spells sp
LEFT JOIN sources s ON sp.source_id = s.id
LEFT JOIN magic_schools ms ON sp.school_id = ms.id
LEFT JOIN spell_damage_types sdt ON sp.id = sdt.spell_id
LEFT JOIN damage_types dt ON sdt.damage_type_id = dt.id
GROUP BY sp.id, s.abbreviation, ms.name;
