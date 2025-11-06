#!/usr/bin/env python3
"""
Database Helper Functions

Shared utility functions for all import scripts.
Provides database connection, lookup functions, and common operations.

Usage:
    from db_helpers import get_connection, lookup_source, lookup_or_create
"""

import psycopg2
from psycopg2.extras import execute_values
from typing import Optional, Dict, Any, List, Tuple
import sys

# Database connection parameters
# Note: Run import scripts with sudo -u postgres to use peer authentication
DB_PARAMS = {
    'dbname': 'dnd5e_reference',
}


def get_connection():
    """
    Get a database connection using peer authentication.

    Must be run as postgres user: sudo -u postgres python3 script.py

    Returns:
        psycopg2.connection: Database connection
    """
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        # Set search_path to ensure we can see tables
        with conn.cursor() as cur:
            cur.execute("SET search_path TO public;")
        conn.commit()
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        print("💡 Hint: Run this script as postgres user:")
        print(f"   sudo -u postgres python3 {sys.argv[0]}")
        sys.exit(1)


# Cache for lookup tables to avoid repeated queries
_LOOKUP_CACHE: Dict[str, Dict[str, int]] = {}


def _load_lookup_cache(conn, table: str, key_column: str):
    """Load entire lookup table into cache."""
    if table not in _LOOKUP_CACHE:
        _LOOKUP_CACHE[table] = {}
        with conn.cursor() as cur:
            cur.execute(f"SELECT id, {key_column} FROM {table}")
            for row_id, key_value in cur.fetchall():
                _LOOKUP_CACHE[table][str(key_value).lower()] = row_id
    return _LOOKUP_CACHE[table]


def lookup_source(conn, source_code: str) -> Optional[int]:
    """
    Lookup source ID by source code.

    Args:
        conn: Database connection
        source_code: Source code (e.g., "PHB", "MM")

    Returns:
        Source ID or None if not found
    """
    cache = _load_lookup_cache(conn, 'sources', 'code')
    return cache.get(source_code.lower())


def lookup_rarity(conn, rarity_name: str) -> Optional[int]:
    """
    Lookup rarity ID by name.

    Args:
        conn: Database connection
        rarity_name: Rarity name (e.g., "common", "rare")

    Returns:
        Rarity ID or None if not found
    """
    cache = _load_lookup_cache(conn, 'item_rarities', 'name')
    return cache.get(rarity_name.lower())


def lookup_damage_type(conn, damage_type: str) -> Optional[int]:
    """
    Lookup damage type ID by name.

    Args:
        conn: Database connection
        damage_type: Damage type name (e.g., "fire", "slashing")

    Returns:
        Damage type ID or None if not found
    """
    cache = _load_lookup_cache(conn, 'damage_types', 'name')
    return cache.get(damage_type.lower())


def lookup_condition_type(conn, condition_name: str) -> Optional[int]:
    """
    Lookup condition type ID by name.

    Args:
        conn: Database connection
        condition_name: Condition name (e.g., "blinded", "paralyzed")

    Returns:
        Condition type ID or None if not found
    """
    cache = _load_lookup_cache(conn, 'condition_types', 'name')
    return cache.get(condition_name.lower())


def lookup_creature_type(conn, creature_type: str) -> Optional[int]:
    """
    Lookup creature type ID by name.

    Args:
        conn: Database connection
        creature_type: Creature type name (e.g., "dragon", "humanoid")

    Returns:
        Creature type ID or None if not found
    """
    cache = _load_lookup_cache(conn, 'creature_types', 'name')
    return cache.get(creature_type.lower())


def lookup_creature_size(conn, size_code: str) -> Optional[int]:
    """
    Lookup creature size ID by code.

    Args:
        conn: Database connection
        size_code: Size code (e.g., "T", "S", "M", "L", "H", "G")

    Returns:
        Size ID or None if not found
    """
    cache = _load_lookup_cache(conn, 'creature_sizes', 'code')
    return cache.get(size_code.lower())


def lookup_spell_school(conn, school_code: str) -> Optional[int]:
    """
    Lookup spell school ID by code.

    Args:
        conn: Database connection
        school_code: School code (e.g., "A", "V", "E")

    Returns:
        School ID or None if not found
    """
    cache = _load_lookup_cache(conn, 'spell_schools', 'code')
    return cache.get(school_code.lower())


def lookup_alignment(conn, alignment_code: str) -> Optional[int]:
    """
    Lookup alignment value ID by code.

    Args:
        conn: Database connection
        alignment_code: Alignment code (e.g., "L", "G", "E", "N", "C", "U", "A")

    Returns:
        Alignment ID or None if not found
    """
    cache = _load_lookup_cache(conn, 'alignment_values', 'code')
    return cache.get(alignment_code.lower())


def lookup_skill(conn, skill_name: str) -> Optional[int]:
    """
    Lookup skill ID by name.

    Args:
        conn: Database connection
        skill_name: Skill name (e.g., "Perception", "Stealth")

    Returns:
        Skill ID or None if not found
    """
    cache = _load_lookup_cache(conn, 'skills', 'name')
    return cache.get(skill_name.lower())


def lookup_attack_type(conn, attack_type_code: str) -> Optional[int]:
    """
    Lookup attack type ID by code.

    Args:
        conn: Database connection
        attack_type_code: Attack type code (e.g., "melee weapon", "ranged spell")

    Returns:
        Attack type ID or None if not found
    """
    cache = _load_lookup_cache(conn, 'attack_types', 'code')
    return cache.get(attack_type_code.lower())


def lookup_or_create_item_type(conn, type_code: str, type_name: str = None) -> int:
    """
    Lookup or create item type by code.

    Item types are created dynamically during import since they vary by source.

    Args:
        conn: Database connection
        type_code: Type code (e.g., "M", "R", "A")
        type_name: Optional type name (will be derived from code if not provided)

    Returns:
        Type ID
    """
    # Check cache first
    if 'item_types' not in _LOOKUP_CACHE:
        _LOOKUP_CACHE['item_types'] = {}

    cache_key = type_code.lower()
    if cache_key in _LOOKUP_CACHE['item_types']:
        return _LOOKUP_CACHE['item_types'][cache_key]

    # Try to find in database
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM item_types WHERE code = %s", (type_code,))
        result = cur.fetchone()
        if result:
            type_id = result[0]
            _LOOKUP_CACHE['item_types'][cache_key] = type_id
            return type_id

    # Create new type
    if type_name is None:
        # Derive name from code
        type_names = {
            'M': 'Melee Weapon',
            'R': 'Ranged Weapon',
            'A': 'Armor',
            'LA': 'Light Armor',
            'MA': 'Medium Armor',
            'HA': 'Heavy Armor',
            'S': 'Shield',
            'G': 'Adventuring Gear',
            'INS': 'Instrument',
            'SCF': 'Spellcasting Focus',
            'T': 'Tool',
            'P': 'Potion',
            'RD': 'Rod',
            'RG': 'Ring',
            'SC': 'Scroll',
            'WD': 'Wand',
        }
        type_name = type_names.get(type_code, type_code)

    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO item_types (code, name) VALUES (%s, %s) RETURNING id",
            (type_code, type_name)
        )
        type_id = cur.fetchone()[0]
        conn.commit()
        _LOOKUP_CACHE['item_types'][cache_key] = type_id
        return type_id


def lookup_or_create_item_property(conn, property_code: str, property_name: str = None) -> int:
    """
    Lookup or create item property by code.

    Args:
        conn: Database connection
        property_code: Property code (e.g., "F", "V", "2H")
        property_name: Optional property name

    Returns:
        Property ID
    """
    # Check cache first
    if 'item_properties' not in _LOOKUP_CACHE:
        _LOOKUP_CACHE['item_properties'] = {}

    cache_key = property_code.lower()
    if cache_key in _LOOKUP_CACHE['item_properties']:
        return _LOOKUP_CACHE['item_properties'][cache_key]

    # Try to find in database
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM item_properties WHERE code = %s", (property_code,))
        result = cur.fetchone()
        if result:
            prop_id = result[0]
            _LOOKUP_CACHE['item_properties'][cache_key] = prop_id
            return prop_id

    # Create new property
    if property_name is None:
        property_names = {
            'F': 'Finesse',
            '2H': 'Two-Handed',
            'V': 'Versatile',
            'H': 'Heavy',
            'L': 'Light',
            'T': 'Thrown',
            'R': 'Reach',
            'LD': 'Loading',
            'A': 'Ammunition',
            'RLD': 'Reload',
        }
        property_name = property_names.get(property_code, property_code)

    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO item_properties (code, name) VALUES (%s, %s) RETURNING id",
            (property_code, property_name)
        )
        prop_id = cur.fetchone()[0]
        conn.commit()
        _LOOKUP_CACHE['item_properties'][cache_key] = prop_id
        return prop_id


def lookup_or_create_creature_type(conn, type_name: str) -> int:
    """
    Lookup or create creature type by name.

    Args:
        conn: Database connection
        type_name: Creature type name (e.g., 'humanoid', 'beast', 'dragon')

    Returns:
        Creature type ID
    """
    if 'creature_types' not in _LOOKUP_CACHE:
        _LOOKUP_CACHE['creature_types'] = {}

    cache_key = type_name.lower()

    # Check cache first
    if cache_key in _LOOKUP_CACHE['creature_types']:
        return _LOOKUP_CACHE['creature_types'][cache_key]

    # Try to find in database
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM creature_types WHERE name = %s", (type_name.lower(),))
        result = cur.fetchone()
        if result:
            type_id = result[0]
            _LOOKUP_CACHE['creature_types'][cache_key] = type_id
            return type_id

    # Create new creature type
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO creature_types (name) VALUES (%s) RETURNING id",
            (type_name.lower(),)
        )
        type_id = cur.fetchone()[0]
        conn.commit()
        _LOOKUP_CACHE['creature_types'][cache_key] = type_id
        return type_id


def lookup_or_create_creature_size(conn, size_code: str) -> int:
    """
    Lookup or create creature size by code.

    Args:
        conn: Database connection
        size_code: Size code (T, S, M, L, H, G)

    Returns:
        Creature size ID
    """
    if 'creature_sizes' not in _LOOKUP_CACHE:
        _LOOKUP_CACHE['creature_sizes'] = {}

    cache_key = size_code.lower()

    # Check cache first
    if cache_key in _LOOKUP_CACHE['creature_sizes']:
        return _LOOKUP_CACHE['creature_sizes'][cache_key]

    # Try to find in database
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM creature_sizes WHERE code = %s", (size_code.upper(),))
        result = cur.fetchone()
        if result:
            size_id = result[0]
            _LOOKUP_CACHE['creature_sizes'][cache_key] = size_id
            return size_id

    # Create new size if not found (should not happen with controlled vocab)
    # Map codes to names
    size_names = {
        'T': 'Tiny',
        'S': 'Small',
        'M': 'Medium',
        'L': 'Large',
        'H': 'Huge',
        'G': 'Gargantuan'
    }
    size_name = size_names.get(size_code.upper(), size_code.upper())

    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO creature_sizes (code, name) VALUES (%s, %s) RETURNING id",
            (size_code.upper(), size_name)
        )
        size_id = cur.fetchone()[0]
        conn.commit()
        _LOOKUP_CACHE['creature_sizes'][cache_key] = size_id
        return size_id


def clean_type_code(type_code: str) -> str:
    """
    Clean item type code by removing source suffixes and $ prefix.

    Examples:
        "M|XPHB" -> "M"
        "$G" -> "G"
        "A" -> "A"

    Args:
        type_code: Raw type code from data

    Returns:
        Cleaned type code
    """
    if not type_code:
        return None

    # Remove $ prefix (indicates generic variant)
    cleaned = type_code.lstrip('$')

    # Remove source suffix (e.g., "|XPHB")
    if '|' in cleaned:
        cleaned = cleaned.split('|')[0]

    return cleaned


def expand_damage_type_code(damage_code: str) -> str:
    """
    Expand single-letter damage type code to full name.

    Args:
        damage_code: Single letter code (B, P, S, etc.)

    Returns:
        Full damage type name
    """
    damage_type_map = {
        'B': 'bludgeoning',
        'P': 'piercing',
        'S': 'slashing',
        'N': 'necrotic',
        'R': 'radiant',
        'F': 'fire',
        'C': 'cold',
        'L': 'lightning',
        'T': 'thunder',
        'A': 'acid',
        'I': 'poison',
        'O': 'force',
        'Y': 'psychic',
    }
    return damage_type_map.get(damage_code.upper(), damage_code.lower())


def parse_cr(cr_value) -> float:
    """
    Parse CR value to float.

    Handles fractional CR like "1/4", "1/2", "1/8" and converts to decimal.

    Args:
        cr_value: CR as string, int, or float

    Returns:
        CR as float (e.g., 0.25 for "1/4")
    """
    if cr_value is None:
        return 0.0

    if isinstance(cr_value, (int, float)):
        return float(cr_value)

    if isinstance(cr_value, str):
        # Handle fractional CR
        if '/' in cr_value:
            parts = cr_value.split('/')
            return float(parts[0]) / float(parts[1])
        return float(cr_value)

    return 0.0


def parse_hp(hp_data) -> tuple:
    """
    Parse HP data to extract average and formula.

    Args:
        hp_data: HP as dict {"average": 10, "formula": "2d8+2"} or int

    Returns:
        Tuple of (average: int, formula: str)
    """
    if isinstance(hp_data, int):
        return hp_data, None

    if isinstance(hp_data, dict):
        average = hp_data.get('average', 0)
        formula = hp_data.get('formula')
        return average, formula

    return 0, None


def parse_ac(ac_data) -> int:
    """
    Parse AC data to extract primary AC value.

    Args:
        ac_data: AC as int or list [{"ac": 15, "from": ["natural armor"]}]

    Returns:
        Primary AC value as int
    """
    if isinstance(ac_data, int):
        return ac_data

    if isinstance(ac_data, list) and len(ac_data) > 0:
        first_ac = ac_data[0]
        if isinstance(first_ac, dict):
            return first_ac.get('ac', 10)
        if isinstance(first_ac, int):
            return first_ac

    return 10  # Default AC


def parse_speed(speed_data) -> dict:
    """
    Parse speed data to extract individual movement types.

    Args:
        speed_data: Speed as dict {"walk": 30, "fly": 60, "swim": 30} or int

    Returns:
        Dict with keys: walk, fly, swim, climb, burrow (all as int)
    """
    speeds = {
        'walk': 30,  # Default walking speed
        'fly': 0,
        'swim': 0,
        'climb': 0,
        'burrow': 0
    }

    if isinstance(speed_data, int):
        speeds['walk'] = speed_data
        return speeds

    if isinstance(speed_data, dict):
        speeds['walk'] = speed_data.get('walk', 30)
        speeds['fly'] = speed_data.get('fly', 0)
        speeds['swim'] = speed_data.get('swim', 0)
        speeds['climb'] = speed_data.get('climb', 0)
        speeds['burrow'] = speed_data.get('burrow', 0)

    return speeds


def parse_ability_scores(monster_data: dict) -> dict:
    """
    Extract ability scores from monster data.

    Args:
        monster_data: Monster dict with str, dex, con, int, wis, cha fields

    Returns:
        Dict with all 6 ability scores (default 10 if missing)
    """
    return {
        'str': monster_data.get('str', 10),
        'dex': monster_data.get('dex', 10),
        'con': monster_data.get('con', 10),
        'int': monster_data.get('int', 10),
        'wis': monster_data.get('wis', 10),
        'cha': monster_data.get('cha', 10),
    }


def generate_search_vector(name: str, description: str = None) -> str:
    """
    Generate a tsvector string for full-text search.

    Args:
        name: Entity name
        description: Optional description text

    Returns:
        SQL expression for tsvector
    """
    if description:
        return f"to_tsvector('english', {psycopg2.extensions.adapt(name)} || ' ' || {psycopg2.extensions.adapt(description)})"
    else:
        return f"to_tsvector('english', {psycopg2.extensions.adapt(name)})"


def batch_insert(conn, table: str, columns: List[str], values: List[Tuple], batch_size: int = 100):
    """
    Insert records in batches for better performance.

    Args:
        conn: Database connection
        table: Table name
        columns: List of column names
        values: List of tuples with values
        batch_size: Number of records per batch
    """
    if not values:
        return

    column_str = ', '.join(columns)

    with conn.cursor() as cur:
        for i in range(0, len(values), batch_size):
            batch = values[i:i + batch_size]
            execute_values(
                cur,
                f"INSERT INTO {table} ({column_str}) VALUES %s",
                batch
            )

    conn.commit()


def log_progress(current: int, total: int, entity_type: str = "records"):
    """
    Print progress update.

    Args:
        current: Current count
        total: Total count
        entity_type: Type of entity being processed
    """
    if current % 100 == 0 or current == total:
        percentage = (current / total * 100) if total > 0 else 0
        print(f"  Progress: {current}/{total} {entity_type} ({percentage:.1f}%)")


def log_warning(message: str):
    """Print warning message."""
    print(f"⚠️  WARNING: {message}")


def log_error(message: str):
    """Print error message."""
    print(f"❌ ERROR: {message}")


def log_success(message: str):
    """Print success message."""
    print(f"✅ {message}")


def log_info(message: str):
    """Print info message."""
    print(f"ℹ️  {message}")


# Statistics tracking
class ImportStats:
    """Track import statistics."""

    def __init__(self):
        self.processed = 0
        self.succeeded = 0
        self.failed = 0
        self.skipped = 0
        self.warnings = []
        self.errors = []

    def record_success(self):
        """Record successful import."""
        self.processed += 1
        self.succeeded += 1

    def record_failure(self, error_msg: str):
        """Record failed import."""
        self.processed += 1
        self.failed += 1
        self.errors.append(error_msg)

    def record_skip(self, reason: str):
        """Record skipped record."""
        self.processed += 1
        self.skipped += 1
        self.warnings.append(reason)

    def record_warning(self, warning_msg: str):
        """Record warning."""
        self.warnings.append(warning_msg)

    def print_summary(self):
        """Print import summary."""
        print("\n" + "=" * 80)
        print("IMPORT SUMMARY")
        print("=" * 80)
        print(f"Total processed: {self.processed}")
        print(f"✅ Succeeded: {self.succeeded}")
        print(f"⏭️  Skipped: {self.skipped}")
        print(f"❌ Failed: {self.failed}")

        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings[:10], 1):
                print(f"  {i}. {warning}")
            if len(self.warnings) > 10:
                print(f"  ... and {len(self.warnings) - 10} more")

        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for i, error in enumerate(self.errors[:10], 1):
                print(f"  {i}. {error}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more")

        print("=" * 80)

        # Return success/failure status
        return self.failed == 0


if __name__ == '__main__':
    # Test database connection and lookups
    print("Testing database helper functions...")

    try:
        conn = get_connection()
        print("✅ Database connection successful")

        # Test lookups
        phb_id = lookup_source(conn, 'PHB')
        print(f"✅ Source lookup: PHB = {phb_id}")

        common_id = lookup_rarity(conn, 'common')
        print(f"✅ Rarity lookup: common = {common_id}")

        fire_id = lookup_damage_type(conn, 'fire')
        print(f"✅ Damage type lookup: fire = {fire_id}")

        # Test type code cleaning
        assert clean_type_code('M|XPHB') == 'M'
        assert clean_type_code('$G') == 'G'
        assert clean_type_code('A') == 'A'
        print("✅ Type code cleaning works")

        # Test damage type expansion
        assert expand_damage_type_code('B') == 'bludgeoning'
        assert expand_damage_type_code('F') == 'fire'
        print("✅ Damage type expansion works")

        conn.close()
        print("\n✅ All tests passed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
