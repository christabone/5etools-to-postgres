"""
Extract representative sample records from 5etools JSON.

Saves examples of:
- Simple records
- Complex records
- Edge case records
"""

import json
from pathlib import Path


DATA_DIR = Path('/home/ctabone/dnd_bot/5etools-src-2.15.0/data')
OUTPUT_DIR = Path('analysis/samples')


def calculate_complexity(obj):
    """Calculate complexity score for a record."""
    if not isinstance(obj, dict):
        return 0

    score = 0
    score += len(obj)  # Number of top-level fields
    score += sum(1 for v in obj.values() if isinstance(v, dict)) * 5  # Nested dicts
    score += sum(1 for v in obj.values() if isinstance(v, list)) * 3  # Arrays
    score += sum(len(v) for v in obj.values() if isinstance(v, list)) * 0.5  # Array elements

    return score


def extract_samples(items, category):
    """Extract simple, complex, and edge case samples."""
    if not items:
        return [], [], []

    # Calculate complexity for each item
    scored_items = [(item, calculate_complexity(item)) for item in items]
    scored_items.sort(key=lambda x: x[1])

    # Simple: bottom 10
    simple = [item for item, _ in scored_items[:10]]

    # Complex: top 10
    complex_items = [item for item, _ in scored_items[-10:]]

    # Edge cases: items with unusual characteristics
    edge_cases = []
    for item in items[:100]:  # Sample first 100
        if not isinstance(item, dict):
            continue

        # Edge case indicators
        has_null = any(v is None for v in item.values())
        has_empty_array = any(isinstance(v, list) and len(v) == 0 for v in item.values())
        has_nested_array = any(
            isinstance(v, list) and any(isinstance(x, list) for x in v)
            for v in item.values()
        )

        if has_null or has_empty_array or has_nested_array:
            edge_cases.append(item)
            if len(edge_cases) >= 10:
                break

    return simple, complex_items, edge_cases


def save_samples(samples, filename):
    """Save samples to JSON file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filepath = OUTPUT_DIR / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(samples, f, indent=2)

    print(f"  ✅ Saved {len(samples)} samples to {filename}")


def main():
    """Main execution."""
    print("=" * 60)
    print("5etools Sample Record Extraction")
    print("=" * 60)

    # Extract item samples
    print("\n📦 Extracting Item Samples...")
    items_base = DATA_DIR / 'items-base.json'
    if items_base.exists():
        with open(items_base, 'r', encoding='utf-8') as f:
            data = json.load(f)
            items = data.get('baseitem', [])

        simple, complex_items, edge = extract_samples(items, 'items')
        save_samples(simple, 'items_simple.json')
        save_samples(complex_items, 'items_complex.json')
        save_samples(edge, 'items_edge_cases.json')

    # Extract monster samples
    print("\n🐉 Extracting Monster Samples...")
    bestiary_dir = DATA_DIR / 'bestiary'
    if bestiary_dir.exists():
        all_monsters = []
        for json_file in sorted(bestiary_dir.glob('*.json'))[:5]:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_monsters.extend(data.get('monster', []))

        simple, complex_items, edge = extract_samples(all_monsters, 'monsters')
        save_samples(simple, 'monsters_simple.json')
        save_samples(complex_items, 'monsters_complex.json')
        save_samples(edge, 'monsters_edge_cases.json')

    # Extract spell samples
    print("\n✨ Extracting Spell Samples...")
    spells_dir = DATA_DIR / 'spells'
    if spells_dir.exists():
        all_spells = []
        for json_file in sorted(spells_dir.glob('*.json'))[:5]:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_spells.extend(data.get('spell', []))

        simple, complex_items, edge = extract_samples(all_spells, 'spells')
        save_samples(simple, 'spells_simple.json')
        save_samples(complex_items, 'spells_complex.json')
        save_samples(edge, 'spells_edge_cases.json')

    print("\n✅ All samples extracted to analysis/samples/")
    print("\n💡 Next step: Manually review samples to understand data patterns")


if __name__ == '__main__':
    main()
