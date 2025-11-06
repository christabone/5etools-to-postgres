#!/usr/bin/env python3
"""
Extract damage information from descriptive text and structured fields.

Phase 0.6: Markup Extraction & Advanced Normalization

This script:
1. Parses {@damage dice+bonus} tags from text
2. Extracts damage type from surrounding context
3. Extracts attack information ({@atk type}, {@hit bonus})
4. Parses structured damage fields (dmg1, dmgType from items)
5. Builds structured data for damage tables

Output: extraction_data/damage_extracted.json

Format:
{
  "items": [
    {
      "item_name": "Longsword",
      "source": "PHB",
      "damage_dice": "1d8",
      "damage_bonus": 0,
      "damage_type": "slashing",
      "versatile_dice": "1d10"
    }
  ],
  "monster_attacks": [
    {
      "monster_name": "Goblin",
      "source": "MM",
      "action_name": "Scimitar",
      "attack_type": "melee weapon",
      "to_hit": 4,
      "reach": 5,
      "damage_dice": "1d6",
      "damage_bonus": 2,
      "damage_type": "slashing"
    }
  ],
  "spells": [...]
}
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from collections import defaultdict


# Attack type codes
ATTACK_TYPES = {
    'mw': 'melee weapon',
    'rw': 'ranged weapon',
    'ms': 'melee spell',
    'rs': 'ranged spell',
    'mw,rw': 'melee or ranged weapon',
    'ms,rs': 'melee or ranged spell'
}

# Damage type keywords
DAMAGE_TYPES = [
    'bludgeoning', 'piercing', 'slashing',  # Physical
    'fire', 'cold', 'lightning', 'thunder', 'acid', 'poison',  # Elemental
    'necrotic', 'radiant', 'psychic', 'force'  # Magical
]


def parse_damage_expression(expr: str) -> Tuple[Optional[str], int]:
    """
    Parse a damage expression into dice and bonus.

    Examples:
        "2d8 + 3" -> ("2d8", 3)
        "1d6" -> ("1d6", 0)
        "10" -> (None, 10)
    """
    expr = expr.strip()

    # Pattern: XdY + Z or XdY or just Z
    match = re.match(r'(\d+d\d+)(?:\s*\+\s*(\d+))?', expr)
    if match:
        dice = match.group(1)
        bonus = int(match.group(2)) if match.group(2) else 0
        return (dice, bonus)

    # Just a number
    match = re.match(r'(\d+)', expr)
    if match:
        return (None, int(match.group(1)))

    return (None, 0)


def extract_damage_type_from_text(text: str, damage_pos: int) -> Optional[str]:
    """
    Extract damage type from text near a damage expression.

    Looks for damage type keywords within 50 characters after the damage tag.
    """
    # Look at text after the damage expression
    after_text = text[damage_pos:damage_pos + 50].lower()

    for dtype in DAMAGE_TYPES:
        if dtype in after_text:
            return dtype

    return None


def extract_reach_or_range(text: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Extract reach (melee) or range (ranged) from attack text.

    Examples:
        "reach 5 ft." -> (5, None)
        "range 150/600 ft." -> (150, 600)
    """
    # Reach pattern
    reach_match = re.search(r'reach (\d+) ft', text)
    if reach_match:
        return (int(reach_match.group(1)), None)

    # Range pattern (normal/long)
    range_match = re.search(r'range (\d+)/(\d+) ft', text)
    if range_match:
        return (int(range_match.group(1)), int(range_match.group(2)))

    # Single range
    range_match = re.search(r'range (\d+) ft', text)
    if range_match:
        return (int(range_match.group(1)), None)

    return (None, None)


def extract_monster_attack(monster_name: str, source: str, action_name: str, text: str) -> Optional[Dict[str, Any]]:
    """
    Extract attack information from a monster action's text.

    Returns structured attack data or None if not an attack.
    """
    # Check if this is an attack (has {@atk} tag)
    atk_match = re.search(r'\{@atk ([^}]+)\}', text)
    if not atk_match:
        return None

    attack_type_code = atk_match.group(1)
    attack_type = ATTACK_TYPES.get(attack_type_code, attack_type_code)

    # Extract to-hit bonus
    to_hit = None
    hit_match = re.search(r'\{@hit ([^}]+)\}', text)
    if hit_match:
        try:
            to_hit = int(hit_match.group(1).lstrip('+'))
        except ValueError:
            pass

    # Extract reach or range
    reach, range_long = extract_reach_or_range(text)

    # Extract damage expressions
    damage_matches = list(re.finditer(r'\{@damage ([^}]+)\}', text))

    if not damage_matches:
        # No damage tags, but still an attack (might be special effect)
        return {
            'monster_name': monster_name,
            'source': source,
            'action_name': action_name,
            'attack_type': attack_type,
            'to_hit': to_hit,
            'reach': reach,
            'range_normal': range_long if range_long else reach,  # Use range if present, else reach
            'range_long': range_long,
            'damage_dice': None,
            'damage_bonus': None,
            'damage_type': None,
            'additional_damage': []
        }

    # Parse first damage (primary)
    first_damage = damage_matches[0]
    damage_expr = first_damage.group(1)
    dice, bonus = parse_damage_expression(damage_expr)
    damage_type = extract_damage_type_from_text(text, first_damage.start())

    # Parse additional damage (if any)
    additional_damage = []
    for dmg_match in damage_matches[1:]:
        add_expr = dmg_match.group(1)
        add_dice, add_bonus = parse_damage_expression(add_expr)
        add_type = extract_damage_type_from_text(text, dmg_match.start())
        additional_damage.append({
            'damage_dice': add_dice,
            'damage_bonus': add_bonus,
            'damage_type': add_type
        })

    return {
        'monster_name': monster_name,
        'source': source,
        'action_name': action_name,
        'attack_type': attack_type,
        'to_hit': to_hit,
        'reach': reach,
        'range_normal': range_long if range_long else reach,
        'range_long': range_long,
        'damage_dice': dice,
        'damage_bonus': bonus,
        'damage_type': damage_type,
        'additional_damage': additional_damage,
        'full_text': text
    }


def extract_from_entries(entries: Any) -> List[str]:
    """Extract text from entries field (string, list, or nested structure)."""
    texts = []

    if isinstance(entries, str):
        texts.append(entries)
    elif isinstance(entries, list):
        for entry in entries:
            if isinstance(entry, str):
                texts.append(entry)
            elif isinstance(entry, dict):
                if 'entries' in entry:
                    texts.extend(extract_from_entries(entry['entries']))
                if 'items' in entry:
                    texts.extend(extract_from_entries(entry['items']))

    return texts


def extract_item_damage(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract damage from items."""
    results = []

    for item in items:
        item_name = item.get('name', 'Unknown')
        source = item.get('source', 'Unknown')

        # Check structured damage fields (weapons)
        if 'dmg1' in item:
            damage_dice, damage_bonus = parse_damage_expression(item['dmg1'])
            damage_type_code = item.get('dmgType', 'unknown')

            # Map damage type codes (P=piercing, S=slashing, B=bludgeoning, etc.)
            type_map = {
                'P': 'piercing', 'S': 'slashing', 'B': 'bludgeoning',
                'N': 'necrotic', 'R': 'radiant', 'F': 'fire', 'C': 'cold',
                'L': 'lightning', 'T': 'thunder', 'A': 'acid', 'I': 'poison',
                'O': 'force', 'Y': 'psychic'
            }
            damage_type = type_map.get(damage_type_code, damage_type_code)

            result = {
                'item_name': item_name,
                'source': source,
                'damage_dice': damage_dice,
                'damage_bonus': damage_bonus,
                'damage_type': damage_type,
                'context': 'weapon_stats'
            }

            # Check for versatile damage
            if 'dmg2' in item:
                vers_dice, vers_bonus = parse_damage_expression(item['dmg2'])
                result['versatile_dice'] = vers_dice
                result['versatile_bonus'] = vers_bonus

            results.append(result)

        # Also check entries for {@damage} tags (magical items with special attacks)
        if 'entries' in item:
            texts = extract_from_entries(item['entries'])
            for text in texts:
                damage_matches = list(re.finditer(r'\{@damage ([^}]+)\}', text))
                for dmg_match in damage_matches:
                    damage_expr = dmg_match.group(1)
                    dice, bonus = parse_damage_expression(damage_expr)
                    damage_type = extract_damage_type_from_text(text, dmg_match.start())

                    results.append({
                        'item_name': item_name,
                        'source': source,
                        'damage_dice': dice,
                        'damage_bonus': bonus,
                        'damage_type': damage_type,
                        'context': 'special_property'
                    })

    return results


def extract_monster_damage(monsters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract damage/attacks from monsters."""
    results = []

    for monster in monsters:
        monster_name = monster.get('name', 'Unknown')
        source = monster.get('source', 'Unknown')

        # Check action, bonus, legendary, and reaction fields
        fields_to_check = [
            ('action', 'action'),
            ('bonus', 'bonus action'),
            ('legendary', 'legendary action'),
            ('reaction', 'reaction')
        ]

        for field_name, context_type in fields_to_check:
            if field_name in monster:
                for ability in monster[field_name]:
                    ability_name = ability.get('name', 'Unknown')

                    if 'entries' in ability:
                        texts = extract_from_entries(ability['entries'])
                        for text in texts:
                            attack_data = extract_monster_attack(
                                monster_name, source, ability_name, text
                            )
                            if attack_data:
                                attack_data['context'] = context_type
                                results.append(attack_data)

    return results


def extract_spell_damage(spells: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract damage from spells."""
    results = []

    for spell in spells:
        spell_name = spell.get('name', 'Unknown')
        source = spell.get('source', 'Unknown')
        spell_level = spell.get('level', 0)

        # Extract damage from entries
        if 'entries' in spell:
            texts = extract_from_entries(spell['entries'])
            full_text = ' '.join(texts)

            damage_matches = list(re.finditer(r'\{@damage ([^}]+)\}', full_text))

            for dmg_match in damage_matches:
                damage_expr = dmg_match.group(1)
                dice, bonus = parse_damage_expression(damage_expr)
                damage_type = extract_damage_type_from_text(full_text, dmg_match.start())

                results.append({
                    'spell_name': spell_name,
                    'source': source,
                    'spell_level': spell_level,
                    'damage_dice': dice,
                    'damage_bonus': bonus,
                    'damage_type': damage_type
                })

    return results


def main():
    """Main extraction process."""
    print("=" * 60)
    print("Phase 0.6: Damage Extraction")
    print("=" * 60)

    base_dir = Path(__file__).parent
    cleaned_dir = base_dir / "cleaned_data"
    output_dir = base_dir / "extraction_data"
    output_dir.mkdir(exist_ok=True)

    # Extract from items
    print("\n[1/3] Extracting damage from items...")
    items_path = cleaned_dir / "items_extracted.json"
    with open(items_path) as f:
        items = json.load(f)

    print(f"  Loaded {len(items)} items")
    item_damage = extract_item_damage(items)
    print(f"  Found {len(item_damage)} damage records")

    # Show sample
    if item_damage:
        print("\n  Sample extractions:")
        for dmg in item_damage[:3]:
            print(f"    - {dmg['item_name']}: {dmg['damage_dice']} {dmg['damage_type']}")

    # Extract from monsters
    print("\n[2/3] Extracting damage from monsters...")
    monsters_path = cleaned_dir / "monsters_extracted.json"
    with open(monsters_path) as f:
        monsters = json.load(f)

    print(f"  Loaded {len(monsters)} monsters")
    monster_attacks = extract_monster_damage(monsters)
    print(f"  Found {len(monster_attacks)} attack records")

    # Show sample
    if monster_attacks:
        print("\n  Sample extractions:")
        for atk in monster_attacks[:3]:
            print(f"    - {atk['monster_name']} ({atk['action_name']})")
            print(f"      {atk['attack_type']}, +{atk['to_hit']} to hit")
            if atk['damage_dice']:
                print(f"      {atk['damage_dice']}+{atk['damage_bonus']} {atk['damage_type']}")

    # Extract from spells
    print("\n[3/3] Extracting damage from spells...")
    spells_path = cleaned_dir / "spells_extracted.json"
    with open(spells_path) as f:
        spells = json.load(f)

    print(f"  Loaded {len(spells)} spells")
    spell_damage = extract_spell_damage(spells)
    print(f"  Found {len(spell_damage)} damage records")

    # Show sample
    if spell_damage:
        print("\n  Sample extractions:")
        for dmg in spell_damage[:3]:
            print(f"    - {dmg['spell_name']} (level {dmg['spell_level']})")
            print(f"      {dmg['damage_dice']} {dmg['damage_type']}")

    # Combine and save
    output_data = {
        'items': item_damage,
        'monster_attacks': monster_attacks,
        'spells': spell_damage
    }

    output_path = output_dir / "damage_extracted.json"
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n  ✓ Saved to {output_path}")

    # Summary statistics
    print("\n" + "=" * 60)
    print("Summary Statistics")
    print("=" * 60)

    total = len(item_damage) + len(monster_attacks) + len(spell_damage)
    print(f"\nTotal damage records: {total}")
    print(f"  - Items: {len(item_damage)}")
    print(f"  - Monster attacks: {len(monster_attacks)}")
    print(f"  - Spells: {len(spell_damage)}")

    # Count by damage type
    from collections import Counter
    all_types = [d.get('damage_type') for d in item_damage + monster_attacks + spell_damage if d.get('damage_type')]
    type_counts = Counter(all_types)
    print(f"\nDamage by type:")
    for dtype, count in sorted(type_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {dtype}: {count}")

    # Attack types
    atk_types = [a.get('attack_type') for a in monster_attacks if a.get('attack_type')]
    atk_counts = Counter(atk_types)
    print(f"\nMonster attacks by type:")
    for atype, count in sorted(atk_counts.items(), key=lambda x: -x[1]):
        print(f"  {atype}: {count}")

    print("\n✓ Damage extraction complete!")


if __name__ == "__main__":
    main()
