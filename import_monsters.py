#!/usr/bin/env python3
"""
Import Monsters from cleaned JSON data

Imports monsters from cleaned_data/monsters_extracted.json into the monsters table.
Also populates monster_alignments junction table.

Input: cleaned_data/monsters_extracted.json (4,445 monsters expected)
Output: Populates monsters table and monster_alignments junction table

Usage:
    sudo -u postgres python3 import_monsters.py
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# Import helper functions
sys.path.insert(0, str(Path(__file__).parent))
from db_helpers import (
    get_connection,
    lookup_source,
    lookup_or_create_creature_type,
    lookup_or_create_creature_size,
    lookup_alignment,
    parse_cr,
    parse_hp,
    parse_ac,
    parse_speed,
    parse_ability_scores,
    log_progress,
    log_warning,
    log_error,
    log_success,
    log_info,
    ImportStats
)

# File paths
MONSTERS_FILE = Path('cleaned_data/monsters_extracted.json')


def load_monsters() -> List[Dict[str, Any]]:
    """Load monsters from JSON file."""
    print(f"📖 Loading monsters from {MONSTERS_FILE}")
    with open(MONSTERS_FILE, 'r') as f:
        monsters = json.load(f)
    print(f"✅ Loaded {len(monsters)} monsters")
    return monsters


def import_monster(conn, monster: Dict[str, Any], stats: ImportStats) -> bool:
    """
    Import a single monster into the database.

    Args:
        conn: Database connection
        monster: Monster data dictionary
        stats: Statistics tracker

    Returns:
        True if successful, False otherwise
    """
    try:
        name = monster.get('name')
        if not name:
            stats.record_skip("Monster has no name")
            return False

        # Resolve foreign keys
        source_code = monster.get('source')
        if not source_code:
            stats.record_skip(f"{name}: No source code")
            return False

        source_id = lookup_source(conn, source_code)
        if source_id is None:
            stats.record_failure(f"{name}: Unknown source '{source_code}'")
            return False

        # Handle creature type
        type_id = None
        type_name = monster.get('type')
        if type_name:
            # Handle type as string or dict {"type": "humanoid", "tags": [...]}
            if isinstance(type_name, dict):
                type_name = type_name.get('type', '')
            if type_name:
                type_id = lookup_or_create_creature_type(conn, type_name)

        # Handle creature size
        size_id = None
        size_code = monster.get('size')
        if size_code:
            # Handle size as list (some monsters have multiple sizes, take first)
            if isinstance(size_code, list):
                size_code = size_code[0] if size_code else None
            if size_code:
                size_id = lookup_or_create_creature_size(conn, size_code)

        # Parse complex fields using helper functions
        cr = parse_cr(monster.get('cr', 0))
        hp_avg, hp_formula = parse_hp(monster.get('hp', {}))
        ac = parse_ac(monster.get('ac', 10))
        speeds = parse_speed(monster.get('speed', {}))
        abilities = parse_ability_scores(monster)

        # Extract alignment codes (can be list for multiple alignments)
        alignment_codes = monster.get('alignment', [])
        if isinstance(alignment_codes, str):
            alignment_codes = [alignment_codes]

        # Extract other fields
        passive_perception = monster.get('passive', 10)

        # Store full original JSON
        data_jsonb = json.dumps(monster)

        # Insert monster
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO monsters (
                    name, source_id, type_id, size_id,
                    cr, hp_average, hp_formula,
                    ac_primary,
                    speed_walk, speed_fly, speed_swim, speed_climb, speed_burrow,
                    str, dex, con, int, wis, cha,
                    passive_perception,
                    data,
                    search_vector
                )
                VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s,
                    %s,
                    to_tsvector('english', %s)
                )
                RETURNING id
            """, (
                name, source_id, type_id, size_id,
                cr, hp_avg, hp_formula,
                ac,
                speeds['walk'], speeds['fly'], speeds['swim'], speeds['climb'], speeds['burrow'],
                abilities['str'], abilities['dex'], abilities['con'],
                abilities['int'], abilities['wis'], abilities['cha'],
                passive_perception,
                data_jsonb,
                name  # For search vector
            ))
            monster_id = cur.fetchone()[0]

        # Insert alignments into junction table
        if alignment_codes:
            for alignment_code in alignment_codes:
                # Alignment codes like 'L', 'G', 'E', 'N', 'C', 'U', 'A'
                alignment_id = lookup_alignment(conn, alignment_code)
                if alignment_id:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO monster_alignments (monster_id, alignment_id)
                            VALUES (%s, %s)
                            ON CONFLICT DO NOTHING
                        """, (monster_id, alignment_id))
                else:
                    stats.record_warning(f"{name}: Unknown alignment code '{alignment_code}'")

        conn.commit()
        stats.record_success()
        return True

    except Exception as e:
        conn.rollback()
        stats.record_failure(f"{monster.get('name', 'UNKNOWN')}: {str(e)}")
        return False


def main():
    """Main import function."""
    print("=" * 80)
    print("MONSTERS IMPORT")
    print("=" * 80)

    # Load monsters
    monsters = load_monsters()

    # Connect to database
    print(f"\n🔌 Connecting to database...")
    conn = get_connection()
    print("✅ Database connection successful")

    # Import monsters
    print(f"\n📥 Importing {len(monsters)} monsters...")
    stats = ImportStats()

    for i, monster in enumerate(monsters, 1):
        import_monster(conn, monster, stats)
        log_progress(i, len(monsters), "monsters")

    # Close connection
    conn.close()
    print("\n🔌 Database connection closed")

    # Print summary
    stats.print_summary()

    # Exit with appropriate code
    if stats.failed > 0:
        log_error(f"Import completed with {stats.failed} failures")
        sys.exit(1)
    else:
        log_success(f"Successfully imported {stats.succeeded} monsters")
        sys.exit(0)


if __name__ == '__main__':
    main()
