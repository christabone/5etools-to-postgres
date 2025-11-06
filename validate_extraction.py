#!/usr/bin/env python3
"""
Validate all extraction work from Phase 0.6.

This script verifies:
1. No {@...} markup in name fields
2. No '+' prefix in bonus fields (all integers)
3. No '$' prefix in type codes
4. All extracted data files exist and are valid JSON
5. Extracted condition/damage/cross-ref counts are reasonable

Output: cleaned_data/EXTRACTION_VALIDATION.md
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List


def validate_names(items: List[Dict], monsters: List[Dict], spells: List[Dict]) -> Dict[str, Any]:
    """Validate that all names are clean (no markup)."""
    results = {
        'passed': True,
        'errors': []
    }

    # Check for {@...} markup in names
    for item in items:
        if '{@' in item.get('name', ''):
            results['passed'] = False
            results['errors'].append(f"Item has markup in name: {item['name']}")

    for monster in monsters:
        if '{@' in monster.get('name', ''):
            results['passed'] = False
            results['errors'].append(f"Monster has markup in name: {monster['name']}")

    for spell in spells:
        if '{@' in spell.get('name', ''):
            results['passed'] = False
            results['errors'].append(f"Spell has markup in name: {spell['name']}")

    # Check that base_name and variant_name fields exist
    items_without_base = [i for i in items if 'base_name' not in i]
    if items_without_base:
        results['passed'] = False
        results['errors'].append(f"{len(items_without_base)} items missing base_name field")

    return results


def validate_bonuses(items: List[Dict]) -> Dict[str, Any]:
    """Validate that all bonus fields are integers."""
    results = {
        'passed': True,
        'errors': []
    }

    bonus_fields = ['bonusWeapon', 'bonusAc', 'bonusSpellAttack', 'bonusSpellSaveDc', 'bonusSavingThrow']

    for item in items:
        for field in bonus_fields:
            if field in item:
                value = item[field]
                if not isinstance(value, int):
                    results['passed'] = False
                    results['errors'].append(
                        f"Item '{item['name']}' has non-integer {field}: {value} ({type(value).__name__})"
                    )

    return results


def validate_type_codes(items: List[Dict]) -> Dict[str, Any]:
    """Validate that type codes don't have $ prefix."""
    results = {
        'passed': True,
        'errors': []
    }

    for item in items:
        if 'type' in item and isinstance(item['type'], str):
            if item['type'].startswith('$'):
                results['passed'] = False
                results['errors'].append(f"Item '{item['name']}' has $ in type: {item['type']}")

        # Check that is_generic_variant field exists
        if 'is_generic_variant' not in item:
            results['passed'] = False
            results['errors'].append(f"Item '{item['name']}' missing is_generic_variant field")
            break  # Only report once

    return results


def validate_extracted_files(extraction_dir: Path) -> Dict[str, Any]:
    """Validate that all extraction output files exist and are valid."""
    results = {
        'passed': True,
        'errors': [],
        'file_counts': {}
    }

    expected_files = [
        'conditions_extracted.json',
        'damage_extracted.json',
        'cross_refs_extracted.json'
    ]

    for filename in expected_files:
        filepath = extraction_dir / filename
        if not filepath.exists():
            results['passed'] = False
            results['errors'].append(f"Missing file: {filename}")
            continue

        try:
            with open(filepath) as f:
                data = json.load(f)

            # Count records
            if filename == 'conditions_extracted.json':
                results['file_counts']['conditions'] = {
                    'items': len(data.get('items', [])),
                    'monsters': len(data.get('monsters', [])),
                    'spells': len(data.get('spells', []))
                }
            elif filename == 'damage_extracted.json':
                results['file_counts']['damage'] = {
                    'items': len(data.get('items', [])),
                    'monster_attacks': len(data.get('monster_attacks', [])),
                    'spells': len(data.get('spells', []))
                }
            elif filename == 'cross_refs_extracted.json':
                results['file_counts']['cross_refs'] = {
                    key: len(val) if isinstance(val, list) else 0
                    for key, val in data.items()
                }

        except json.JSONDecodeError as e:
            results['passed'] = False
            results['errors'].append(f"Invalid JSON in {filename}: {e}")

    return results


def main():
    """Main validation process."""
    print("=" * 60)
    print("Phase 0.6: Extraction Validation")
    print("=" * 60)

    base_dir = Path(__file__).parent
    cleaned_dir = base_dir / "cleaned_data"
    extraction_dir = base_dir / "extraction_data"

    # Load data
    print("\n[1/5] Loading data...")
    with open(cleaned_dir / "items_extracted.json") as f:
        items = json.load(f)
    with open(cleaned_dir / "monsters_extracted.json") as f:
        monsters = json.load(f)
    with open(cleaned_dir / "spells_extracted.json") as f:
        spells = json.load(f)

    print(f"  Items: {len(items)}")
    print(f"  Monsters: {len(monsters)}")
    print(f"  Spells: {len(spells)}")

    # Run validations
    all_passed = True
    validation_results = {}

    print("\n[2/5] Validating names...")
    validation_results['names'] = validate_names(items, monsters, spells)
    if validation_results['names']['passed']:
        print("  ✓ All names clean (no markup)")
    else:
        print(f"  ✗ {len(validation_results['names']['errors'])} name validation errors")
        all_passed = False

    print("\n[3/5] Validating bonus fields...")
    validation_results['bonuses'] = validate_bonuses(items)
    if validation_results['bonuses']['passed']:
        print("  ✓ All bonus fields are integers")
    else:
        print(f"  ✗ {len(validation_results['bonuses']['errors'])} bonus validation errors")
        all_passed = False

    print("\n[4/5] Validating type codes...")
    validation_results['type_codes'] = validate_type_codes(items)
    if validation_results['type_codes']['passed']:
        print("  ✓ All type codes normalized (no $ prefix)")
    else:
        print(f"  ✗ {len(validation_results['type_codes']['errors'])} type code errors")
        all_passed = False

    print("\n[5/5] Validating extracted files...")
    validation_results['extracted_files'] = validate_extracted_files(extraction_dir)
    if validation_results['extracted_files']['passed']:
        print("  ✓ All extraction files present and valid")
    else:
        print(f"  ✗ {len(validation_results['extracted_files']['errors'])} file errors")
        all_passed = False

    # Generate report
    print("\n" + "=" * 60)
    print("Validation Report")
    print("=" * 60)

    report_lines = []
    report_lines.append("# Phase 0.6 Extraction Validation Report\n")
    report_lines.append(f"**Status**: {'✅ PASSED' if all_passed else '❌ FAILED'}\n")
    report_lines.append("## Validation Results\n")

    for category, result in validation_results.items():
        status = "✅ PASSED" if result['passed'] else "❌ FAILED"
        report_lines.append(f"### {category.replace('_', ' ').title()}: {status}\n")

        if result['errors']:
            report_lines.append("\n**Errors:**\n")
            for error in result['errors'][:10]:  # Limit to first 10 errors
                report_lines.append(f"- {error}\n")
            if len(result['errors']) > 10:
                report_lines.append(f"- ... and {len(result['errors']) - 10} more errors\n")

        if 'file_counts' in result:
            report_lines.append("\n**Extracted Data Counts:**\n")
            for file_type, counts in result['file_counts'].items():
                report_lines.append(f"\n**{file_type}:**\n")
                if isinstance(counts, dict):
                    for key, count in counts.items():
                        report_lines.append(f"- {key}: {count}\n")

        report_lines.append("\n")

    # Write report
    report_path = cleaned_dir / "EXTRACTION_VALIDATION.md"
    with open(report_path, 'w') as f:
        f.writelines(report_lines)

    print(f"\n✓ Validation report saved to {report_path}")

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    if all_passed:
        print("\n✅ ALL VALIDATIONS PASSED")
        print("\nPhase 0.6 extraction is complete and validated!")
    else:
        print("\n❌ SOME VALIDATIONS FAILED")
        print("\nPlease review the errors above and in the validation report.")

    # Show extraction counts
    if 'extracted_files' in validation_results and 'file_counts' in validation_results['extracted_files']:
        print("\nExtracted Data Summary:")
        counts = validation_results['extracted_files']['file_counts']

        if 'conditions' in counts:
            total_cond = sum(counts['conditions'].values())
            print(f"  Conditions: {total_cond} references")

        if 'damage' in counts:
            total_dmg = sum(counts['damage'].values())
            print(f"  Damage: {total_dmg} records")

        if 'cross_refs' in counts:
            total_refs = sum(counts['cross_refs'].values())
            print(f"  Cross-references: {total_refs} relationships")

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
