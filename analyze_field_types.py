"""
Analyze data type variations in 5etools JSON.

Identifies polymorphic fields and type inconsistencies:
- Fields that can be multiple types
- Array element type variations
- Complex nested structures
- Edge cases
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Any, Dict


DATA_DIR = Path('/home/ctabone/dnd_bot/5etools-src-2.15.0/data')
OUTPUT_FILE = Path('analysis/field_types_report.json')


class TypeAnalyzer:
    """Analyzes field type variations."""

    def __init__(self):
        self.field_types = defaultdict(lambda: {
            'type_examples': defaultdict(list),
            'polymorphic': False,
            'array_element_types': set(),
            'total_count': 0
        })

    def analyze_value(self, value: Any, path: str):
        """Analyze type of a value."""
        field_info = self.field_types[path]
        field_info['total_count'] += 1

        type_name = type(value).__name__

        # Store example for this type (up to 3 examples per type)
        if len(field_info['type_examples'][type_name]) < 3:
            if isinstance(value, (str, int, float, bool, type(None))):
                field_info['type_examples'][type_name].append(value)
            elif isinstance(value, dict):
                field_info['type_examples'][type_name].append({
                    '__sample__': 'dict',
                    'keys': list(value.keys())[:10]
                })
            elif isinstance(value, list):
                field_info['type_examples'][type_name].append({
                    '__sample__': 'list',
                    'length': len(value),
                    'element_types': list(set(type(x).__name__ for x in value[:10]))
                })

        # Check for polymorphic fields
        if len(field_info['type_examples']) > 1:
            field_info['polymorphic'] = True

        # Analyze array element types
        if isinstance(value, list):
            for item in value[:20]:  # Sample first 20
                field_info['array_element_types'].add(type(item).__name__)

        # Recurse
        if isinstance(value, dict):
            for key, val in value.items():
                new_path = f"{path}.{key}" if path else key
                self.analyze_value(val, new_path)
        elif isinstance(value, list):
            for item in value[:10]:  # Sample first 10
                new_path = f"{path}[]"
                self.analyze_value(item, new_path)

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
                        self.analyze_value(item, root_key)
            else:
                self.analyze_value(data, filepath.stem)

        except Exception as e:
            print(f"    ❌ Error: {e}")

    def to_dict(self) -> Dict:
        """Convert to serializable dict."""
        result = {}
        for path, info in sorted(self.field_types.items()):
            result[path] = {
                'total_count': info['total_count'],
                'type_examples': {
                    k: v for k, v in info['type_examples'].items()
                },
                'polymorphic': info['polymorphic'],
                'num_types': len(info['type_examples']),
                'array_element_types': list(info['array_element_types']) if info['array_element_types'] else None
            }
        return result


def main():
    """Main execution."""
    print("=" * 60)
    print("5etools Field Type Analysis")
    print("=" * 60)

    analyzer = TypeAnalyzer()

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
    report = {
        'summary': {
            'total_fields': len(analyzer.field_types),
            'polymorphic_fields': sum(1 for f in analyzer.field_types.values() if f['polymorphic'])
        },
        'fields': analyzer.to_dict()
    }

    # Save
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"\n✅ Report saved to: {OUTPUT_FILE}")

    # Print polymorphic fields
    print("\n" + "=" * 60)
    print("⚠️  Polymorphic Fields (Need Special Handling)")
    print("=" * 60)

    polymorphic = {k: v for k, v in analyzer.field_types.items() if v['polymorphic']}
    for path, info in sorted(polymorphic.items())[:30]:
        types = list(info['type_examples'].keys())
        print(f"  {path:40s} types={types}")

    print(f"\n📊 Total polymorphic fields: {len(polymorphic)}")


if __name__ == '__main__':
    main()
