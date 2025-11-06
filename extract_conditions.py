#!/usr/bin/env python3
"""
Extract condition references from descriptive text.

Phase 0.6: Markup Extraction & Advanced Normalization

This script:
1. Parses {@condition name|source} tags from all text fields
2. Extracts save DC and ability from surrounding context
3. Extracts duration information
4. Builds structured data for junction tables

Output: extraction_data/conditions_extracted.json

Format:
{
  "items": [
    {
      "item_name": "Dagger of Venom",
      "source": "DMG",
      "condition": "poisoned",
      "condition_source": "XPHB",
      "inflicts": true,
      "save_dc": 15,
      "save_ability": "Constitution",
      "duration_text": "1 minute",
      "context": "action|trait|property",
      "context_name": "Special Property",
      "full_text": "..."
    }
  ],
  "monsters": [...],
  "spells": [...]
}
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from collections import defaultdict


def extract_dc(text: str) -> Optional[int]:
    """
    Extract DC value from text.

    Examples:
        "{@dc 15}" -> 15
        "DC 13" -> 13
    """
    # Try {@dc X} pattern first
    match = re.search(r'\{@dc (\d+)\}', text)
    if match:
        return int(match.group(1))

    # Try plain "DC X" pattern
    match = re.search(r'\bDC (\d+)\b', text)
    if match:
        return int(match.group(1))

    return None


def extract_save_ability(text: str) -> Optional[str]:
    """
    Extract saving throw ability from text.

    Examples:
        "Strength saving throw" -> "Strength"
        "Wisdom save" -> "Wisdom"
    """
    abilities = ['Strength', 'Dexterity', 'Constitution', 'Intelligence', 'Wisdom', 'Charisma']

    for ability in abilities:
        # Look for "Ability saving throw" or "Ability save"
        if re.search(rf'\b{ability}\s+sav(?:ing throw|e)\b', text, re.IGNORECASE):
            return ability

    return None


def extract_duration(text: str) -> Optional[str]:
    """
    Extract duration from text.

    Examples:
        "for 1 minute" -> "1 minute"
        "until the end of your next turn" -> "until the end of your next turn"
        "for 1 hour" -> "1 hour"
    """
    # Pattern: "for X time-unit"
    match = re.search(r'for (\d+\s+(?:round|minute|hour|day)s?)', text)
    if match:
        return match.group(1)

    # Pattern: "until X"
    match = re.search(r'until ([^.;,]+?)(?:[.;,]|$)', text)
    if match:
        duration = match.group(1).strip()
        if len(duration) < 80:  # Reasonable duration text length
            return duration

    return None


def is_immunity_or_resistance(text: str, condition_pos: int) -> bool:
    """
    Check if this condition reference is about immunity/resistance rather than inflicting.

    Examples:
        "immune to the poisoned condition" -> True
        "advantage on saves against being charmed" -> True
        "has the poisoned condition" -> False
    """
    # Get text before the condition tag (up to 100 chars)
    before_text = text[max(0, condition_pos - 100):condition_pos].lower()

    immunity_keywords = [
        'immune to',
        'immunity to',
        'can\'t be',
        'cannot be',
        'advantage on saving throws against',
        'advantage on saves against'
    ]

    for keyword in immunity_keywords:
        if keyword in before_text:
            return True

    return False


def extract_conditions_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Extract all condition references from a text string.

    Returns list of condition extractions with context.
    """
    if not isinstance(text, str):
        return []

    results = []

    # Find all {@condition name|source} tags
    pattern = r'\{@condition ([^}|]+)(?:\|([^}]+))?\}'

    for match in re.finditer(pattern, text):
        condition_name = match.group(1).strip()
        condition_source = match.group(2).strip() if match.group(2) else None

        # Normalize condition name (lowercase for consistency)
        condition_name = condition_name.lower()

        # Check if this is immunity/resistance or inflicting
        inflicts = not is_immunity_or_resistance(text, match.start())

        # Extract DC and save ability from surrounding text
        # Look within 200 characters before and after the condition
        context_start = max(0, match.start() - 200)
        context_end = min(len(text), match.end() + 200)
        context_text = text[context_start:context_end]

        dc = extract_dc(context_text)
        save_ability = extract_save_ability(context_text)
        duration = extract_duration(context_text)

        results.append({
            'condition': condition_name,
            'condition_source': condition_source,
            'inflicts': inflicts,
            'save_dc': dc,
            'save_ability': save_ability,
            'duration_text': duration,
            'full_text': text
        })

    return results


def extract_from_entries(entries: Any) -> List[str]:
    """
    Extract text from entries field (which can be string, list, or nested structure).
    """
    texts = []

    if isinstance(entries, str):
        texts.append(entries)
    elif isinstance(entries, list):
        for entry in entries:
            if isinstance(entry, str):
                texts.append(entry)
            elif isinstance(entry, dict):
                # Handle nested structures like {type: "entries", entries: [...]}
                if 'entries' in entry:
                    texts.extend(extract_from_entries(entry['entries']))
                # Also check for 'items' field
                if 'items' in entry:
                    texts.extend(extract_from_entries(entry['items']))

    return texts


def extract_item_conditions(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract conditions from items."""
    results = []

    for item in items:
        item_name = item.get('name', 'Unknown')
        source = item.get('source', 'Unknown')

        # Check entries field
        if 'entries' in item:
            texts = extract_from_entries(item['entries'])
            for text in texts:
                conditions = extract_conditions_from_text(text)
                for cond in conditions:
                    results.append({
                        'item_name': item_name,
                        'source': source,
                        'context': 'entries',
                        'context_name': None,
                        **cond
                    })

    return results


def extract_monster_conditions(monsters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract conditions from monsters."""
    results = []

    for monster in monsters:
        monster_name = monster.get('name', 'Unknown')
        source = monster.get('source', 'Unknown')

        # Check various fields that can contain conditions
        fields_to_check = [
            ('trait', 'trait'),
            ('action', 'action'),
            ('bonus', 'bonus action'),
            ('reaction', 'reaction'),
            ('legendary', 'legendary action')
        ]

        for field_name, context_type in fields_to_check:
            if field_name in monster:
                for ability in monster[field_name]:
                    ability_name = ability.get('name', 'Unknown')

                    if 'entries' in ability:
                        texts = extract_from_entries(ability['entries'])
                        for text in texts:
                            conditions = extract_conditions_from_text(text)
                            for cond in conditions:
                                results.append({
                                    'monster_name': monster_name,
                                    'source': source,
                                    'context': context_type,
                                    'context_name': ability_name,
                                    **cond
                                })

    return results


def extract_spell_conditions(spells: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract conditions from spells."""
    results = []

    for spell in spells:
        spell_name = spell.get('name', 'Unknown')
        source = spell.get('source', 'Unknown')

        # Check entries field
        if 'entries' in spell:
            texts = extract_from_entries(spell['entries'])
            for text in texts:
                conditions = extract_conditions_from_text(text)
                for cond in conditions:
                    results.append({
                        'spell_name': spell_name,
                        'source': source,
                        'context': 'entries',
                        'context_name': None,
                        **cond
                    })

    return results


def main():
    """Main extraction process."""
    print("=" * 60)
    print("Phase 0.6: Condition Extraction")
    print("=" * 60)

    base_dir = Path(__file__).parent
    cleaned_dir = base_dir / "cleaned_data"
    output_dir = base_dir / "extraction_data"
    output_dir.mkdir(exist_ok=True)

    # Extract from items
    print("\n[1/3] Extracting conditions from items...")
    items_path = cleaned_dir / "items_extracted.json"
    with open(items_path) as f:
        items = json.load(f)

    print(f"  Loaded {len(items)} items")
    item_conditions = extract_item_conditions(items)
    print(f"  Found {len(item_conditions)} condition references")

    # Show sample
    if item_conditions:
        print("\n  Sample extractions:")
        for cond in item_conditions[:3]:
            print(f"    - {cond['item_name']}: {cond['condition']}")
            if cond['save_dc']:
                print(f"      DC {cond['save_dc']}{' ' + cond['save_ability'] if cond['save_ability'] else ''}")
            print(f"      Inflicts: {cond['inflicts']}")

    # Extract from monsters
    print("\n[2/3] Extracting conditions from monsters...")
    monsters_path = cleaned_dir / "monsters_extracted.json"
    with open(monsters_path) as f:
        monsters = json.load(f)

    print(f"  Loaded {len(monsters)} monsters")
    monster_conditions = extract_monster_conditions(monsters)
    print(f"  Found {len(monster_conditions)} condition references")

    # Show sample
    if monster_conditions:
        print("\n  Sample extractions:")
        for cond in monster_conditions[:3]:
            print(f"    - {cond['monster_name']} ({cond['context_name']}): {cond['condition']}")
            if cond['save_dc']:
                print(f"      DC {cond['save_dc']}{' ' + cond['save_ability'] if cond['save_ability'] else ''}")
            print(f"      Inflicts: {cond['inflicts']}")

    # Extract from spells
    print("\n[3/3] Extracting conditions from spells...")
    spells_path = cleaned_dir / "spells_extracted.json"
    with open(spells_path) as f:
        spells = json.load(f)

    print(f"  Loaded {len(spells)} spells")
    spell_conditions = extract_spell_conditions(spells)
    print(f"  Found {len(spell_conditions)} condition references")

    # Show sample
    if spell_conditions:
        print("\n  Sample extractions:")
        for cond in spell_conditions[:3]:
            print(f"    - {cond['spell_name']}: {cond['condition']}")
            if cond['save_dc']:
                print(f"      DC {cond['save_dc']}{' ' + cond['save_ability'] if cond['save_ability'] else ''}")
            print(f"      Inflicts: {cond['inflicts']}")

    # Combine and save
    output_data = {
        'items': item_conditions,
        'monsters': monster_conditions,
        'spells': spell_conditions
    }

    output_path = output_dir / "conditions_extracted.json"
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n  ✓ Saved to {output_path}")

    # Summary statistics
    print("\n" + "=" * 60)
    print("Summary Statistics")
    print("=" * 60)

    total = len(item_conditions) + len(monster_conditions) + len(spell_conditions)
    print(f"\nTotal condition references: {total}")
    print(f"  - Items: {len(item_conditions)}")
    print(f"  - Monsters: {len(monster_conditions)}")
    print(f"  - Spells: {len(spell_conditions)}")

    # Count unique conditions
    all_conditions = [c['condition'] for c in item_conditions + monster_conditions + spell_conditions]
    unique_conditions = set(all_conditions)
    print(f"\nUnique conditions: {len(unique_conditions)}")
    print("  ", ", ".join(sorted(unique_conditions)))

    # Count by inflicts vs immunity
    inflicts_count = sum(1 for c in item_conditions + monster_conditions + spell_conditions if c['inflicts'])
    immunity_count = total - inflicts_count
    print(f"\nInflicts condition: {inflicts_count}")
    print(f"Grants immunity/resistance: {immunity_count}")

    # Count with DC
    with_dc = sum(1 for c in item_conditions + monster_conditions + spell_conditions if c['save_dc'])
    print(f"\nWith save DC: {with_dc}")

    print("\n✓ Condition extraction complete!")


if __name__ == "__main__":
    main()
