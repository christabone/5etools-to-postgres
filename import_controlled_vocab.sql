-- Import Controlled Vocabulary Data
-- Run with: sudo -u postgres psql -d dnd5e_reference -f import_controlled_vocab.sql

\echo '================================================================================'
\echo 'CONTROLLED VOCABULARY IMPORT'
\echo '================================================================================'

-- Note: Sources already imported (126 records) via Python script

-- Import item rarities
\echo ''
\echo '💎 Importing item rarities...'
INSERT INTO item_rarities (name, sort_order) VALUES
('none', 0),
('common', 1),
('uncommon', 2),
('rare', 3),
('very rare', 4),
('legendary', 5),
('artifact', 6),
('unknown', 7),
('unknown (magic)', 8),
('varies', 9)
ON CONFLICT (name) DO NOTHING;

SELECT COUNT(*) || ' rarities imported' FROM item_rarities;

-- Import damage types
\echo ''
\echo '🔥 Importing damage types...'
INSERT INTO damage_types (name, category) VALUES
('bludgeoning', 'physical'),
('piercing', 'physical'),
('slashing', 'physical'),
('acid', 'elemental'),
('cold', 'elemental'),
('fire', 'elemental'),
('lightning', 'elemental'),
('poison', 'elemental'),
('thunder', 'elemental'),
('force', 'magical'),
('necrotic', 'magical'),
('psychic', 'magical'),
('radiant', 'magical')
ON CONFLICT (name) DO NOTHING;

SELECT COUNT(*) || ' damage types imported' FROM damage_types;

-- Import condition types
\echo ''
\echo '🤢 Importing condition types...'
INSERT INTO condition_types (name, description) VALUES
('blinded', 'Vision impaired'),
('charmed', 'Friendly to charmer'),
('deafened', 'Hearing impaired'),
('exhaustion', 'Multiple levels of fatigue'),
('frightened', 'Disadvantage while source visible'),
('grappled', 'Speed is 0'),
('incapacitated', 'Cannot take actions or reactions'),
('invisible', 'Cannot be seen'),
('paralyzed', 'Incapacitated and auto-fail STR/DEX saves'),
('petrified', 'Transformed into stone'),
('poisoned', 'Disadvantage on attacks and ability checks'),
('prone', 'Lying down, disadvantage on attacks'),
('restrained', 'Speed is 0, disadvantage on attacks'),
('stunned', 'Incapacitated and auto-fail STR/DEX saves'),
('unconscious', 'Incapacitated, prone, unaware')
ON CONFLICT (name) DO NOTHING;

SELECT COUNT(*) || ' condition types imported' FROM condition_types;

-- Import creature types
\echo ''
\echo '🐉 Importing creature types...'
INSERT INTO creature_types (name) VALUES
('aberration'),
('beast'),
('celestial'),
('construct'),
('dragon'),
('elemental'),
('fey'),
('fiend'),
('giant'),
('humanoid'),
('monstrosity'),
('ooze'),
('plant'),
('undead')
ON CONFLICT (name) DO NOTHING;

SELECT COUNT(*) || ' creature types imported' FROM creature_types;

-- Import creature sizes
\echo ''
\echo '📏 Importing creature sizes...'
INSERT INTO creature_sizes (code, name, space_feet) VALUES
('T', 'Tiny', 2),
('S', 'Small', 5),
('M', 'Medium', 5),
('L', 'Large', 10),
('H', 'Huge', 15),
('G', 'Gargantuan', 20)
ON CONFLICT (code) DO NOTHING;

SELECT COUNT(*) || ' creature sizes imported' FROM creature_sizes;

-- Import spell schools
\echo ''
\echo '✨ Importing spell schools...'
INSERT INTO spell_schools (code, name) VALUES
('A', 'Abjuration'),
('C', 'Conjuration'),
('D', 'Divination'),
('E', 'Enchantment'),
('I', 'Illusion'),
('N', 'Necromancy'),
('T', 'Transmutation'),
('V', 'Evocation')
ON CONFLICT (code) DO NOTHING;

SELECT COUNT(*) || ' spell schools imported' FROM spell_schools;

-- Import alignment values
\echo ''
\echo '⚖️  Importing alignment values...'
INSERT INTO alignment_values (code, name, description) VALUES
('L', 'Lawful', 'law-chaos axis'),
('N', 'Neutral', 'law-chaos axis or good-evil axis'),
('C', 'Chaotic', 'law-chaos axis'),
('G', 'Good', 'good-evil axis'),
('E', 'Evil', 'good-evil axis'),
('U', 'Unaligned', 'no alignment'),
('A', 'Any', 'any alignment')
ON CONFLICT (code) DO NOTHING;

SELECT COUNT(*) || ' alignment values imported' FROM alignment_values;

-- Import skills
\echo ''
\echo '🎯 Importing skills...'
INSERT INTO skills (name, ability) VALUES
('Acrobatics', 'DEX'),
('Animal Handling', 'WIS'),
('Arcana', 'INT'),
('Athletics', 'STR'),
('Deception', 'CHA'),
('History', 'INT'),
('Insight', 'WIS'),
('Intimidation', 'CHA'),
('Investigation', 'INT'),
('Medicine', 'WIS'),
('Nature', 'INT'),
('Perception', 'WIS'),
('Performance', 'CHA'),
('Persuasion', 'CHA'),
('Religion', 'INT'),
('Sleight of Hand', 'DEX'),
('Stealth', 'DEX'),
('Survival', 'WIS')
ON CONFLICT (name) DO NOTHING;

SELECT COUNT(*) || ' skills imported' FROM skills;

\echo ''
\echo '================================================================================'
\echo '✅ CONTROLLED VOCABULARY IMPORT COMPLETE'
\echo '================================================================================'
\echo ''
\echo 'Summary:'
SELECT 'sources: ' || COUNT(*) FROM sources
UNION ALL
SELECT 'item_rarities: ' || COUNT(*) FROM item_rarities
UNION ALL
SELECT 'damage_types: ' || COUNT(*) FROM damage_types
UNION ALL
SELECT 'condition_types: ' || COUNT(*) FROM condition_types
UNION ALL
SELECT 'creature_types: ' || COUNT(*) FROM creature_types
UNION ALL
SELECT 'creature_sizes: ' || COUNT(*) FROM creature_sizes
UNION ALL
SELECT 'spell_schools: ' || COUNT(*) FROM spell_schools
UNION ALL
SELECT 'alignment_values: ' || COUNT(*) FROM alignment_values
UNION ALL
SELECT 'skills: ' || COUNT(*) FROM skills
UNION ALL
SELECT 'attack_types: ' || COUNT(*) FROM attack_types;

\echo ''
\echo 'Note: item_types and item_properties will be populated during entity import'
\echo '      as they require more complex extraction from the data files.'
