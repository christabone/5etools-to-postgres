#!/usr/bin/env python3
"""
Import Spells from cleaned JSON data

Imports spells from cleaned_data/spells_extracted.json into the spells table.

Input: cleaned_data/spells_extracted.json (937 spells expected)
Output: Populates spells table

Usage:
    sudo -u postgres python3 import_spells.py
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
    lookup_spell_school,
    log_progress,
    log_warning,
    log_error,
    log_success,
    log_info,
    ImportStats
)

# File paths
SPELLS_FILE = Path('cleaned_data/spells_extracted.json')


def load_spells() -> List[Dict[str, Any]]:
    """Load spells from JSON file."""
    print(f"📖 Loading spells from {SPELLS_FILE}")
    with open(SPELLS_FILE, 'r') as f:
        spells = json.load(f)
    print(f"✅ Loaded {len(spells)} spells")
    return spells


def parse_casting_time(time_data) -> tuple:
    """
    Parse casting time data to extract number and unit.

    Returns:
        (number, unit) tuple - e.g., (1, "action"), (10, "minute"), etc.
    """
    if isinstance(time_data, list) and len(time_data) > 0:
        time_entry = time_data[0]
        if isinstance(time_entry, dict):
            number = time_entry.get('number', 1)
            unit = time_entry.get('unit', 'action')
            return number, unit
    return 1, 'action'


def parse_range(range_data) -> tuple:
    """
    Parse range data to extract type, value, and unit.

    Returns:
        (type, value, unit) tuple - e.g., ("point", 120, "feet"), ("self", 0, "")
    """
    if isinstance(range_data, dict):
        range_type = range_data.get('type', 'self')

        if range_type == 'point':
            distance = range_data.get('distance', {})
            if isinstance(distance, dict):
                value = distance.get('amount', 0)
                unit = distance.get('type', 'feet')
                return range_type, value, unit
        elif range_type in ['radius', 'sphere', 'cone', 'line', 'cube', 'hemisphere']:
            distance = range_data.get('distance', {})
            if isinstance(distance, dict):
                value = distance.get('amount', 0)
                unit = distance.get('type', 'feet')
                return range_type, value, unit

        return range_type, 0, ''

    return 'self', 0, ''


def parse_duration(duration_data) -> tuple:
    """
    Parse duration data to extract type, value, and unit.

    Returns:
        (type, value, unit) tuple - e.g., ("timed", 10, "minute"), ("instant", 0, "")
    """
    if isinstance(duration_data, dict):
        duration_type = duration_data.get('type', 'instant')

        if duration_type == 'timed':
            value = duration_data.get('value', 1)
            unit = duration_data.get('unit', 'round')
            return duration_type, value, unit

        return duration_type, 0, ''

    return 'instant', 0, ''


def parse_components(components_data) -> tuple:
    """
    Parse components data to extract V, S, M flags and material text.

    Returns:
        (has_v, has_s, has_m, m_text) tuple
    """
    if isinstance(components_data, dict):
        has_v = components_data.get('v', False)
        has_s = components_data.get('s', False)
        has_m = components_data.get('m', False)

        m_text = ''
        if has_m:
            m_data = components_data.get('m')
            if isinstance(m_data, str):
                m_text = m_data
            elif isinstance(m_data, dict):
                m_text = m_data.get('text', '')

        return has_v, has_s, has_m, m_text

    return False, False, False, ''


def import_spell(conn, spell: Dict[str, Any], stats: ImportStats) -> bool:
    """
    Import a single spell into the database.

    Args:
        conn: Database connection
        spell: Spell data dictionary
        stats: Statistics tracker

    Returns:
        True if successful, False otherwise
    """
    try:
        name = spell.get('name')
        if not name:
            stats.record_skip("Spell has no name")
            return False

        # Resolve foreign keys
        source_code = spell.get('source')
        if not source_code:
            stats.record_skip(f"{name}: No source code")
            return False

        source_id = lookup_source(conn, source_code)
        if source_id is None:
            stats.record_failure(f"{name}: Unknown source '{source_code}'")
            return False

        # Handle spell school
        school_id = None
        school_code = spell.get('school')
        if school_code:
            school_id = lookup_spell_school(conn, school_code)
            if school_id is None:
                stats.record_warning(f"{name}: Unknown school '{school_code}'")

        # Extract basic fields
        level = spell.get('level', 0)
        is_ritual = spell.get('meta', {}).get('ritual', False)
        requires_concentration = False

        # Check for concentration in duration
        duration_data = spell.get('duration', {})
        if isinstance(duration_data, dict):
            requires_concentration = duration_data.get('concentration', False)

        # Parse complex fields
        casting_time_num, casting_time_unit = parse_casting_time(spell.get('time'))
        range_type, range_value, range_unit = parse_range(spell.get('range'))
        duration_type, duration_value, duration_unit = parse_duration(duration_data)
        comp_v, comp_s, comp_m, comp_m_text = parse_components(spell.get('components'))

        # Store full original JSON
        data_jsonb = json.dumps(spell)

        # Insert spell
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO spells (
                    name, source_id, school_id, level,
                    is_ritual, requires_concentration,
                    casting_time_number, casting_time_unit,
                    range_type, range_value, range_unit,
                    duration_type, duration_value, duration_unit,
                    component_v, component_s, component_m, component_m_text,
                    data,
                    search_vector
                )
                VALUES (
                    %s, %s, %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s,
                    to_tsvector('english', %s)
                )
                RETURNING id
            """, (
                name, source_id, school_id, level,
                is_ritual, requires_concentration,
                casting_time_num, casting_time_unit,
                range_type, range_value, range_unit,
                duration_type, duration_value, duration_unit,
                comp_v, comp_s, comp_m, comp_m_text,
                data_jsonb,
                name  # For search vector
            ))
            spell_id = cur.fetchone()[0]

        conn.commit()
        stats.record_success()
        return True

    except Exception as e:
        conn.rollback()
        stats.record_failure(f"{spell.get('name', 'UNKNOWN')}: {str(e)}")
        return False


def main():
    """Main import function."""
    print("=" * 80)
    print("SPELLS IMPORT")
    print("=" * 80)

    # Load spells
    spells = load_spells()

    # Connect to database
    print(f"\n🔌 Connecting to database...")
    conn = get_connection()
    print("✅ Database connection successful")

    # Import spells
    print(f"\n📥 Importing {len(spells)} spells...")
    stats = ImportStats()

    for i, spell in enumerate(spells, 1):
        import_spell(conn, spell, stats)
        log_progress(i, len(spells), "spells")

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
        log_success(f"Successfully imported {stats.succeeded} spells")
        sys.exit(0)


if __name__ == '__main__':
    main()
