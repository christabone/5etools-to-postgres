#!/usr/bin/env python3
"""
Import Items from cleaned JSON data

Imports items from cleaned_data/items_extracted.json into the items table.
Also populates item_item_properties junction table for weapon properties.

Input: cleaned_data/items_extracted.json (2,722 items expected)
Output: Populates items table and item_item_properties junction table

Usage:
    sudo -u postgres python3 import_items.py
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
    lookup_rarity,
    lookup_or_create_item_type,
    lookup_or_create_item_property,
    clean_type_code,
    log_progress,
    log_warning,
    log_error,
    log_success,
    log_info,
    ImportStats
)

# File paths
ITEMS_FILE = Path('cleaned_data/items_extracted.json')


def load_items() -> List[Dict[str, Any]]:
    """Load items from JSON file."""
    print(f"📖 Loading items from {ITEMS_FILE}")
    with open(ITEMS_FILE, 'r') as f:
        items = json.load(f)
    print(f"✅ Loaded {len(items)} items")
    return items


def import_item(conn, item: Dict[str, Any], stats: ImportStats) -> bool:
    """
    Import a single item into the database.

    Args:
        conn: Database connection
        item: Item data dictionary
        stats: Statistics tracker

    Returns:
        True if successful, False otherwise
    """
    try:
        name = item.get('name')
        if not name:
            stats.record_skip("Item has no name")
            return False

        # Resolve foreign keys
        source_code = item.get('source')
        if not source_code:
            stats.record_skip(f"{name}: No source code")
            return False

        source_id = lookup_source(conn, source_code)
        if source_id is None:
            stats.record_failure(f"{name}: Unknown source '{source_code}'")
            return False

        # Handle item type
        type_id = None
        raw_type = item.get('type')
        if raw_type:
            # Clean type code (remove $ prefix and source suffixes)
            type_code = clean_type_code(raw_type)
            if type_code:
                type_id = lookup_or_create_item_type(conn, type_code)

        # Handle rarity
        rarity_id = None
        rarity_name = item.get('rarity')
        if rarity_name:
            rarity_id = lookup_rarity(conn, rarity_name)
            if rarity_id is None:
                # Default to 'none' if rarity not found
                rarity_id = lookup_rarity(conn, 'none')

        # Extract normalized fields
        value_cp = item.get('value', 0)  # Fixed: was 'value_cp', should be 'value'
        weight_lbs = item.get('weight', 0)

        # Handle requires_attunement (can be bool, string, or dict)
        req_attune = item.get('reqAttune', False)
        if isinstance(req_attune, bool):
            requires_attunement = req_attune
        elif isinstance(req_attune, (str, dict)):
            requires_attunement = True  # Any attunement requirement
        else:
            requires_attunement = False

        # Armor/weapon specific fields
        ac = item.get('ac')
        strength_requirement = item.get('strength')

        # Range fields - Fixed: handle dict format, not string
        range_normal = None
        range_long = None
        if 'range' in item:
            range_data = item['range']
            if isinstance(range_data, dict):
                range_normal = range_data.get('normal')
                range_long = range_data.get('long')
            elif isinstance(range_data, str) and '/' in range_data:
                # Fallback for string format
                parts = range_data.split('/')
                range_normal = int(parts[0]) if parts[0].isdigit() else None
                range_long = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None

        # Phase 1 extracted fields
        base_name = item.get('base_name')
        variant_name = item.get('variant_name')
        container_type = item.get('container_type')
        default_quantity = item.get('default_quantity')
        bonus_display = item.get('bonus_display')
        is_generic_variant = item.get('is_generic_variant', False)
        if isinstance(is_generic_variant, str):
            is_generic_variant = is_generic_variant.lower() == 'true'

        # Store full original JSON
        data_jsonb = json.dumps(item)

        # Generate search vector (simplified - will use database function in production)
        # For now, we'll let the database generate it via a trigger or update later

        # Insert item
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO items (
                    name, source_id, type_id, rarity_id,
                    value_cp, weight_lbs, requires_attunement,
                    ac, strength_requirement,
                    range_normal, range_long,
                    base_name, variant_name, container_type,
                    default_quantity, bonus_display, is_generic_variant,
                    data,
                    search_vector
                )
                VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s,
                    to_tsvector('english', %s)
                )
                RETURNING id
            """, (
                name, source_id, type_id, rarity_id,
                value_cp, weight_lbs, requires_attunement,
                ac, strength_requirement,
                range_normal, range_long,
                base_name, variant_name, container_type,
                default_quantity, bonus_display, is_generic_variant,
                data_jsonb,
                name  # For search vector
            ))
            item_id = cur.fetchone()[0]

        # Insert item properties (weapon properties like Finesse, Versatile, etc.)
        if 'property' in item and item['property']:
            properties = item['property']
            if isinstance(properties, str):
                properties = [properties]

            for prop_code in properties:
                # Fixed: Clean property code to remove source suffixes (e.g., "V|XPHB" -> "V")
                prop_code_cleaned = clean_type_code(prop_code)
                prop_id = lookup_or_create_item_property(conn, prop_code_cleaned)
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO item_item_properties (item_id, property_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                    """, (item_id, prop_id))

        conn.commit()
        stats.record_success()
        return True

    except Exception as e:
        conn.rollback()
        stats.record_failure(f"{item.get('name', 'UNKNOWN')}: {str(e)}")
        return False


def main():
    """Main import function."""
    print("=" * 80)
    print("ITEMS IMPORT")
    print("=" * 80)

    # Load items
    items = load_items()

    # Connect to database
    print(f"\n🔌 Connecting to database...")
    conn = get_connection()
    print("✅ Database connection successful")

    # Import items
    print(f"\n📥 Importing {len(items)} items...")
    stats = ImportStats()

    for i, item in enumerate(items, 1):
        import_item(conn, item, stats)
        log_progress(i, len(items), "items")

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
        log_success(f"Successfully imported {stats.succeeded} items")
        sys.exit(0)


if __name__ == '__main__':
    main()
