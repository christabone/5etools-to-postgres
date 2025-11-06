#!/usr/bin/env python3
"""
Extract cross-references between entities (items, spells, creatures).

Phase 0.6: Markup Extraction & Advanced Normalization

This script:
1. Parses {@item name|source} tags to find item relationships
2. Parses {@spell name|source} tags to find spell references
3. Parses {@creature name|source} tags to find creature references
4. Builds structured relationship data for junction tables

Output: extraction_data/cross_refs_extracted.json

Format:
{
  "item_to_item": [
    {
      "from_item": "Arrow",
      "to_item": "Quiver",
      "relationship_type": "requires"
    }
  ],
  "spell_summons": [
    {
      "spell_name": "Animate Dead",
      "creature_name": "skeleton"
    }
  ],
  "monster_spells": [
    {
      "monster_name": "Lich",
      "spell_name": "fireball"
    }
  ]
}
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from collections import defaultdict


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


def extract_item_references(items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extract cross-references from items.

    Returns:
        - item_to_item: Items that reference other items
        - item_to_spell: Items that reference spells
        - item_to_creature: Items that reference creatures
    """
    item_to_item = []
    item_to_spell = []
    item_to_creature = []

    for item in items:
        item_name = item.get('name', 'Unknown')
        source = item.get('source', 'Unknown')

        if 'entries' not in item:
            continue

        texts = extract_from_entries(item['entries'])
        full_text = ' '.join(texts)

        # Find {@item} references
        item_refs = re.findall(r'\{@item ([^|}]+)(?:\|([^}]+))?\}', full_text)
        for ref_name, ref_source in item_refs:
            # Try to determine relationship type from context
            relationship_type = 'references'

            # Common relationship patterns
            if re.search(rf'{re.escape(ref_name)}.*(?:requires?|needs?|uses?)', full_text, re.IGNORECASE):
                relationship_type = 'requires'
            elif re.search(rf'(?:contains?|includes?|comes with).*{re.escape(ref_name)}', full_text, re.IGNORECASE):
                relationship_type = 'contains'

            item_to_item.append({
                'from_item': item_name,
                'from_source': source,
                'to_item': ref_name,
                'to_source': ref_source if ref_source else None,
                'relationship_type': relationship_type
            })

        # Find {@spell} references
        spell_refs = re.findall(r'\{@spell ([^|}]+)(?:\|([^}]+))?\}', full_text)
        for ref_name, ref_source in spell_refs:
            item_to_spell.append({
                'item_name': item_name,
                'item_source': source,
                'spell_name': ref_name,
                'spell_source': ref_source if ref_source else None
            })

        # Find {@creature} references
        creature_refs = re.findall(r'\{@creature ([^|}]+)(?:\|([^}]+))?\}', full_text)
        for ref_name, ref_source in creature_refs:
            item_to_creature.append({
                'item_name': item_name,
                'item_source': source,
                'creature_name': ref_name,
                'creature_source': ref_source if ref_source else None
            })

    return {
        'item_to_item': item_to_item,
        'item_to_spell': item_to_spell,
        'item_to_creature': item_to_creature
    }


def extract_monster_references(monsters: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extract cross-references from monsters.

    Returns:
        - monster_to_item: Monsters that use items
        - monster_to_spell: Monsters that can cast spells
        - monster_to_creature: Monsters that reference other creatures
    """
    monster_to_item = []
    monster_to_spell = []
    monster_to_creature = []

    for monster in monsters:
        monster_name = monster.get('name', 'Unknown')
        source = monster.get('source', 'Unknown')

        # Check all text fields
        all_text = str(monster)

        # Find {@item} references
        item_refs = re.findall(r'\{@item ([^|}]+)(?:\|([^}]+))?\}', all_text)
        for ref_name, ref_source in item_refs:
            monster_to_item.append({
                'monster_name': monster_name,
                'monster_source': source,
                'item_name': ref_name,
                'item_source': ref_source if ref_source else None
            })

        # Find {@spell} references (often in spellcasting traits)
        spell_refs = re.findall(r'\{@spell ([^|}]+)(?:\|([^}]+))?\}', all_text)
        for ref_name, ref_source in spell_refs:
            # Try to extract frequency/usage from context
            frequency = None

            # Look for patterns like "1/day", "at will", "3/day"
            context_match = re.search(
                rf'({ref_name}.*?(?:at will|\d+/day|recharge))',
                all_text,
                re.IGNORECASE
            )
            if context_match:
                context = context_match.group(1)
                freq_match = re.search(r'(\d+)/day|at will|recharge', context, re.IGNORECASE)
                if freq_match:
                    frequency = freq_match.group(0).lower()

            monster_to_spell.append({
                'monster_name': monster_name,
                'monster_source': source,
                'spell_name': ref_name,
                'spell_source': ref_source if ref_source else None,
                'frequency': frequency
            })

        # Find {@creature} references
        creature_refs = re.findall(r'\{@creature ([^|}]+)(?:\|([^}]+))?\}', all_text)
        for ref_name, ref_source in creature_refs:
            monster_to_creature.append({
                'monster_name': monster_name,
                'monster_source': source,
                'creature_name': ref_name,
                'creature_source': ref_source if ref_source else None
            })

    return {
        'monster_to_item': monster_to_item,
        'monster_to_spell': monster_to_spell,
        'monster_to_creature': monster_to_creature
    }


def extract_spell_references(spells: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extract cross-references from spells.

    Returns:
        - spell_to_item: Spells that mention items (components, etc.)
        - spell_to_spell: Spells that reference other spells
        - spell_summons: Spells that summon creatures
    """
    spell_to_item = []
    spell_to_spell = []
    spell_summons = []

    for spell in spells:
        spell_name = spell.get('name', 'Unknown')
        source = spell.get('source', 'Unknown')
        spell_level = spell.get('level', 0)

        if 'entries' not in spell:
            continue

        texts = extract_from_entries(spell['entries'])
        full_text = ' '.join(texts)

        # Find {@item} references
        item_refs = re.findall(r'\{@item ([^|}]+)(?:\|([^}]+))?\}', full_text)
        for ref_name, ref_source in item_refs:
            spell_to_item.append({
                'spell_name': spell_name,
                'spell_source': source,
                'spell_level': spell_level,
                'item_name': ref_name,
                'item_source': ref_source if ref_source else None
            })

        # Find {@spell} references
        spell_refs = re.findall(r'\{@spell ([^|}]+)(?:\|([^}]+))?\}', full_text)
        for ref_name, ref_source in spell_refs:
            # Don't include self-references
            if ref_name.lower() != spell_name.lower():
                spell_to_spell.append({
                    'from_spell': spell_name,
                    'from_source': source,
                    'to_spell': ref_name,
                    'to_source': ref_source if ref_source else None
                })

        # Find {@creature} references (summons)
        creature_refs = re.findall(r'\{@creature ([^|}]+)(?:\|([^}]+))?\}', full_text)
        for ref_name, ref_source in creature_refs:
            # Try to determine if it's a summon
            is_summon = False
            quantity = None

            # Look for summon keywords
            if re.search(r'summons?|conjures?|creates?|animates?', full_text, re.IGNORECASE):
                is_summon = True

                # Try to extract quantity
                qty_match = re.search(rf'(\d+)\s+{re.escape(ref_name)}', full_text, re.IGNORECASE)
                if qty_match:
                    quantity = int(qty_match.group(1))

            spell_summons.append({
                'spell_name': spell_name,
                'spell_source': source,
                'spell_level': spell_level,
                'creature_name': ref_name,
                'creature_source': ref_source if ref_source else None,
                'is_summon': is_summon,
                'quantity': quantity
            })

    return {
        'spell_to_item': spell_to_item,
        'spell_to_spell': spell_to_spell,
        'spell_summons': spell_summons
    }


def main():
    """Main extraction process."""
    print("=" * 60)
    print("Phase 0.6: Cross-Reference Extraction")
    print("=" * 60)

    base_dir = Path(__file__).parent
    cleaned_dir = base_dir / "cleaned_data"
    output_dir = base_dir / "extraction_data"
    output_dir.mkdir(exist_ok=True)

    # Extract from items
    print("\n[1/3] Extracting cross-references from items...")
    items_path = cleaned_dir / "items_extracted.json"
    with open(items_path) as f:
        items = json.load(f)

    print(f"  Loaded {len(items)} items")
    item_refs = extract_item_references(items)

    print(f"  Found {len(item_refs['item_to_item'])} item→item references")
    print(f"  Found {len(item_refs['item_to_spell'])} item→spell references")
    print(f"  Found {len(item_refs['item_to_creature'])} item→creature references")

    # Extract from monsters
    print("\n[2/3] Extracting cross-references from monsters...")
    monsters_path = cleaned_dir / "monsters_extracted.json"
    with open(monsters_path) as f:
        monsters = json.load(f)

    print(f"  Loaded {len(monsters)} monsters")
    monster_refs = extract_monster_references(monsters)

    print(f"  Found {len(monster_refs['monster_to_item'])} monster→item references")
    print(f"  Found {len(monster_refs['monster_to_spell'])} monster→spell references")
    print(f"  Found {len(monster_refs['monster_to_creature'])} monster→creature references")

    # Extract from spells
    print("\n[3/3] Extracting cross-references from spells...")
    spells_path = cleaned_dir / "spells_extracted.json"
    with open(spells_path) as f:
        spells = json.load(f)

    print(f"  Loaded {len(spells)} spells")
    spell_refs = extract_spell_references(spells)

    print(f"  Found {len(spell_refs['spell_to_item'])} spell→item references")
    print(f"  Found {len(spell_refs['spell_to_spell'])} spell→spell references")
    print(f"  Found {len(spell_refs['spell_summons'])} spell→creature references")

    # Show samples
    print("\n  Sample extractions:")
    if item_refs['item_to_item']:
        ref = item_refs['item_to_item'][0]
        print(f"    - {ref['from_item']} → {ref['to_item']} ({ref['relationship_type']})")

    if spell_refs['spell_summons']:
        ref = spell_refs['spell_summons'][0]
        print(f"    - {ref['spell_name']} summons {ref['creature_name']}")

    if monster_refs['monster_to_spell']:
        ref = monster_refs['monster_to_spell'][0]
        freq = f" ({ref['frequency']})" if ref.get('frequency') else ""
        print(f"    - {ref['monster_name']} casts {ref['spell_name']}{freq}")

    # Combine and save
    output_data = {
        **item_refs,
        **monster_refs,
        **spell_refs
    }

    output_path = output_dir / "cross_refs_extracted.json"
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n  ✓ Saved to {output_path}")

    # Summary statistics
    print("\n" + "=" * 60)
    print("Summary Statistics")
    print("=" * 60)

    total = sum(len(v) if isinstance(v, list) else 0 for v in output_data.values())
    print(f"\nTotal cross-references: {total}")
    print(f"\nBy type:")
    for key, value in output_data.items():
        if isinstance(value, list):
            print(f"  {key}: {len(value)}")

    # Summon spells
    summons = [s for s in spell_refs['spell_summons'] if s.get('is_summon')]
    print(f"\nSpells that summon creatures: {len(summons)}")

    print("\n✓ Cross-reference extraction complete!")


if __name__ == "__main__":
    main()
