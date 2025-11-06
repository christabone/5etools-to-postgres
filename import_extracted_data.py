#!/usr/bin/env python3
"""
Import Extracted Relationship Data

Imports conditions, damage, and cross-reference relationships from extraction_data/ files
into junction tables.

Input Files:
- extraction_data/conditions_extracted.json (6,113 relationships)
- extraction_data/damage_extracted.json (5,618 relationships)
- extraction_data/cross_refs_extracted.json (14,769 relationships)

Output: Populates junction tables for conditions, damage, and entity relationships

Usage:
    sudo -u postgres python3 import_extracted_data.py
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import helper functions
sys.path.insert(0, str(Path(__file__).parent))
from db_helpers import (
    get_connection,
    lookup_damage_type,
    lookup_condition_type,
    lookup_attack_type,
    log_progress,
    log_warning,
    log_error,
    log_success,
    log_info,
    ImportStats
)

# File paths
CONDITIONS_FILE = Path('extraction_data/conditions_extracted.json')
DAMAGE_FILE = Path('extraction_data/damage_extracted.json')
CROSS_REFS_FILE = Path('extraction_data/cross_refs_extracted.json')


def load_data_files() -> tuple:
    """Load all extraction data files."""
    print(f"📖 Loading extraction data files...")

    with open(CONDITIONS_FILE, 'r') as f:
        conditions = json.load(f)
    print(f"  ✅ Conditions: {sum(len(v) for v in conditions.values())} relationships")

    with open(DAMAGE_FILE, 'r') as f:
        damage = json.load(f)
    print(f"  ✅ Damage: {sum(len(v) for v in damage.values())} relationships")

    with open(CROSS_REFS_FILE, 'r') as f:
        cross_refs = json.load(f)
    print(f"  ✅ Cross-refs: {sum(len(v) for v in cross_refs.values())} relationships")

    total = (sum(len(v) for v in conditions.values()) +
             sum(len(v) for v in damage.values()) +
             sum(len(v) for v in cross_refs.values()))
    print(f"  📊 Total: {total} relationships to import\n")

    return conditions, damage, cross_refs


def lookup_item_by_name_source(conn, name: str, source: str) -> Optional[int]:
    """Lookup item ID by name and source."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT i.id
            FROM items i
            JOIN sources s ON i.source_id = s.id
            WHERE i.name = %s AND s.code = %s
            LIMIT 1
        """, (name, source))
        result = cur.fetchone()
        return result[0] if result else None


def lookup_monster_by_name_source(conn, name: str, source: str) -> Optional[int]:
    """Lookup monster ID by name and source."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT m.id
            FROM monsters m
            JOIN sources s ON m.source_id = s.id
            WHERE m.name = %s AND s.code = %s
            LIMIT 1
        """, (name, source))
        result = cur.fetchone()
        return result[0] if result else None


def lookup_spell_by_name_source(conn, name: str, source: str) -> Optional[int]:
    """Lookup spell ID by name and source."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT sp.id
            FROM spells sp
            JOIN sources s ON sp.source_id = s.id
            WHERE sp.name = %s AND s.code = %s
            LIMIT 1
        """, (name, source))
        result = cur.fetchone()
        return result[0] if result else None


def import_item_conditions(conn, conditions: List[Dict], stats: ImportStats) -> None:
    """Import item condition relationships."""
    print(f"\n📥 Importing {len(conditions)} item condition relationships...")

    for i, cond in enumerate(conditions, 1):
        try:
            item_id = lookup_item_by_name_source(conn, cond['item_name'], cond['source'])
            if not item_id:
                stats.record_skip(f"{cond['item_name']}: Item not found")
                continue

            condition_id = lookup_condition_type(conn, cond['condition'])
            if not condition_id:
                stats.record_warning(f"{cond['item_name']}: Unknown condition '{cond['condition']}'")
                continue

            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO item_conditions (
                        item_id, condition_id, inflicts,
                        save_dc, save_ability, duration_text
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    item_id, condition_id, cond.get('inflicts', True),
                    cond.get('save_dc'), cond.get('save_ability'),
                    cond.get('duration_text')
                ))

            conn.commit()
            stats.record_success()

        except Exception as e:
            conn.rollback()
            stats.record_failure(f"{cond.get('item_name', 'UNKNOWN')}: {str(e)}")

        if i % 100 == 0:
            log_progress(i, len(conditions), "item conditions")


def import_monster_conditions(conn, conditions: List[Dict], stats: ImportStats) -> None:
    """Import monster condition relationships (from actions)."""
    print(f"\n📥 Importing {len(conditions)} monster condition relationships...")

    for i, cond in enumerate(conditions, 1):
        try:
            monster_id = lookup_monster_by_name_source(conn, cond['monster_name'], cond['source'])
            if not monster_id:
                stats.record_skip(f"{cond['monster_name']}: Monster not found")
                continue

            condition_id = lookup_condition_type(conn, cond['condition'])
            if not condition_id:
                stats.record_warning(f"{cond['monster_name']}: Unknown condition '{cond['condition']}'")
                continue

            # Use context_name as action_name (field name mismatch in extracted data)
            action_name = cond.get('context_name') or cond.get('action_name') or 'Unknown'

            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO monster_action_conditions (
                        monster_id, condition_id, action_name, inflicts,
                        save_dc, save_ability, duration_text
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    monster_id, condition_id, action_name,
                    cond.get('inflicts', True),
                    cond.get('save_dc'), cond.get('save_ability'),
                    cond.get('duration_text')
                ))

            conn.commit()
            stats.record_success()

        except Exception as e:
            conn.rollback()
            stats.record_failure(f"{cond.get('monster_name', 'UNKNOWN')}: {str(e)}")

        if i % 100 == 0:
            log_progress(i, len(conditions), "monster conditions")


def import_spell_conditions(conn, conditions: List[Dict], stats: ImportStats) -> None:
    """Import spell condition relationships."""
    print(f"\n📥 Importing {len(conditions)} spell condition relationships...")

    for i, cond in enumerate(conditions, 1):
        try:
            spell_id = lookup_spell_by_name_source(conn, cond['spell_name'], cond['source'])
            if not spell_id:
                stats.record_skip(f"{cond['spell_name']}: Spell not found")
                continue

            condition_id = lookup_condition_type(conn, cond['condition'])
            if not condition_id:
                stats.record_warning(f"{cond['spell_name']}: Unknown condition '{cond['condition']}'")
                continue

            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO spell_conditions (
                        spell_id, condition_id, inflicts,
                        save_type, duration_text
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    spell_id, condition_id, cond.get('inflicts', True),
                    cond.get('save_ability'),
                    cond.get('duration_text')
                ))

            conn.commit()
            stats.record_success()

        except Exception as e:
            conn.rollback()
            stats.record_failure(f"{cond.get('spell_name', 'UNKNOWN')}: {str(e)}")

        if i % 100 == 0:
            log_progress(i, len(conditions), "spell conditions")


def import_item_damage(conn, damage_list: List[Dict], stats: ImportStats) -> None:
    """Import item damage relationships."""
    print(f"\n📥 Importing {len(damage_list)} item damage relationships...")

    for i, dmg in enumerate(damage_list, 1):
        try:
            item_id = lookup_item_by_name_source(conn, dmg['item_name'], dmg['source'])
            if not item_id:
                stats.record_skip(f"{dmg['item_name']}: Item not found")
                continue

            damage_type_id = None
            if dmg.get('damage_type'):
                damage_type_id = lookup_damage_type(conn, dmg['damage_type'])
                if not damage_type_id:
                    stats.record_warning(f"{dmg['item_name']}: Unknown damage type '{dmg['damage_type']}'")

            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO item_damage (
                        item_id, damage_dice, damage_bonus, damage_type_id,
                        versatile_dice, versatile_bonus
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    item_id, dmg.get('damage_dice'), dmg.get('damage_bonus', 0), damage_type_id,
                    dmg.get('versatile_dice'), dmg.get('versatile_bonus', 0)
                ))

            conn.commit()
            stats.record_success()

        except Exception as e:
            conn.rollback()
            stats.record_failure(f"{dmg.get('item_name', 'UNKNOWN')}: {str(e)}")

        if i % 100 == 0:
            log_progress(i, len(damage_list), "item damage")


def import_monster_attacks(conn, attacks: List[Dict], stats: ImportStats) -> None:
    """Import monster attack damage relationships."""
    print(f"\n📥 Importing {len(attacks)} monster attack relationships...")

    for i, atk in enumerate(attacks, 1):
        try:
            monster_id = lookup_monster_by_name_source(conn, atk['monster_name'], atk['source'])
            if not monster_id:
                stats.record_skip(f"{atk['monster_name']}: Monster not found")
                continue

            # Lookup attack type
            attack_type_id = None
            if atk.get('attack_type'):
                attack_type_id = lookup_attack_type(conn, atk['attack_type'])
                if not attack_type_id:
                    stats.record_warning(f"{atk['monster_name']}: Unknown attack type '{atk['attack_type']}'")

            # Lookup damage type
            damage_type_id = None
            if atk.get('damage_type'):
                damage_type_id = lookup_damage_type(conn, atk['damage_type'])
                if not damage_type_id:
                    stats.record_warning(f"{atk['monster_name']}: Unknown damage type '{atk['damage_type']}'")

            # Handle additional damage (first one only)
            # LIMITATION: monster_attacks schema only supports one extra damage entry.
            # 147 monsters (3.4%) have 2+ additional_damage entries in source data.
            # Only the first is imported; subsequent entries are lost.
            # Full data is preserved in monsters.data JSONB column.
            extra_damage_type_id = None
            extra_damage_dice = None
            extra_damage_bonus = 0
            if atk.get('additional_damage') and len(atk['additional_damage']) > 0:
                extra_dmg = atk['additional_damage'][0]
                extra_damage_dice = extra_dmg.get('damage_dice')
                extra_damage_bonus = extra_dmg.get('damage_bonus', 0)
                if extra_dmg.get('damage_type'):
                    extra_damage_type_id = lookup_damage_type(conn, extra_dmg['damage_type'])

            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO monster_attacks (
                        monster_id, action_name, attack_type_id,
                        to_hit_bonus, reach_ft, range_normal_ft, range_long_ft,
                        damage_dice, damage_bonus, damage_type_id,
                        extra_damage_dice, extra_damage_bonus, extra_damage_type_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (monster_id, action_name) DO NOTHING
                """, (
                    monster_id, atk['action_name'], attack_type_id,
                    atk.get('to_hit'), atk.get('reach'), atk.get('range_normal'), atk.get('range_long'),
                    atk.get('damage_dice'), atk.get('damage_bonus', 0), damage_type_id,
                    extra_damage_dice, extra_damage_bonus, extra_damage_type_id
                ))

            conn.commit()
            stats.record_success()

        except Exception as e:
            conn.rollback()
            stats.record_failure(f"{atk.get('monster_name', 'UNKNOWN')}: {str(e)}")

        if i % 100 == 0:
            log_progress(i, len(attacks), "monster attacks")


def import_spell_damage(conn, damage_list: List[Dict], stats: ImportStats) -> None:
    """Import spell damage relationships."""
    print(f"\n📥 Importing {len(damage_list)} spell damage relationships...")

    for i, dmg in enumerate(damage_list, 1):
        try:
            spell_id = lookup_spell_by_name_source(conn, dmg['spell_name'], dmg['source'])
            if not spell_id:
                stats.record_skip(f"{dmg['spell_name']}: Spell not found")
                continue

            damage_type_id = None
            if dmg.get('damage_type'):
                damage_type_id = lookup_damage_type(conn, dmg['damage_type'])
                if not damage_type_id:
                    stats.record_warning(f"{dmg['spell_name']}: Unknown damage type '{dmg['damage_type']}'")

            spell_level = dmg.get('spell_level', 0)

            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO spell_damage (
                        spell_id, spell_level, damage_dice, damage_bonus, damage_type_id
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    spell_id, spell_level, dmg.get('damage_dice'), dmg.get('damage_bonus', 0), damage_type_id
                ))

            conn.commit()
            stats.record_success()

        except Exception as e:
            conn.rollback()
            stats.record_failure(f"{dmg.get('spell_name', 'UNKNOWN')}: {str(e)}")

        if i % 100 == 0:
            log_progress(i, len(damage_list), "spell damage")


def main():
    """Main import function."""
    print("=" * 80)
    print("EXTRACTED RELATIONSHIP DATA IMPORT")
    print("=" * 80)

    # Load data files
    conditions, damage, cross_refs = load_data_files()

    # Connect to database
    print(f"🔌 Connecting to database...")
    conn = get_connection()
    print("✅ Database connection successful\n")

    # Import conditions
    print("=" * 80)
    print("PHASE 1: CONDITION RELATIONSHIPS")
    print("=" * 80)

    stats_items_cond = ImportStats()
    import_item_conditions(conn, conditions['items'], stats_items_cond)

    stats_monsters_cond = ImportStats()
    import_monster_conditions(conn, conditions['monsters'], stats_monsters_cond)

    stats_spells_cond = ImportStats()
    import_spell_conditions(conn, conditions['spells'], stats_spells_cond)

    # Print condition summaries
    print("\n" + "=" * 80)
    print("CONDITION IMPORT SUMMARY")
    print("=" * 80)
    print("\nItem Conditions:")
    stats_items_cond.print_summary()
    print("\nMonster Conditions:")
    stats_monsters_cond.print_summary()
    print("\nSpell Conditions:")
    stats_spells_cond.print_summary()

    # Import damage
    print("\n" + "=" * 80)
    print("PHASE 2: DAMAGE RELATIONSHIPS")
    print("=" * 80)

    stats_items_dmg = ImportStats()
    import_item_damage(conn, damage['items'], stats_items_dmg)

    stats_monsters_dmg = ImportStats()
    import_monster_attacks(conn, damage['monster_attacks'], stats_monsters_dmg)

    stats_spells_dmg = ImportStats()
    import_spell_damage(conn, damage['spells'], stats_spells_dmg)

    # Print damage summaries
    print("\n" + "=" * 80)
    print("DAMAGE IMPORT SUMMARY")
    print("=" * 80)
    print("\nItem Damage:")
    stats_items_dmg.print_summary()
    print("\nMonster Attacks:")
    stats_monsters_dmg.print_summary()
    print("\nSpell Damage:")
    stats_spells_dmg.print_summary()

    # Close connection
    conn.close()
    print("\n🔌 Database connection closed")

    # Exit with appropriate code
    total_failed = (stats_items_cond.failed + stats_monsters_cond.failed + stats_spells_cond.failed +
                    stats_items_dmg.failed + stats_monsters_dmg.failed + stats_spells_dmg.failed)
    if total_failed > 0:
        log_error(f"Import completed with {total_failed} failures")
        sys.exit(1)
    else:
        total_success = (stats_items_cond.succeeded + stats_monsters_cond.succeeded + stats_spells_cond.succeeded +
                        stats_items_dmg.succeeded + stats_monsters_dmg.succeeded + stats_spells_dmg.succeeded)
        log_success(f"Successfully imported {total_success} relationships (conditions + damage)")
        sys.exit(0)


if __name__ == '__main__':
    main()
