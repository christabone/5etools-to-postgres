#!/usr/bin/env python3
"""
Normalize bonus fields from strings to integers.

Phase 0.6: Markup Extraction & Advanced Normalization

This script:
1. Converts bonus fields from "+1" to 1 (integer)
2. Validates all bonus fields are now integers
3. Handles edge cases (already integer, missing +, etc.)

Bonus fields to normalize:
- bonusWeapon
- bonusAc
- bonusSpellAttack
- bonusSpellSaveDc
- bonusSavingThrow

Input: cleaned_data/*_extracted.json
Output: Modifies files in place
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path


BONUS_FIELDS = [
    "bonusWeapon",
    "bonusAc",
    "bonusSpellAttack",
    "bonusSpellSaveDc",
    "bonusSavingThrow",
    "bonusAbilityCheck",
    "bonusProficiencyBonus"
]


def normalize_bonus(value: Any) -> Optional[int]:
    """
    Normalize a bonus value to an integer.

    Examples:
        "+1" -> 1
        "+2" -> 2
        1 -> 1 (already int)
        "3" -> 3 (missing +)
        None -> None
    """
    if value is None:
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, str):
        # Strip + prefix if present
        clean_value = value.strip().lstrip('+')
        try:
            return int(clean_value)
        except ValueError:
            print(f"  ⚠️  Could not parse bonus value: {value}")
            return None

    print(f"  ⚠️  Unexpected bonus type: {type(value).__name__} = {value}")
    return None


def normalize_item_bonuses(items: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """Normalize all bonus fields in items."""
    normalized_count = 0

    for item in items:
        for field in BONUS_FIELDS:
            if field in item:
                original = item[field]
                normalized = normalize_bonus(original)

                if normalized is not None and normalized != original:
                    item[field] = normalized
                    normalized_count += 1

    return items, normalized_count


def normalize_monster_bonuses(monsters: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """
    Normalize bonus fields in monsters (if any exist).

    Monsters typically don't have bonus fields like items do, but check anyway.
    """
    normalized_count = 0

    for monster in monsters:
        for field in BONUS_FIELDS:
            if field in monster:
                original = monster[field]
                normalized = normalize_bonus(original)

                if normalized is not None and normalized != original:
                    monster[field] = normalized
                    normalized_count += 1

    return monsters, normalized_count


def validate_bonuses(records: list[Dict[str, Any]], record_type: str) -> bool:
    """
    Validate that all bonus fields are integers.

    Returns True if all valid, False otherwise.
    """
    all_valid = True

    for record in records:
        for field in BONUS_FIELDS:
            if field in record:
                value = record[field]
                if not isinstance(value, int):
                    print(f"  ❌ {record_type} '{record['name']}' has non-integer {field}: {value} ({type(value).__name__})")
                    all_valid = False

    return all_valid


def main():
    """Main normalization process."""
    print("=" * 60)
    print("Phase 0.6: Bonus Field Normalization")
    print("=" * 60)

    base_dir = Path(__file__).parent
    cleaned_dir = base_dir / "cleaned_data"

    # Process items
    print("\n[1/3] Normalizing item bonuses...")
    items_path = cleaned_dir / "items_extracted.json"
    with open(items_path) as f:
        items = json.load(f)

    print(f"  Loaded {len(items)} items")

    # Show examples before
    print("\n  Sample BEFORE:")
    bonus_items = [i for i in items if any(f in i for f in BONUS_FIELDS)][:3]
    for item in bonus_items:
        print(f"    {item['name']}:")
        for field in BONUS_FIELDS:
            if field in item:
                print(f"      {field}: {item[field]} ({type(item[field]).__name__})")

    items, normalized_count = normalize_item_bonuses(items)

    # Show examples after
    print("\n  Sample AFTER:")
    for item in bonus_items:
        print(f"    {item['name']}:")
        for field in BONUS_FIELDS:
            if field in item:
                print(f"      {field}: {item[field]} ({type(item[field]).__name__})")

    print(f"\n  ✓ Normalized {normalized_count} bonus fields")

    # Validate
    print("\n  Validating...")
    if validate_bonuses(items, "Item"):
        print("  ✓ All item bonus fields are valid integers")
    else:
        print("  ❌ Some item bonus fields are invalid")

    # Save
    with open(items_path, 'w') as f:
        json.dump(items, f, indent=2)
    print(f"\n  ✓ Saved to {items_path}")

    # Process monsters
    print("\n[2/3] Normalizing monster bonuses...")
    monsters_path = cleaned_dir / "monsters_extracted.json"
    with open(monsters_path) as f:
        monsters = json.load(f)

    print(f"  Loaded {len(monsters)} monsters")

    monsters, normalized_count = normalize_monster_bonuses(monsters)

    if normalized_count > 0:
        print(f"\n  ✓ Normalized {normalized_count} bonus fields")

        # Validate
        print("\n  Validating...")
        if validate_bonuses(monsters, "Monster"):
            print("  ✓ All monster bonus fields are valid integers")
        else:
            print("  ❌ Some monster bonus fields are invalid")

        # Save
        with open(monsters_path, 'w') as f:
            json.dump(monsters, f, indent=2)
        print(f"\n  ✓ Saved to {monsters_path}")
    else:
        print("  ℹ️  No bonus fields found in monsters (expected)")

    # Process spells (spells don't typically have bonus fields)
    print("\n[3/3] Checking spells...")
    spells_path = cleaned_dir / "spells_extracted.json"
    with open(spells_path) as f:
        spells = json.load(f)

    spells_with_bonuses = [s for s in spells if any(f in s for f in BONUS_FIELDS)]
    if spells_with_bonuses:
        print(f"  ⚠️  Found {len(spells_with_bonuses)} spells with bonus fields (unexpected)")
    else:
        print("  ℹ️  No bonus fields found in spells (expected)")

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    items_with_bonuses = sum(1 for i in items if any(f in i for f in BONUS_FIELDS))
    print(f"\nItems with bonus fields: {items_with_bonuses}")
    for field in BONUS_FIELDS:
        count = sum(1 for i in items if field in i)
        if count > 0:
            print(f"  - {field}: {count}")

    print("\n✓ Bonus normalization complete!")


if __name__ == "__main__":
    main()
