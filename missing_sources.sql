-- Missing Sources - Discovered during Phase 2.1 Review
-- These 18 source codes exist in extracted data but were not in the original controlled vocabulary
-- Run before Phase 2.2 import to prevent foreign key constraint failures
--
-- Affected entities: 50 (31 items, 19 monsters, 0 spells) = 0.6% of total dataset
--
-- Usage: sudo -u postgres psql -d dnd5e_reference -f missing_sources.sql

\echo 'Adding 18 missing source codes...'

INSERT INTO sources (code, name, type) VALUES
('AZfyT', 'A Zib for Your Thoughts', 'unknown'),
('EET', 'Elemental Evil: Trinkets', 'unknown'),
('ESK', 'Essentials Kit', 'unknown'),
('GotSF', 'Guildmasters Guide to Spelljammer', 'unknown'),
('HAT-LMI', 'Honor Among Thieves: Legendary Magic Items', 'unknown'),
('HoL', 'The House of Lament', 'unknown'),
('NRH-ASS', 'NERDS Restoring Harmony: A Sticky Situation', 'unknown'),
('NRH-AT', 'NERDS Restoring Harmony: Ancient Tomb', 'unknown'),
('NRH-AVitW', 'NERDS Restoring Harmony: A Voice in the Wilderness', 'unknown'),
('NRH-AWoL', 'NERDS Restoring Harmony: A Web of Lies', 'unknown'),
('NRH-CoI', 'NERDS Restoring Harmony: Chapel of Iribixi', 'unknown'),
('NRH-TCMC', 'NERDS Restoring Harmony: The Candy Mountain Caper', 'unknown'),
('NRH-TLT', 'NERDS Restoring Harmony: The Lost Tomb', 'unknown'),
('OGA', 'One Grung Above', 'unknown'),
('RoTOS', 'The Rise of Tiamat Online Supplement', 'unknown'),
('RtG', 'Return to Glory', 'unknown'),
('SLW', 'Storm Lord''s Wrath', 'unknown'),
('XMtS', 'Xanathar''s Missing Ten Spells', 'unknown')
ON CONFLICT (code) DO NOTHING;

\echo ''
SELECT 'Total sources now in database: ' || COUNT(*) FROM sources;

\echo ''
\echo '✅ Missing sources added successfully'
