"""
Investigate all abbreviations in cleaned data.

Identify fields that use abbreviations and understand what they represent.
"""

import json
from pathlib import Path
from collections import Counter


def main():
    """Investigate abbreviations across all datasets."""

    print("=" * 70)
    print("ABBREVIATION INVESTIGATION")
    print("=" * 70)

    # Items
    print("\n" + "=" * 70)
    print("ITEMS")
    print("=" * 70)

    with open('cleaned_data/items.json', 'r') as f:
        items = json.load(f)

    print(f"Total items: {len(items)}")

    # Item type codes
    types = Counter(item.get('type') for item in items if item.get('type'))
    print(f"\n📋 Item Type Codes ({len(types)} unique):")
    for code, count in sorted(types.items(), key=lambda x: -x[1])[:20]:
        print(f"  {code:15} → {count:4} items")

    # Rarity
    rarities = Counter(item.get('rarity') for item in items if item.get('rarity'))
    print(f"\n💎 Rarities ({len(rarities)} unique):")
    for rarity, count in sorted(rarities.items(), key=lambda x: -x[1]):
        print(f"  {rarity:20} → {count:4} items")

    # Properties
    all_props = []
    for item in items:
        props = item.get('property', [])
        if props:
            all_props.extend(props)

    prop_counts = Counter(all_props)
    print(f"\n🔧 Item Properties ({len(prop_counts)} unique):")
    for prop, count in sorted(prop_counts.items(), key=lambda x: -x[1])[:25]:
        print(f"  {prop:15} → {count:4} items")

    # Source codes
    sources = Counter(item.get('source') for item in items if item.get('source'))
    print(f"\n📚 Sources ({len(sources)} unique):")
    for source, count in sorted(sources.items(), key=lambda x: -x[1])[:20]:
        print(f"  {source:10} → {count:4} items")

    # Monsters
    print("\n" + "=" * 70)
    print("MONSTERS")
    print("=" * 70)

    with open('cleaned_data/monsters.json', 'r') as f:
        monsters = json.load(f)

    print(f"Total monsters: {len(monsters)}")

    # Creature types (should be full names now)
    types = Counter(m.get('type', {}).get('type') for m in monsters)
    print(f"\n🐉 Creature Types ({len(types)} unique):")
    for ctype, count in sorted(types.items(), key=lambda x: -x[1])[:20]:
        print(f"  {ctype:15} → {count:4} monsters")

    # Size codes
    sizes = Counter(m.get('size') for m in monsters if m.get('size'))
    print(f"\n📏 Size Codes ({len(sizes)} unique):")
    for size, count in sorted(sizes.items(), key=lambda x: -x[1]):
        print(f"  {size:3} → {count:4} monsters")

    # Alignment codes
    all_alignments = []
    for monster in monsters:
        aligns = monster.get('alignment', [])
        if aligns:
            all_alignments.extend(aligns)

    align_counts = Counter(all_alignments)
    print(f"\n⚖️  Alignment Codes ({len(align_counts)} unique):")
    for align, count in sorted(align_counts.items(), key=lambda x: -x[1]):
        print(f"  {align:5} → {count:4} monsters")

    # Sources
    sources = Counter(m.get('source') for m in monsters if m.get('source'))
    print(f"\n📚 Sources ({len(sources)} unique):")
    for source, count in sorted(sources.items(), key=lambda x: -x[1])[:20]:
        print(f"  {source:10} → {count:4} monsters")

    # Spells
    print("\n" + "=" * 70)
    print("SPELLS")
    print("=" * 70)

    with open('cleaned_data/spells.json', 'r') as f:
        spells = json.load(f)

    print(f"Total spells: {len(spells)}")

    # School codes
    schools = Counter(s.get('school') for s in spells if s.get('school'))
    print(f"\n🎓 School Codes ({len(schools)} unique):")
    for school, count in sorted(schools.items(), key=lambda x: -x[1]):
        print(f"  {school:3} → {count:4} spells")

    # Sources
    sources = Counter(s.get('source') for s in spells if s.get('source'))
    print(f"\n📚 Sources ({len(sources)} unique):")
    for source, count in sorted(sources.items(), key=lambda x: -x[1])[:20]:
        print(f"  {source:10} → {count:4} spells")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY: FIELDS USING ABBREVIATIONS")
    print("=" * 70)
    print("""
ITEMS:
  - type: Codes like M, R, A, LA, MA, $G, etc. (NEEDS MAPPING)
  - rarity: Full names (common, uncommon, rare, etc.) ✅
  - property: Codes like V, 2H, F, L, T, etc. (NEEDS MAPPING)
  - source: Codes like PHB, MM, DMG, XGE, etc. (NEEDS MAPPING)

MONSTERS:
  - type.type: Full names (humanoid, beast, etc.) ✅
  - size: Single letter codes T, S, M, L, H, G (NEEDS MAPPING)
  - alignment: Letter codes L, N, C, G, E, U, A (NEEDS MAPPING)
  - source: Codes like MM, MPMM, XPHB, etc. (NEEDS MAPPING)

SPELLS:
  - school: Single letter codes A, C, D, E, I, N, T, V (NEEDS MAPPING)
  - source: Codes like PHB, XGE, XPHB, etc. (NEEDS MAPPING)

COMMON PATTERN:
  - source: Always abbreviated across all datasets
  - Some fields use codes (size, school, alignment, item type/properties)
  - Some fields use full names (rarity, creature type)

QUESTION: Should we create lookup tables with both code + full name?
    """)


if __name__ == '__main__':
    main()
