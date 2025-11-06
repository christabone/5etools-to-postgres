#!/usr/bin/env python3
"""
Extract and clean name fields from cleaned data.

Phase 0.6: Markup Extraction & Advanced Normalization

This script:
1. Removes ALL {@...} markup from name fields
2. Extracts base name and variant from parentheses
3. Parses quantities, bonuses, containers from item names
4. Creates new fields: base_name, variant_name, container_type, default_quantity, etc.

Input: cleaned_data/items.json, cleaned_data/monsters.json
Output: cleaned_data/items_extracted.json, cleaned_data/monsters_extracted.json
"""

import json
import re
from typing import Dict, Any, Optional, Tuple
from pathlib import Path


def strip_markup(text: str) -> str:
    """
    Remove all {@...} markup tags from text.

    Examples:
        "{@creature Aboleth|MM} Spawn" -> "Aboleth Spawn"
        "{@item longsword|phb}" -> "longsword"
    """
    # Pattern: {@type anything|source|display}
    pattern = r'\{@[^}]+\}'
    return re.sub(pattern, '', text).strip()


def parse_item_name(name: str) -> Dict[str, Any]:
    """
    Parse item name to extract base name, variant, quantity, container, bonus.

    Examples:
        "Arrow (20)" -> {base_name: "Arrow", default_quantity: 20}
        "Acid (vial)" -> {base_name: "Acid", container_type: "vial"}
        "+1 Longsword" -> {base_name: "Longsword", bonus_display: "+1"}
        "Longsword (+1)" -> {base_name: "Longsword", bonus_display: "+1"}
    """
    result = {
        "base_name": name,
        "variant_name": None,
        "container_type": None,
        "default_quantity": None,
        "bonus_display": None
    }

    # First, strip any markup
    clean_name = strip_markup(name)

    # Check for leading bonus: "+1 Longsword"
    leading_bonus_match = re.match(r'^(\+\d+)\s+(.+)$', clean_name)
    if leading_bonus_match:
        result["bonus_display"] = leading_bonus_match.group(1)
        clean_name = leading_bonus_match.group(2)

    # Check for parentheses: "Arrow (20)" or "Acid (vial)" or "Longsword (+1)"
    paren_match = re.match(r'^(.+?)\s*\((.+?)\)$', clean_name)
    if paren_match:
        base = paren_match.group(1).strip()
        in_parens = paren_match.group(2).strip()

        # Check if it's a number (quantity)
        if in_parens.isdigit():
            result["base_name"] = base
            result["default_quantity"] = int(in_parens)
        # Check if it's a bonus
        elif re.match(r'^\+\d+$', in_parens):
            result["base_name"] = base
            result["bonus_display"] = in_parens
        # Otherwise it's a variant or container
        else:
            # Common container types
            containers = ["vial", "flask", "bottle", "pouch", "bag", "jar", "jug"]
            if in_parens.lower() in containers:
                result["base_name"] = base
                result["container_type"] = in_parens.lower()
            else:
                result["base_name"] = base
                result["variant_name"] = in_parens
    else:
        result["base_name"] = clean_name

    return result


def parse_monster_name(name: str) -> Dict[str, Any]:
    """
    Parse monster name to extract base name and variant.

    Examples:
        "{@creature Aboleth|MM} Spawn" -> {base_name: "Aboleth", variant_name: "Spawn"}
        "Empyrean (Maimed){@note maimed}" -> {base_name: "Empyrean", variant_name: "Maimed"}
        "Goblin Boss" -> {base_name: "Goblin Boss"}
        "Ayo Jabe (Tier 1)" -> {base_name: "Ayo Jabe", variant_name: "Tier 1"}
    """
    result = {
        "base_name": name,
        "variant_name": None,
        "variant_notes": None
    }

    # First, strip all markup
    clean_name = strip_markup(name)

    # Check for parentheses: "Empyrean (Maimed)" or "Ayo Jabe (Tier 1)"
    paren_match = re.match(r'^(.+?)\s*\((.+?)\)$', clean_name)
    if paren_match:
        result["base_name"] = paren_match.group(1).strip()
        result["variant_name"] = paren_match.group(2).strip()
    else:
        result["base_name"] = clean_name

    return result


def extract_item_names(items: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """
    Process all items to extract name components.
    """
    for item in items:
        name_parts = parse_item_name(item["name"])

        # Update the item with extracted fields
        item["name"] = strip_markup(item["name"])  # Clean the display name
        item["base_name"] = name_parts["base_name"]
        item["variant_name"] = name_parts["variant_name"]
        item["container_type"] = name_parts["container_type"]
        item["default_quantity"] = name_parts["default_quantity"]
        item["bonus_display"] = name_parts["bonus_display"]

    return items


def extract_monster_names(monsters: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """
    Process all monsters to extract name components.
    """
    for monster in monsters:
        name_parts = parse_monster_name(monster["name"])

        # Update the monster with extracted fields
        monster["name"] = strip_markup(monster["name"])  # Clean the display name
        monster["base_name"] = name_parts["base_name"]
        monster["variant_name"] = name_parts["variant_name"]
        monster["variant_notes"] = name_parts["variant_notes"]

    return monsters


def extract_spell_names(spells: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """
    Process all spells to clean names (spells don't have complex name issues).
    """
    for spell in spells:
        # Just strip any markup (should be rare/non-existent)
        spell["name"] = strip_markup(spell["name"])

    return spells


def main():
    """Main extraction process."""
    print("=" * 60)
    print("Phase 0.6: Name Extraction & Cleaning")
    print("=" * 60)

    base_dir = Path(__file__).parent
    cleaned_dir = base_dir / "cleaned_data"

    # Process items
    print("\n[1/3] Processing items...")
    items_path = cleaned_dir / "items.json"
    with open(items_path) as f:
        items = json.load(f)

    print(f"  Loaded {len(items)} items")

    # Show some examples before
    print("\n  Sample BEFORE:")
    for item in items[:3]:
        print(f"    - {item['name']}")

    items = extract_item_names(items)

    # Show examples after
    print("\n  Sample AFTER:")
    for item in items[:3]:
        print(f"    - name: {item['name']}")
        print(f"      base_name: {item['base_name']}")
        if item['variant_name']:
            print(f"      variant_name: {item['variant_name']}")
        if item['default_quantity']:
            print(f"      default_quantity: {item['default_quantity']}")
        if item['container_type']:
            print(f"      container_type: {item['container_type']}")
        if item['bonus_display']:
            print(f"      bonus_display: {item['bonus_display']}")

    # Save
    output_path = cleaned_dir / "items_extracted.json"
    with open(output_path, 'w') as f:
        json.dump(items, f, indent=2)
    print(f"\n  ✓ Saved to {output_path}")

    # Process monsters
    print("\n[2/3] Processing monsters...")
    monsters_path = cleaned_dir / "monsters.json"
    with open(monsters_path) as f:
        monsters = json.load(f)

    print(f"  Loaded {len(monsters)} monsters")

    # Show some examples before
    print("\n  Sample BEFORE:")
    for monster in monsters[:3]:
        print(f"    - {monster['name']}")

    monsters = extract_monster_names(monsters)

    # Show examples after
    print("\n  Sample AFTER:")
    for monster in monsters[:3]:
        print(f"    - name: {monster['name']}")
        print(f"      base_name: {monster['base_name']}")
        if monster['variant_name']:
            print(f"      variant_name: {monster['variant_name']}")

    # Save
    output_path = cleaned_dir / "monsters_extracted.json"
    with open(output_path, 'w') as f:
        json.dump(monsters, f, indent=2)
    print(f"\n  ✓ Saved to {output_path}")

    # Process spells
    print("\n[3/3] Processing spells...")
    spells_path = cleaned_dir / "spells.json"
    with open(spells_path) as f:
        spells = json.load(f)

    print(f"  Loaded {len(spells)} spells")

    spells = extract_spell_names(spells)

    # Save
    output_path = cleaned_dir / "spells_extracted.json"
    with open(output_path, 'w') as f:
        json.dump(spells, f, indent=2)
    print(f"\n  ✓ Saved to {output_path}")

    # Summary statistics
    print("\n" + "=" * 60)
    print("Summary Statistics")
    print("=" * 60)

    items_with_quantity = sum(1 for i in items if i.get('default_quantity'))
    items_with_container = sum(1 for i in items if i.get('container_type'))
    items_with_bonus = sum(1 for i in items if i.get('bonus_display'))
    items_with_variant = sum(1 for i in items if i.get('variant_name'))

    monsters_with_variant = sum(1 for m in monsters if m.get('variant_name'))

    print(f"\nItems:")
    print(f"  - Total: {len(items)}")
    print(f"  - With default quantity: {items_with_quantity}")
    print(f"  - With container type: {items_with_container}")
    print(f"  - With bonus display: {items_with_bonus}")
    print(f"  - With variant name: {items_with_variant}")

    print(f"\nMonsters:")
    print(f"  - Total: {len(monsters)}")
    print(f"  - With variant name: {monsters_with_variant}")

    print(f"\nSpells:")
    print(f"  - Total: {len(spells)}")

    print("\n✓ Name extraction complete!")


if __name__ == "__main__":
    main()
