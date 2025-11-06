"""
Extract controlled vocabulary (enum values) from 5etools JSON.

Identifies fields with limited value sets that should become lookup tables.
"""

import json
from pathlib import Path
from collections import Counter, defaultdict
from typing import Any


DATA_DIR = Path('/home/ctabone/dnd_bot/5etools-src-2.15.0/data')
OUTPUT_FILE = Path('analysis/controlled_vocab.json')


class VocabAnalyzer:
    """Extracts controlled vocabulary from JSON."""

    def __init__(self):
        self.field_values = defaultdict(Counter)
        self.field_total_count = defaultdict(int)

    def extract_values(self, value: Any, path: str):
        """Extract values for vocabulary analysis."""
        self.field_total_count[path] += 1

        # Only track simple scalar values and small strings
        if isinstance(value, str):
            # Track if it looks like a controlled value (short, alphanumeric)
            if len(value) < 50 and not any(char in value for char in ['\n', '  ']):
                self.field_values[path][value] += 1

        elif isinstance(value, (int, float, bool)) and not isinstance(value, bool):
            # Track numbers that might be enums
            if isinstance(value, int) and -10 < value < 100:
                self.field_values[path][value] += 1

        elif isinstance(value, bool):
            self.field_values[path][value] += 1

        # Recurse
        if isinstance(value, dict):
            for key, val in value.items():
                new_path = f"{path}.{key}" if path else key
                self.extract_values(val, new_path)

        elif isinstance(value, list):
            for item in value:
                new_path = f"{path}[]"
                self.extract_values(item, new_path)

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
                        self.extract_values(item, root_key)
            else:
                self.extract_values(data, filepath.stem)

        except Exception as e:
            print(f"    ❌ Error: {e}")

    def identify_controlled_vocab(self, max_unique_values=100):
        """Identify fields that are likely controlled vocabularies."""
        vocab_fields = {}

        for path, value_counts in self.field_values.items():
            unique_count = len(value_counts)
            total_count = self.field_total_count[path]

            # Heuristics for controlled vocab:
            # 1. Has limited unique values (< max_unique_values)
            # 2. Values are reused (total_count > unique_count * 2)
            # 3. Or has very few values (< 20)

            if unique_count <= max_unique_values:
                if total_count > unique_count * 2 or unique_count < 20:
                    vocab_fields[path] = {
                        'unique_count': unique_count,
                        'total_count': total_count,
                        'reuse_ratio': round(total_count / unique_count, 2),
                        'values': dict(value_counts.most_common(100)),
                        'is_likely_enum': unique_count < 20
                    }

        return vocab_fields

    def to_dict(self) -> dict:
        """Convert to serializable dict."""
        vocab = self.identify_controlled_vocab()

        return {
            'summary': {
                'total_fields_analyzed': len(self.field_values),
                'controlled_vocab_fields': len(vocab),
                'high_confidence_enums': sum(1 for v in vocab.values() if v['is_likely_enum'])
            },
            'fields': vocab
        }


def main():
    """Main execution."""
    print("=" * 60)
    print("5etools Controlled Vocabulary Analysis")
    print("=" * 60)

    analyzer = VocabAnalyzer()

    # Analyze items
    print("\n📦 Analyzing Items...")
    items_base = DATA_DIR / 'items-base.json'
    if items_base.exists():
        analyzer.analyze_file(items_base, 'baseitem')

    items = DATA_DIR / 'items.json'
    if items.exists():
        analyzer.analyze_file(items, 'item')

    # Analyze monsters
    print("\n🐉 Analyzing Monsters...")
    bestiary_dir = DATA_DIR / 'bestiary'
    if bestiary_dir.exists():
        for json_file in sorted(bestiary_dir.glob('*.json')):
            analyzer.analyze_file(json_file, 'monster')

    # Analyze spells
    print("\n✨ Analyzing Spells...")
    spells_dir = DATA_DIR / 'spells'
    if spells_dir.exists():
        for json_file in sorted(spells_dir.glob('*.json')):
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
    print("🎯 High Confidence Controlled Vocabularies")
    print("=" * 60)

    enums = {k: v for k, v in report['fields'].items() if v['is_likely_enum']}
    for path, info in sorted(enums.items(), key=lambda x: x[1]['unique_count'])[:30]:
        values_preview = list(info['values'].keys())[:10]
        print(f"\n  {path}")
        print(f"    Unique values: {info['unique_count']}, Total occurrences: {info['total_count']}")
        print(f"    Values: {values_preview}")

    print(f"\n📊 Total controlled vocab fields: {report['summary']['controlled_vocab_fields']}")
    print(f"📊 High confidence enums: {report['summary']['high_confidence_enums']}")


if __name__ == '__main__':
    main()
