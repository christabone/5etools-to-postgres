"""
Discover data relationships in 5etools JSON.

Identifies:
- Foreign key relationships (references to other entities)
- Many-to-many relationships
- Parent-child structures
- Cross-references between data types
"""

import json
from pathlib import Path
from collections import defaultdict


DATA_DIR = Path('/home/ctabone/dnd_bot/5etools-src-2.15.0/data')
OUTPUT_FILE = Path('analysis/relationships.json')


class RelationshipAnalyzer:
    """Analyzes relationships between data entities."""

    def __init__(self):
        self.potential_fks = defaultdict(set)
        self.array_relationships = defaultdict(lambda: {'types': set(), 'examples': []})
        self.reference_patterns = defaultdict(list)

    def analyze_potential_fk(self, value, path):
        """Identify potential foreign key fields."""
        # Common FK patterns
        fk_indicators = ['source', 'type', 'school', 'rarity', 'size', 'alignment']

        if isinstance(value, str):
            for indicator in fk_indicators:
                if indicator in path.lower():
                    self.potential_fks[path].add(value)

    def analyze_array_relationship(self, value, path):
        """Analyze array fields that might represent relationships."""
        if isinstance(value, list) and len(value) > 0:
            element_types = set(type(x).__name__ for x in value)
            self.array_relationships[path]['types'].update(element_types)

            # Store examples
            if len(self.array_relationships[path]['examples']) < 5:
                self.array_relationships[path]['examples'].append({
                    'length': len(value),
                    'sample': value[:3] if all(isinstance(x, (str, int)) for x in value[:3]) else 'complex'
                })

    def analyze_references(self, obj, parent_path=''):
        """Find cross-references between entities."""
        if isinstance(obj, dict):
            # Look for name/id pairs that might indicate references
            if 'name' in obj and 'source' in obj:
                self.reference_patterns[parent_path].append({
                    'type': 'named_entity',
                    'name': obj.get('name'),
                    'source': obj.get('source')
                })

            for key, value in obj.items():
                new_path = f"{parent_path}.{key}" if parent_path else key
                self.analyze_potential_fk(value, new_path)
                self.analyze_array_relationship(value, new_path)
                self.analyze_references(value, new_path)

        elif isinstance(obj, list):
            for item in obj[:10]:  # Sample first 10
                self.analyze_references(item, parent_path)

    def analyze_file(self, filepath: Path, root_key: str = None):
        """Analyze a single JSON file."""
        print(f"  Analyzing {filepath.name}...")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if root_key and root_key in data:
                items = data[root_key]
                if isinstance(items, list):
                    for item in items:
                        self.analyze_references(item, root_key)
            else:
                self.analyze_references(data, filepath.stem)

        except Exception as e:
            print(f"    ❌ Error: {e}")

    def to_dict(self) -> dict:
        """Convert to serializable dict."""
        return {
            'potential_foreign_keys': {
                path: {
                    'unique_values': list(values)[:50],
                    'count': len(values)
                }
                for path, values in self.potential_fks.items()
            },
            'array_relationships': {
                path: {
                    'element_types': list(info['types']),
                    'examples': info['examples']
                }
                for path, info in self.array_relationships.items()
                if len(info['examples']) > 0
            },
            'named_entities': {
                path: {
                    'count': len(refs),
                    'sample': refs[:5]
                }
                for path, refs in self.reference_patterns.items()
                if refs
            }
        }


def main():
    """Main execution."""
    print("=" * 60)
    print("5etools Relationship Analysis")
    print("=" * 60)

    analyzer = RelationshipAnalyzer()

    # Analyze items
    print("\n📦 Analyzing Items...")
    items_base = DATA_DIR / 'items-base.json'
    if items_base.exists():
        analyzer.analyze_file(items_base, 'baseitem')

    # Analyze monsters
    print("\n🐉 Analyzing Monsters...")
    bestiary_dir = DATA_DIR / 'bestiary'
    if bestiary_dir.exists():
        for json_file in sorted(bestiary_dir.glob('*.json'))[:5]:
            analyzer.analyze_file(json_file, 'monster')

    # Analyze spells
    print("\n✨ Analyzing Spells...")
    spells_dir = DATA_DIR / 'spells'
    if spells_dir.exists():
        for json_file in sorted(spells_dir.glob('*.json'))[:5]:
            analyzer.analyze_file(json_file, 'spell')

    # Generate report
    print("\n📊 Generating report...")
    report = analyzer.to_dict()

    # Save
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"\n✅ Report saved to: {OUTPUT_FILE}")

    # Print summary
    print("\n" + "=" * 60)
    print("🔗 Potential Foreign Key Fields")
    print("=" * 60)

    for path, info in sorted(report['potential_foreign_keys'].items())[:20]:
        print(f"\n  {path}")
        print(f"    Unique values ({info['count']}): {info['unique_values'][:10]}")

    print("\n" + "=" * 60)
    print("📋 Array Relationships (Many-to-Many)")
    print("=" * 60)

    for path, info in sorted(report['array_relationships'].items())[:20]:
        print(f"\n  {path}")
        print(f"    Element types: {info['element_types']}")
        if info['examples']:
            print(f"    Example: {info['examples'][0]}")


if __name__ == '__main__':
    main()
