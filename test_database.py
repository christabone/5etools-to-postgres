#!/usr/bin/env python3
"""
Comprehensive Database Test Suite

Tests database functionality, query performance, and data integrity.
Uses pytest framework for organized testing.

Usage:
    pytest test_database.py -v
    pytest test_database.py -v --benchmark-only  # Performance tests only
    pytest test_database.py -v -k "test_spell"   # Run specific tests

Requirements:
    pip install pytest pytest-benchmark
"""

import pytest
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
from pathlib import Path

# Import helpers
sys.path.insert(0, str(Path(__file__).parent))
from db_helpers import get_connection


@pytest.fixture(scope="session")
def db_connection():
    """Create a database connection for all tests"""
    conn = get_connection()
    yield conn
    conn.close()


@pytest.fixture
def cursor(db_connection):
    """Create a cursor for each test"""
    cur = db_connection.cursor(cursor_factory=RealDictCursor)
    yield cur
    # Rollback any failed transactions
    if db_connection.status != psycopg2.extensions.STATUS_READY:
        db_connection.rollback()
    cur.close()


# ============================================================================
# ENTITY QUERY TESTS
# ============================================================================

class TestItemQueries:
    """Test item-related queries"""

    def test_get_all_items(self, cursor):
        """Fetch all items"""
        cursor.execute("SELECT COUNT(*) as count FROM items")
        result = cursor.fetchone()
        assert result['count'] == 2722

    def test_get_item_by_name(self, cursor):
        """Find specific item by name"""
        cursor.execute("SELECT * FROM items WHERE name = 'Longsword' LIMIT 1")
        item = cursor.fetchone()
        assert item is not None
        assert item['name'] == 'Longsword'

    def test_get_items_by_rarity(self, cursor):
        """Get items filtered by rarity"""
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM items i
            JOIN item_rarities r ON i.rarity_id = r.id
            WHERE r.name = 'legendary'
        """)
        result = cursor.fetchone()
        assert result['count'] > 0

    def test_get_items_with_damage(self, cursor):
        """Get items that have damage"""
        cursor.execute("""
            SELECT i.name, id.damage_dice, dt.name as damage_type
            FROM items i
            JOIN item_damage id ON i.id = id.item_id
            LEFT JOIN damage_types dt ON id.damage_type_id = dt.id
            LIMIT 10
        """)
        results = cursor.fetchall()
        assert len(results) > 0
        # Verify structure
        assert 'damage_dice' in results[0]

    def test_get_versatile_weapons(self, cursor):
        """Get items with versatile damage"""
        cursor.execute("""
            SELECT i.name, id.damage_dice, id.versatile_dice
            FROM items i
            JOIN item_damage id ON i.id = id.item_id
            WHERE id.versatile_dice IS NOT NULL
        """)
        results = cursor.fetchall()
        assert len(results) == 146  # Documented count
        # Verify all have versatile dice
        for item in results:
            assert item['versatile_dice'] is not None

    def test_get_items_with_properties(self, cursor):
        """Get items with specific properties"""
        cursor.execute("""
            SELECT i.name, array_agg(ip.code) as properties
            FROM items i
            JOIN item_item_properties iip ON i.id = iip.item_id
            JOIN item_properties ip ON iip.property_id = ip.id
            GROUP BY i.id, i.name
            HAVING 'F' = ANY(array_agg(ip.code))  -- Finesse property
        """)
        results = cursor.fetchall()
        assert len(results) > 0


class TestMonsterQueries:
    """Test monster-related queries"""

    def test_get_all_monsters(self, cursor):
        """Fetch all monsters"""
        cursor.execute("SELECT COUNT(*) as count FROM monsters")
        result = cursor.fetchone()
        assert result['count'] == 4445

    def test_get_monster_by_cr(self, cursor):
        """Get monsters filtered by CR"""
        cursor.execute("SELECT COUNT(*) as count FROM monsters WHERE cr >= 10 AND cr <= 15")
        result = cursor.fetchone()
        assert result['count'] > 0

    def test_get_spellcasting_monsters(self, cursor):
        """Get monsters that can cast spells"""
        cursor.execute("""
            SELECT DISTINCT m.name, COUNT(ms.spell_id) as spell_count
            FROM monsters m
            JOIN monster_spells ms ON m.id = ms.monster_id
            GROUP BY m.id, m.name
            HAVING COUNT(ms.spell_id) > 5
            ORDER BY spell_count DESC
            LIMIT 10
        """)
        results = cursor.fetchall()
        assert len(results) > 0
        # Verify all have spell_count > 5
        for monster in results:
            assert monster['spell_count'] > 5

    def test_get_monster_attacks(self, cursor):
        """Get monster attack information"""
        cursor.execute("""
            SELECT m.name, ma.action_name, ma.damage_dice, dt.name as damage_type
            FROM monsters m
            JOIN monster_attacks ma ON m.id = ma.monster_id
            LEFT JOIN damage_types dt ON ma.damage_type_id = dt.id
            WHERE m.name = 'Ancient Red Dragon'
        """)
        results = cursor.fetchall()
        assert len(results) > 0

    def test_get_monsters_by_type(self, cursor):
        """Get monsters filtered by creature type"""
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM monsters m
            JOIN creature_types ct ON m.type_id = ct.id
            WHERE ct.name = 'dragon'
        """)
        result = cursor.fetchone()
        assert result['count'] > 0

    def test_get_monster_with_conditions(self, cursor):
        """Get monsters that inflict conditions"""
        cursor.execute("""
            SELECT m.name, mac.action_name, ct.name as condition
            FROM monsters m
            JOIN monster_action_conditions mac ON m.id = mac.monster_id
            JOIN condition_types ct ON mac.condition_id = ct.id
            WHERE ct.name = 'poisoned'
            LIMIT 10
        """)
        results = cursor.fetchall()
        assert len(results) > 0


class TestSpellQueries:
    """Test spell-related queries"""

    def test_get_all_spells(self, cursor):
        """Fetch all spells"""
        cursor.execute("SELECT COUNT(*) as count FROM spells")
        result = cursor.fetchone()
        assert result['count'] == 937

    def test_get_spells_by_level(self, cursor):
        """Get spells filtered by level"""
        cursor.execute("SELECT COUNT(*) as count FROM spells WHERE level = 3")
        result = cursor.fetchone()
        assert result['count'] > 0

    def test_get_cantrips(self, cursor):
        """Get all cantrips (level 0 spells)"""
        cursor.execute("SELECT name FROM spells WHERE level = 0")
        results = cursor.fetchall()
        assert len(results) > 0

    def test_get_ritual_spells(self, cursor):
        """Get all ritual spells"""
        cursor.execute("SELECT COUNT(*) as count FROM spells WHERE is_ritual = true")
        result = cursor.fetchone()
        assert result['count'] == 66  # Documented count

    def test_get_concentration_spells(self, cursor):
        """Get all concentration spells"""
        cursor.execute("SELECT COUNT(*) as count FROM spells WHERE requires_concentration = true")
        result = cursor.fetchone()
        assert result['count'] == 405  # Documented count

    def test_get_spells_by_school(self, cursor):
        """Get spells filtered by school"""
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM spells s
            JOIN spell_schools ss ON s.school_id = ss.id
            WHERE ss.name = 'Evocation'
        """)
        result = cursor.fetchone()
        assert result['count'] > 0

    def test_get_spells_with_damage(self, cursor):
        """Get damage-dealing spells"""
        cursor.execute("""
            SELECT s.name, sd.damage_dice, dt.name as damage_type
            FROM spells s
            JOIN spell_damage sd ON s.id = sd.spell_id
            LEFT JOIN damage_types dt ON sd.damage_type_id = dt.id
            WHERE s.level = 1
            LIMIT 10
        """)
        results = cursor.fetchall()
        assert len(results) > 0

    def test_get_spell_summons(self, cursor):
        """Get spells that summon creatures"""
        cursor.execute("""
            SELECT s.name, m.name as creature_name, ss.quantity
            FROM spells s
            JOIN spell_summons ss ON s.id = ss.spell_id
            JOIN monsters m ON ss.creature_id = m.id
        """)
        results = cursor.fetchall()
        assert len(results) > 0


# ============================================================================
# RELATIONSHIP QUERY TESTS
# ============================================================================

class TestRelationshipQueries:
    """Test complex relationship queries"""

    def test_items_granting_spells(self, cursor):
        """Get items that grant spell abilities"""
        cursor.execute("""
            SELECT i.name as item_name, s.name as spell_name, s.level
            FROM items i
            JOIN item_spells isp ON i.id = isp.item_id
            JOIN spells s ON isp.spell_id = s.id
            ORDER BY i.name
            LIMIT 10
        """)
        results = cursor.fetchall()
        assert len(results) > 0

    def test_spells_that_reference_other_spells(self, cursor):
        """Get spells that reference other spells"""
        cursor.execute("""
            SELECT s1.name as spell, s2.name as related_spell
            FROM spells s1
            JOIN spell_related_spells srs ON s1.id = srs.spell_id
            JOIN spells s2 ON srs.related_spell_id = s2.id
        """)
        results = cursor.fetchall()
        assert len(results) > 0

    def test_monsters_with_magic_items(self, cursor):
        """Get monsters that possess magic items"""
        cursor.execute("""
            SELECT m.name as monster, i.name as item
            FROM monsters m
            JOIN monster_items mi ON m.id = mi.monster_id
            JOIN items i ON mi.item_id = i.id
        """)
        results = cursor.fetchall()
        assert len(results) > 0

    def test_cross_reference_completeness(self, cursor):
        """Verify cross-reference tables are populated"""
        tables = [
            'item_related_items',
            'item_spells',
            'item_creatures',
            'monster_items',
            'monster_spells',
            'monster_creatures',
            'spell_items',
            'spell_related_spells',
            'spell_summons'
        ]

        for table in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            result = cursor.fetchone()
            # All cross-ref tables should have at least 1 record
            assert result['count'] > 0, f"{table} is empty"


# ============================================================================
# AGGREGATION & STATISTICAL QUERIES
# ============================================================================

class TestAggregationQueries:
    """Test aggregation and statistical queries"""

    def test_spell_count_by_level(self, cursor):
        """Get spell distribution across levels"""
        cursor.execute("""
            SELECT level, COUNT(*) as count
            FROM spells
            GROUP BY level
            ORDER BY level
        """)
        results = cursor.fetchall()
        assert len(results) == 10  # Levels 0-9
        # Verify all counts are positive
        for row in results:
            assert row['count'] > 0

    def test_monster_count_by_cr(self, cursor):
        """Get monster distribution across CR"""
        cursor.execute("""
            SELECT cr, COUNT(*) as count
            FROM monsters
            GROUP BY cr
            ORDER BY cr
        """)
        results = cursor.fetchall()
        assert len(results) > 0

    def test_item_count_by_rarity(self, cursor):
        """Get item distribution by rarity"""
        cursor.execute("""
            SELECT r.name, COUNT(i.id) as count
            FROM item_rarities r
            LEFT JOIN items i ON r.id = i.rarity_id
            GROUP BY r.id, r.name
            ORDER BY r.name
        """)
        results = cursor.fetchall()
        assert len(results) > 0

    def test_average_monster_stats(self, cursor):
        """Calculate average monster statistics"""
        cursor.execute("""
            SELECT
                AVG(cr) as avg_cr,
                AVG(hp_average) as avg_hp,
                AVG(ac_primary) as avg_ac
            FROM monsters
        """)
        result = cursor.fetchone()
        assert result['avg_cr'] is not None
        assert result['avg_hp'] > 0
        assert result['avg_ac'] > 0

    def test_damage_type_frequency(self, cursor):
        """Count usage of each damage type"""
        cursor.execute("""
            SELECT dt.name,
                   COUNT(DISTINCT id.item_id) as item_count,
                   COUNT(DISTINCT ma.monster_id) as monster_count,
                   COUNT(DISTINCT sd.spell_id) as spell_count
            FROM damage_types dt
            LEFT JOIN item_damage id ON dt.id = id.damage_type_id
            LEFT JOIN monster_attacks ma ON dt.id = ma.damage_type_id
            LEFT JOIN spell_damage sd ON dt.id = sd.damage_type_id
            GROUP BY dt.id, dt.name
            ORDER BY (COUNT(id.item_id) + COUNT(ma.monster_id) + COUNT(sd.spell_id)) DESC
        """)
        results = cursor.fetchall()
        assert len(results) > 0


# ============================================================================
# FULL-TEXT SEARCH TESTS
# ============================================================================

class TestSearchQueries:
    """Test search and filtering capabilities"""

    def test_case_insensitive_name_search(self, cursor):
        """Search for items by partial name (case-insensitive)"""
        cursor.execute("""
            SELECT name FROM items
            WHERE LOWER(name) LIKE LOWER('%sword%')
            LIMIT 10
        """)
        results = cursor.fetchall()
        assert len(results) > 0
        # Verify all contain 'sword' (case-insensitive)
        for item in results:
            assert 'sword' in item['name'].lower()

    def test_search_by_source(self, cursor):
        """Get all entities from a specific source"""
        cursor.execute("""
            SELECT
                (SELECT COUNT(*) FROM items i WHERE i.source_id = s.id) as item_count,
                (SELECT COUNT(*) FROM monsters m WHERE m.source_id = s.id) as monster_count,
                (SELECT COUNT(*) FROM spells sp WHERE sp.source_id = s.id) as spell_count
            FROM sources s
            WHERE s.code = 'PHB'
        """)
        result = cursor.fetchone()
        # PHB should have content in all categories
        assert result['item_count'] > 0
        assert result['monster_count'] > 0
        assert result['spell_count'] > 0

    def test_multi_criteria_monster_search(self, cursor):
        """Search monsters with multiple criteria"""
        cursor.execute("""
            SELECT m.name, m.cr, ct.name as type
            FROM monsters m
            JOIN creature_types ct ON m.type_id = ct.id
            WHERE m.cr BETWEEN 5 AND 10
              AND ct.name IN ('dragon', 'fiend', 'undead')
            ORDER BY m.cr
        """)
        results = cursor.fetchall()
        # Verify all match criteria
        for monster in results:
            assert 5 <= monster['cr'] <= 10
            assert monster['type'] in ['dragon', 'fiend', 'undead']


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_level_0_cantrips(self, cursor):
        """Verify cantrips are correctly identified"""
        cursor.execute("SELECT COUNT(*) as count FROM spells WHERE level = 0")
        result = cursor.fetchone()
        assert result['count'] > 0

    def test_cr_0_monsters(self, cursor):
        """Verify CR 0 monsters exist"""
        cursor.execute("SELECT COUNT(*) as count FROM monsters WHERE cr = 0")
        result = cursor.fetchone()
        assert result['count'] > 0

    def test_items_without_rarity(self, cursor):
        """Check items with NULL rarity"""
        cursor.execute("SELECT COUNT(*) as count FROM items WHERE rarity_id IS NULL")
        result = cursor.fetchone()
        # Some items may not have rarity (generic equipment)
        assert result['count'] >= 0

    def test_items_without_type(self, cursor):
        """Check items with NULL type_id"""
        cursor.execute("SELECT COUNT(*) as count FROM items WHERE type_id IS NULL")
        result = cursor.fetchone()
        # We know 38.2% have NULL type_id
        assert result['count'] == 1039

    def test_spell_max_level(self, cursor):
        """Verify 9th level spells exist"""
        cursor.execute("SELECT COUNT(*) as count FROM spells WHERE level = 9")
        result = cursor.fetchone()
        assert result['count'] > 0

    def test_highest_cr_monster(self, cursor):
        """Get highest CR monster"""
        cursor.execute("""
            SELECT name, cr FROM monsters
            ORDER BY cr DESC
            LIMIT 1
        """)
        result = cursor.fetchone()
        assert result['cr'] >= 20  # Should be high CR


# ============================================================================
# PERFORMANCE BENCHMARKS
# ============================================================================

class TestPerformance:
    """Benchmark query performance"""

    def test_index_on_item_name(self, benchmark, cursor):
        """Benchmark item lookup by name"""
        def query():
            cursor.execute("SELECT * FROM items WHERE name = 'Longsword'")
            return cursor.fetchone()

        result = benchmark(query)
        assert result is not None

    def test_join_performance_monster_spells(self, benchmark, cursor):
        """Benchmark monster-spell join query"""
        def query():
            cursor.execute("""
                SELECT m.name, s.name as spell
                FROM monsters m
                JOIN monster_spells ms ON m.id = ms.monster_id
                JOIN spells s ON ms.spell_id = s.id
                LIMIT 100
            """)
            return cursor.fetchall()

        results = benchmark(query)
        assert len(results) > 0

    def test_aggregation_performance(self, benchmark, cursor):
        """Benchmark aggregation query"""
        def query():
            cursor.execute("""
                SELECT level, COUNT(*) as count
                FROM spells
                GROUP BY level
            """)
            return cursor.fetchall()

        results = benchmark(query)
        assert len(results) == 10

    def test_complex_join_performance(self, benchmark, cursor):
        """Benchmark complex multi-table join"""
        def query():
            cursor.execute("""
                SELECT
                    i.name,
                    s.name as source,
                    r.name as rarity,
                    array_agg(DISTINCT ip.code) as properties
                FROM items i
                JOIN sources s ON i.source_id = s.id
                LEFT JOIN item_rarities r ON i.rarity_id = r.id
                LEFT JOIN item_item_properties iip ON i.id = iip.item_id
                LEFT JOIN item_properties ip ON iip.property_id = ip.id
                GROUP BY i.id, i.name, s.name, r.name
                LIMIT 100
            """)
            return cursor.fetchall()

        results = benchmark(query)
        assert len(results) > 0


# ============================================================================
# DATA INTEGRITY TESTS
# ============================================================================

class TestDataIntegrity:
    """Test data integrity constraints"""

    def test_no_duplicate_entity_names_in_source(self, cursor):
        """Verify no duplicate (name, source) pairs in entities"""
        # Items
        cursor.execute("""
            SELECT name, source_id, COUNT(*) as count
            FROM items
            GROUP BY name, source_id
            HAVING COUNT(*) > 1
        """)
        duplicates = cursor.fetchall()
        assert len(duplicates) == 0, f"Found {len(duplicates)} duplicate items"

        # Monsters
        cursor.execute("""
            SELECT name, source_id, COUNT(*) as count
            FROM monsters
            GROUP BY name, source_id
            HAVING COUNT(*) > 1
        """)
        duplicates = cursor.fetchall()
        assert len(duplicates) == 0, f"Found {len(duplicates)} duplicate monsters"

        # Spells
        cursor.execute("""
            SELECT name, source_id, COUNT(*) as count
            FROM spells
            GROUP BY name, source_id
            HAVING COUNT(*) > 1
        """)
        duplicates = cursor.fetchall()
        assert len(duplicates) == 0, f"Found {len(duplicates)} duplicate spells"

    def test_all_entities_have_sources(self, cursor):
        """Verify all entities reference valid sources"""
        for table in ['items', 'monsters', 'spells']:
            cursor.execute(f"""
                SELECT COUNT(*) as count
                FROM {table}
                WHERE source_id NOT IN (SELECT id FROM sources)
            """)
            orphans = cursor.fetchone()['count']
            assert orphans == 0, f"Found {orphans} {table} with invalid source_id"

    def test_relationship_referential_integrity(self, cursor):
        """Verify all relationships point to valid entities"""
        # Monster spells must reference valid monsters and spells
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM monster_spells ms
            WHERE NOT EXISTS (SELECT 1 FROM monsters m WHERE m.id = ms.monster_id)
               OR NOT EXISTS (SELECT 1 FROM spells s WHERE s.id = ms.spell_id)
        """)
        orphans = cursor.fetchone()['count']
        assert orphans == 0, f"Found {orphans} orphaned monster_spells"

    def test_unique_constraints_enforced(self, cursor):
        """Verify UNIQUE constraints prevent duplicates"""
        # This test verifies constraints exist, actual duplicate detection in validate_import.py
        cursor.execute("""
            SELECT conname FROM pg_constraint
            WHERE contype = 'u'
              AND conname IN ('item_damage_unique', 'spell_damage_unique')
        """)
        constraints = cursor.fetchall()
        assert len(constraints) == 2, "Missing UNIQUE constraints on damage tables"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
