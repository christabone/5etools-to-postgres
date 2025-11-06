#!/usr/bin/env python3
"""
Normalize item type codes that have $ prefix.

Phase 0.6: Markup Extraction & Advanced Normalization

This script:
1. Identifies items with $ prefix in type codes ($G, $A, $C, etc.)
2. Extracts the $ flag to a separate field (is_generic_variant)
3. Removes the $ prefix from the type code

Type code meanings:
- $G = Generic variant
- $A = Alternate version
- $C = Custom/crafted

Input: cleaned_data/items_extracted.json
Output: Modifies file in place
"""

import json
from typing import Dict, Any
from pathlib import Path


def normalize_type_code(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize type code with $ prefix.

    Examples:
        type="$G" -> type="G", is_generic_variant=True
        type="$A" -> type="A", is_generic_variant=True
        type="M" -> type="M", is_generic_variant=False
    """
    type_code = item.get("type", "")

    if not type_code:
        item["is_generic_variant"] = False
        return item

    if type_code.startswith("$"):
        item["is_generic_variant"] = True
        item["type"] = type_code[1:]  # Remove $ prefix
    else:
        item["is_generic_variant"] = False

    return item


def main():
    """Main normalization process."""
    print("=" * 60)
    print("Phase 0.6: Type Code Normalization")
    print("=" * 60)

    base_dir = Path(__file__).parent
    cleaned_dir = base_dir / "cleaned_data"

    # Process items
    print("\n[1/1] Normalizing item type codes...")
    items_path = cleaned_dir / "items_extracted.json"
    with open(items_path) as f:
        items = json.load(f)

    print(f"  Loaded {len(items)} items")

    # Count items with $ prefix before
    dollar_items_before = [i for i in items if i.get("type", "").startswith("$")]
    print(f"\n  Items with $ prefix before: {len(dollar_items_before)}")

    # Show examples before
    print("\n  Sample BEFORE:")
    for item in dollar_items_before[:5]:
        print(f"    {item['name']}: type={item.get('type')}")

    # Normalize
    normalized_count = 0
    for item in items:
        type_before = item.get("type", "")
        item = normalize_type_code(item)
        type_after = item.get("type", "")

        if type_before != type_after:
            normalized_count += 1

    # Show examples after
    print("\n  Sample AFTER:")
    generic_items = [i for i in items if i.get("is_generic_variant")][:5]
    for item in generic_items:
        print(f"    {item['name']}: type={item.get('type')}, is_generic_variant={item.get('is_generic_variant')}")

    print(f"\n  ✓ Normalized {normalized_count} type codes")

    # Validate
    print("\n  Validating...")
    items_with_dollar = [i for i in items if i.get("type", "").startswith("$")]
    if items_with_dollar:
        print(f"  ❌ Still have {len(items_with_dollar)} items with $ prefix:")
        for item in items_with_dollar[:5]:
            print(f"    - {item['name']}: {item.get('type')}")
    else:
        print("  ✓ No items have $ prefix in type code")

    # Verify is_generic_variant was added to all items
    items_without_flag = [i for i in items if "is_generic_variant" not in i]
    if items_without_flag:
        print(f"  ❌ {len(items_without_flag)} items missing is_generic_variant flag")
    else:
        print("  ✓ All items have is_generic_variant flag")

    # Save
    with open(items_path, 'w') as f:
        json.dump(items, f, indent=2)
    print(f"\n  ✓ Saved to {items_path}")

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    generic_items = [i for i in items if i.get("is_generic_variant")]
    print(f"\nGeneric variant items: {len(generic_items)}")

    # Count by type
    type_counts = {}
    for item in generic_items:
        type_code = item.get("type", "unknown")
        type_counts[type_code] = type_counts.get(type_code, 0) + 1

    print("\nGeneric variants by type:")
    for type_code, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  - {type_code}: {count}")

    print("\n✓ Type code normalization complete!")


if __name__ == "__main__":
    main()
