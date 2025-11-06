"""
Deep inspection of 5etools JSON file structure.

This script recursively walks through JSON files to:
- Identify all unique keys/fields
- Track data types for each field
- Count occurrences
- Find optional vs required fields
- Detect nested structures
- Sample values
"""

import json
from pathlib import Path
from collections import defaultdict, Counter
from typing import Any, Dict, Set
import sys


DATA_DIR = Path('/home/ctabone/dnd_bot/5etools-src-2.15.0/data')
OUTPUT_FILE = Path('analysis/structure_report.json')


class StructureAnalyzer:
    """Analyzes JSON structure recursively."""

    def __init__(self):
        self.fields = defaultdict(lambda: {
            'count': 0,
            'types': Counter(),
            'paths': set(),
            'sample_values': [],
            'null_count': 0,
            'max_depth': 0
        })

    def analyze_value(self, value: Any, path: str, depth: int = 0):
        """Recursively analyze a value and its structure."""
        field_info = self.fields[path]
        field_info['count'] += 1
        field_info['paths'].add(path)
        field_info['max_depth'] = max(field_info['max_depth'], depth)

        if value is None:
            field_info['null_count'] += 1
            field_info['types']['null'] += 1
            return

        type_name = type(value).__name__
        field_info['types'][type_name] += 1

        # Store sample values (up to 10 unique)
        if len(field_info['sample_values']) < 10:
            if isinstance(value, (str, int, float, bool)):
                if value not in field_info['sample_values']:
                    field_info['sample_values'].append(value)
            elif isinstance(value, dict):
                # Store keys of dict as sample
                sample = f"dict({len(value)} keys: {list(value.keys())[:5]})"
                if sample not in field_info['sample_values']:
                    field_info['sample_values'].append(sample)
            elif isinstance(value, list):
                sample = f"list({len(value)} items)"
                if sample not in field_info['sample_values']:
                    field_info['sample_values'].append(sample)

        # Recurse into structures
        if isinstance(value, dict):
            for key, val in value.items():
                new_path = f"{path}.{key}" if path else key
                self.analyze_value(val, new_path, depth + 1)

        elif isinstance(value, list):
            for i, item in enumerate(value[:5]):  # Sample first 5 items
                new_path = f"{path}[]"
                self.analyze_value(item, new_path, depth + 1)

    def analyze_file(self, filepath: Path, root_key: str = None):
        """Analyze a single JSON file."""
        print(f"  Analyzing {filepath.name}...")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if root_key and root_key in data:
                items = data[root_key]
                if isinstance(items, list):
                    print(f"    Found {len(items)} items in '{root_key}'")
                    for item in items:
                        self.analyze_value(item, root_key, 0)
                else:
                    self.analyze_value(items, root_key, 0)
            else:
                # Analyze entire structure
                self.analyze_value(data, filepath.stem, 0)

        except Exception as e:
            print(f"    ❌ Error: {e}")

    def to_dict(self) -> Dict:
        """Convert analysis results to serializable dict."""
        result = {}
        for path, info in sorted(self.fields.items()):
            result[path] = {
                'count': info['count'],
                'types': dict(info['types']),
                'sample_values': info['sample_values'][:10],
                'null_count': info['null_count'],
                'max_depth': info['max_depth'],
                'optional': info['null_count'] > 0 or info['count'] < max(f['count'] for f in self.fields.values())
            }
        return result


def main():
    """Main execution."""
    print("=" * 60)
    print("5etools JSON Structure Analysis")
    print("=" * 60)

    analyzer = StructureAnalyzer()

    # Analyze items
    print("\n📦 Analyzing Items...")
    items_base = DATA_DIR / 'items-base.json'
    if items_base.exists():
        analyzer.analyze_file(items_base, 'baseitem')

    items = DATA_DIR / 'items.json'
    if items.exists():
        analyzer.analyze_file(items, 'item')

    # Analyze bestiary
    print("\n🐉 Analyzing Monsters...")
    bestiary_dir = DATA_DIR / 'bestiary'
    if bestiary_dir.exists():
        for json_file in sorted(bestiary_dir.glob('*.json'))[:5]:  # Sample first 5 files
            analyzer.analyze_file(json_file, 'monster')

    # Analyze spells
    print("\n✨ Analyzing Spells...")
    spells_dir = DATA_DIR / 'spells'
    if spells_dir.exists():
        for json_file in sorted(spells_dir.glob('*.json'))[:5]:  # Sample first 5 files
            analyzer.analyze_file(json_file, 'spell')

    # Generate report
    print("\n📊 Generating report...")
    report = {
        'summary': {
            'total_unique_fields': len(analyzer.fields),
            'files_analyzed': 'items-base.json, items.json, bestiary/*.json (5 files), spells/*.json (5 files)'
        },
        'fields': analyzer.to_dict()
    }

    # Save report
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"\n✅ Report saved to: {OUTPUT_FILE}")
    print(f"📈 Total unique field paths: {len(analyzer.fields)}")

    # Print top-level summary
    print("\n" + "=" * 60)
    print("Top-Level Fields Summary")
    print("=" * 60)

    top_level = {k: v for k, v in report['fields'].items() if '.' not in k and '[]' not in k}
    for path, info in sorted(top_level.items(), key=lambda x: x[1]['count'], reverse=True)[:20]:
        types_str = ', '.join(f"{t}({c})" for t, c in info['types'].items())
        optional_str = "optional" if info['optional'] else "required"
        print(f"  {path:30s} count={info['count']:5d} {optional_str:10s} types=[{types_str}]")


if __name__ == '__main__':
    main()
