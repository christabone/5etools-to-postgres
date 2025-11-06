"""
Validate cleaned data to ensure no polymorphic fields remain.
"""

import json
from pathlib import Path
from collections import defaultdict, Counter


CLEANED_DIR = Path('cleaned_data')


def check_type_consistency(data: list, name: str) -> dict:
    """Check that all fields have consistent types."""
    field_types = defaultdict(Counter)
    polymorphic_fields = []

    for record in data:
        check_record_types(record, "", field_types)

    # Find polymorphic fields
    for field, type_counts in field_types.items():
        if len(type_counts) > 1:
            polymorphic_fields.append({
                "field": field,
                "types": dict(type_counts)
            })

    return {
        "dataset": name,
        "total_records": len(data),
        "unique_fields": len(field_types),
        "polymorphic_fields": polymorphic_fields,
        "is_valid": len(polymorphic_fields) == 0
    }


def check_record_types(obj, path, field_types):
    """Recursively check types in a record."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            new_path = f"{path}.{key}" if path else key
            type_name = type(value).__name__
            field_types[new_path][type_name] += 1

            if isinstance(value, (dict, list)):
                check_record_types(value, new_path, field_types)

    elif isinstance(obj, list) and obj:
        # Check list element types
        new_path = f"{path}[]"
        for item in obj[:10]:  # Sample first 10
            type_name = type(item).__name__
            field_types[new_path][type_name] += 1


def validate_required_fields(data: list, name: str, required_fields: list) -> dict:
    """Check that required fields are present."""
    missing_counts = Counter()

    for record in data:
        for field in required_fields:
            if field not in record or record[field] is None:
                missing_counts[field] += 1

    return {
        "dataset": name,
        "required_fields": required_fields,
        "missing_fields": dict(missing_counts),
        "is_valid": len(missing_counts) == 0
    }


def main():
    """Main validation."""
    print("=" * 60)
    print("Cleaned Data Validation")
    print("=" * 60)

    validation_results = {
        "summary": {},
        "type_consistency": {},
        "required_fields": {}
    }

    # Validate items
    items_file = CLEANED_DIR / 'items.json'
    if items_file.exists():
        print("\n📦 Validating items...")
        with open(items_file, 'r') as f:
            items = json.load(f)

        type_check = check_type_consistency(items, "items")
        validation_results["type_consistency"]["items"] = type_check

        print(f"  Records: {type_check['total_records']}")
        print(f"  Unique fields: {type_check['unique_fields']}")
        print(f"  Polymorphic fields: {len(type_check['polymorphic_fields'])}")

        if type_check['polymorphic_fields']:
            print("  ⚠️  Polymorphic fields found:")
            for pf in type_check['polymorphic_fields'][:5]:
                print(f"    - {pf['field']}: {pf['types']}")

    # Validate monsters
    monsters_file = CLEANED_DIR / 'monsters.json'
    if monsters_file.exists():
        print("\n🐉 Validating monsters...")
        with open(monsters_file, 'r') as f:
            monsters = json.load(f)

        type_check = check_type_consistency(monsters, "monsters")
        validation_results["type_consistency"]["monsters"] = type_check

        print(f"  Records: {type_check['total_records']}")
        print(f"  Unique fields: {type_check['unique_fields']}")
        print(f"  Polymorphic fields: {len(type_check['polymorphic_fields'])}")

        if type_check['polymorphic_fields']:
            print("  ⚠️  Polymorphic fields found:")
            for pf in type_check['polymorphic_fields'][:5]:
                print(f"    - {pf['field']}: {pf['types']}")

    # Validate spells
    spells_file = CLEANED_DIR / 'spells.json'
    if spells_file.exists():
        print("\n✨ Validating spells...")
        with open(spells_file, 'r') as f:
            spells = json.load(f)

        type_check = check_type_consistency(spells, "spells")
        validation_results["type_consistency"]["spells"] = type_check

        print(f"  Records: {type_check['total_records']}")
        print(f"  Unique fields: {type_check['unique_fields']}")
        print(f"  Polymorphic fields: {len(type_check['polymorphic_fields'])}")

        if type_check['polymorphic_fields']:
            print("  ⚠️  Polymorphic fields found:")
            for pf in type_check['polymorphic_fields'][:5]:
                print(f"    - {pf['field']}: {pf['types']}")

    # Calculate overall validation
    all_valid = all(
        result.get('is_valid', False)
        for result in validation_results["type_consistency"].values()
    )

    validation_results["summary"] = {
        "all_valid": all_valid,
        "datasets_validated": len(validation_results["type_consistency"])
    }

    # Save validation report
    report_file = CLEANED_DIR / 'VALIDATION_REPORT.json'
    with open(report_file, 'w') as f:
        json.dump(validation_results, f, indent=2)

    # Create markdown report
    md_report = CLEANED_DIR / 'VALIDATION_REPORT.md'
    with open(md_report, 'w') as f:
        f.write("# Cleaned Data Validation Report\n\n")
        f.write(f"**Overall Status**: {'✅ PASS' if all_valid else '❌ FAIL'}\n\n")

        for dataset, results in validation_results["type_consistency"].items():
            f.write(f"## {dataset.capitalize()}\n\n")
            f.write(f"- Records: {results['total_records']}\n")
            f.write(f"- Unique fields: {results['unique_fields']}\n")
            f.write(f"- Polymorphic fields: {len(results['polymorphic_fields'])}\n")
            f.write(f"- Status: {'✅ PASS' if results['is_valid'] else '❌ FAIL'}\n\n")

            if results['polymorphic_fields']:
                f.write("### Polymorphic Fields\n\n")
                for pf in results['polymorphic_fields']:
                    f.write(f"- `{pf['field']}`: {pf['types']}\n")
                f.write("\n")

    print("\n" + "=" * 60)
    print(f"Validation {'✅ PASSED' if all_valid else '❌ FAILED'}")
    print("=" * 60)
    print(f"\n📊 Report saved to: {report_file}")
    print(f"📄 Markdown report: {md_report}")


if __name__ == '__main__':
    main()
