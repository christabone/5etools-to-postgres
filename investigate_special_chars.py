"""
Investigate all special/non-alphabetic characters in cleaned data.

Find every non-standard character (excluding pipes which are already investigated).
"""

import json
import re
from pathlib import Path
from collections import Counter


def find_special_chars(text):
    """Extract all non-standard characters from text."""
    if not isinstance(text, str):
        return []

    # Match any character that is NOT:
    # - Letters (a-z, A-Z)
    # - Numbers (0-9)
    # - Common punctuation (. , ! ? ' " - space)
    # - Pipe (already investigated separately)
    standard_chars = re.compile(r'[a-zA-Z0-9.,!?\'" \-\n\t\r]')

    special_chars = []
    for char in text:
        if char == '|':  # Skip pipes, already investigated
            continue
        if not standard_chars.match(char):
            special_chars.append(char)

    return special_chars


def find_special_chars_recursive(obj, path=""):
    """Recursively find all special characters in data structure."""
    findings = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            new_path = f"{path}.{key}" if path else key
            findings.extend(find_special_chars_recursive(value, new_path))

    elif isinstance(obj, list):
        for item in obj:
            findings.extend(find_special_chars_recursive(item, f"{path}[]"))

    elif isinstance(obj, str):
        special = find_special_chars(obj)
        if special:
            for char in special:
                findings.append({
                    "path": path,
                    "char": char,
                    "code": ord(char),
                    "name": repr(char),
                    "context": obj[:100]  # First 100 chars for context
                })

    return findings


def main():
    """Investigate special characters in all cleaned data."""

    print("=" * 70)
    print("SPECIAL CHARACTER INVESTIGATION")
    print("=" * 70)
    print("\nSearching for non-standard characters:")
    print("  Excluding: a-z, A-Z, 0-9, . , ! ? ' \" - space newline tab")
    print("  Excluding: | (pipe - already investigated)")
    print()

    data_files = [
        ('items', Path('cleaned_data/items.json')),
        ('monsters', Path('cleaned_data/monsters.json')),
        ('spells', Path('cleaned_data/spells.json'))
    ]

    all_char_counts = Counter()
    all_findings = {}

    for name, filepath in data_files:
        print(f"\n{'=' * 70}")
        print(f"Analyzing {name.upper()}")
        print("=" * 70)

        with open(filepath, 'r') as f:
            data = json.load(f)

        print(f"Total records: {len(data)}")

        # Find all special characters
        findings = []
        for record in data:
            findings.extend(find_special_chars_recursive(record))

        if not findings:
            print("✅ No special characters found!")
            continue

        print(f"⚠️  Found {len(findings)} special character occurrences")

        # Count unique characters
        char_counts = Counter(f['char'] for f in findings)
        all_char_counts.update(char_counts)

        # Show top characters
        print(f"\n📊 Top special characters ({len(char_counts)} unique):")
        for char, count in char_counts.most_common(20):
            # Show character, unicode code point, and name
            code = ord(char)
            print(f"  '{char}' (U+{code:04X}, ord={code:3d}): {count:5d} occurrences")

        # Group by path
        by_path = {}
        for finding in findings:
            path = finding['path']
            char = finding['char']
            if path not in by_path:
                by_path[path] = Counter()
            by_path[path][char] += 1

        # Show top paths with special chars
        print(f"\n📍 Top fields with special characters:")
        sorted_paths = sorted(by_path.items(),
                            key=lambda x: sum(x[1].values()),
                            reverse=True)[:10]

        for path, chars in sorted_paths:
            total = sum(chars.values())
            print(f"\n  {path}: {total} occurrences")
            for char, count in chars.most_common(5):
                print(f"    '{char}' (U+{ord(char):04X}): {count}")

        # Show some examples
        print(f"\n📝 Example contexts:")
        shown_chars = set()
        for finding in findings[:20]:
            char = finding['char']
            if char not in shown_chars:
                shown_chars.add(char)
                context = finding['context'].replace('\n', '\\n')[:80]
                print(f"\n  '{char}' (U+{ord(char):04X}) in {finding['path']}:")
                print(f"    {context}...")
                if len(shown_chars) >= 10:
                    break

        all_findings[name] = findings

    # Overall summary
    print("\n" + "=" * 70)
    print("OVERALL SUMMARY")
    print("=" * 70)

    print(f"\nTotal special characters found: {len(all_char_counts)}")
    print(f"Total occurrences: {sum(all_char_counts.values())}")

    print(f"\n🔝 Top 30 special characters across ALL datasets:")
    for i, (char, count) in enumerate(all_char_counts.most_common(30), 1):
        code = ord(char)
        hex_code = f"U+{code:04X}"

        # Try to identify common ones
        name = ""
        if char == '—':
            name = "EM DASH"
        elif char == '–':
            name = "EN DASH"
        elif char == ''':
            name = "RIGHT SINGLE QUOTE"
        elif char == ''':
            name = "LEFT SINGLE QUOTE"
        elif char == '"':
            name = "LEFT DOUBLE QUOTE"
        elif char == '"':
            name = "RIGHT DOUBLE QUOTE"
        elif char == '…':
            name = "ELLIPSIS"
        elif char == '×':
            name = "MULTIPLICATION SIGN"
        elif char == '−':
            name = "MINUS SIGN"
        elif char == '÷':
            name = "DIVISION SIGN"
        elif char == '•':
            name = "BULLET"
        elif char == '©':
            name = "COPYRIGHT"
        elif char == '®':
            name = "REGISTERED"
        elif char == '™':
            name = "TRADEMARK"
        elif char == '\u2003':
            name = "EM SPACE"
        elif char == '\u00a0':
            name = "NON-BREAKING SPACE"
        elif code >= 0x2000 and code <= 0x200F:
            name = "UNICODE SPACE/FORMATTING"

        print(f"  {i:2d}. '{char}' ({hex_code}, {code:4d}) {name:30s}: {count:6d}")

    # Analysis
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    print("""
Common categories of special characters found:

1. **Typography** (em dash, en dash, smart quotes, ellipsis)
   - Used in descriptive text (entries, lore, etc.)
   - These are fine to keep in JSONB text fields
   - Should be preserved for display purposes

2. **Math symbols** (×, −, ÷, ±)
   - Used in formulas, calculations
   - Important for accuracy, keep as-is

3. **Special spaces** (non-breaking, em space, etc.)
   - May cause issues with searching/comparison
   - Consider normalizing to regular spaces?

4. **Unicode symbols** (bullets, arrows, etc.)
   - Used for formatting in text
   - Keep in JSONB

5. **Accented characters** (é, ñ, etc.)
   - Used in names (proper nouns)
   - Must preserve for accuracy

RECOMMENDATION:
- Keep all special chars in JSONB text fields (entries, descriptions)
- Only normalize special chars in KEY FIELDS used for:
  * Searching/filtering (names, types, etc.)
  * Foreign key lookups
  * Comparison operations
    """)

    # Check if special chars appear in key fields
    print("\n" + "=" * 70)
    print("SPECIAL CHARS IN KEY FIELDS")
    print("=" * 70)

    key_fields = ['name', 'type', 'source', 'school', 'size', 'rarity']

    for name, findings in all_findings.items():
        print(f"\n{name.upper()}:")
        key_field_chars = {}

        for finding in findings:
            path = finding['path']
            # Check if path is or ends with a key field
            for kf in key_fields:
                if path == kf or path.endswith(f'.{kf}'):
                    if kf not in key_field_chars:
                        key_field_chars[kf] = Counter()
                    key_field_chars[kf][finding['char']] += 1

        if key_field_chars:
            for field, chars in key_field_chars.items():
                print(f"  {field}: {sum(chars.values())} special chars")
                for char, count in chars.most_common(5):
                    print(f"    '{char}' (U+{ord(char):04X}): {count}")
        else:
            print("  ✅ No special chars in key fields")


if __name__ == '__main__':
    main()
