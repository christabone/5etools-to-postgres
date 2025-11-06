"""
Investigate all pipe (|) usage in cleaned data.

Find every field that contains pipe characters and understand what they mean.
"""

import json
from pathlib import Path
from collections import defaultdict, Counter


def find_pipes_recursive(obj, path=""):
    """Recursively find all values containing pipes."""
    findings = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            new_path = f"{path}.{key}" if path else key
            findings.extend(find_pipes_recursive(value, new_path))

    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            findings.extend(find_pipes_recursive(item, f"{path}[]"))

    elif isinstance(obj, str) and '|' in obj:
        findings.append({
            "path": path,
            "value": obj,
            "before_pipe": obj.split('|')[0],
            "after_pipe": obj.split('|', 1)[1]
        })

    return findings


def main():
    """Investigate pipes in all cleaned data."""

    print("=" * 70)
    print("PIPE CHARACTER INVESTIGATION")
    print("=" * 70)

    data_files = [
        ('items', Path('cleaned_data/items.json')),
        ('monsters', Path('cleaned_data/monsters.json')),
        ('spells', Path('cleaned_data/spells.json'))
    ]

    all_findings = defaultdict(list)

    for name, filepath in data_files:
        print(f"\n{'=' * 70}")
        print(f"Analyzing {name.upper()}")
        print("=" * 70)

        with open(filepath, 'r') as f:
            data = json.load(f)

        print(f"Total records: {len(data)}")

        # Find all pipe occurrences
        findings = []
        for record in data:
            findings.extend(find_pipes_recursive(record))

        if not findings:
            print("✅ No pipes found!")
            continue

        print(f"⚠️  Found {len(findings)} values with pipes")
        print()

        # Group by path
        by_path = defaultdict(list)
        for finding in findings:
            by_path[finding['path']].append(finding)

        # Show summary by path
        for path, items in sorted(by_path.items()):
            print(f"\nPath: {path}")
            print(f"  Count: {len(items)}")

            # Count what comes after pipe
            after_pipe_counts = Counter(item['after_pipe'] for item in items)
            print(f"  After pipe patterns ({len(after_pipe_counts)}):")
            for pattern, count in sorted(after_pipe_counts.items(), key=lambda x: -x[1])[:10]:
                print(f"    {pattern}: {count}")

            # Show examples
            print(f"  Examples:")
            for item in items[:5]:
                print(f"    '{item['value']}'")

        all_findings[name] = findings

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for name, findings in all_findings.items():
        if findings:
            print(f"\n{name.upper()}: {len(findings)} values with pipes")

            # Most common "after pipe" values
            after_values = Counter(f['after_pipe'] for f in findings)
            print("  Top 'after pipe' values:")
            for val, count in after_values.most_common(10):
                print(f"    |{val}: {count}")

    # Analysis
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    print("""
The pipe character (|) in 5etools data appears to indicate:
  - Source book reference (e.g., "V|XPHB" = Versatile from XPHB)
  - Variant or alternative form
  - Namespace/module indicator

Questions to answer:
  1. Should we strip the pipe suffix? (Likely YES for properties, types)
  2. Should we preserve the source info? (Maybe in a separate field)
  3. Are there cases where the pipe means something else?
    """)


if __name__ == '__main__':
    main()
