"""
Master script to run all cleaning operations.
"""

import subprocess
import sys
import time
from pathlib import Path


def print_banner(text):
    """Print a nice banner."""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def run_script(script_name, description):
    """Run a Python script and track timing."""
    print_banner(description)
    start_time = time.time()

    try:
        result = subprocess.run(
            [sys.executable, script_name],
            check=True,
            capture_output=False,
            text=True
        )

        elapsed = time.time() - start_time
        print(f"\n✅ {description} completed in {elapsed:.1f}s")
        return True, elapsed

    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start_time
        print(f"\n❌ {description} failed after {elapsed:.1f}s!")
        return False, elapsed


def main():
    """Main execution."""
    print_banner("5etools Data Cleaning Pipeline")
    print("\nThis will clean all 5etools data:")
    print("  1. Items (base + magic)")
    print("  2. Monsters (all bestiary files)")
    print("  3. Spells (all spell files)")
    print("  4. Validation")

    # Track overall timing
    total_start = time.time()
    results = {}

    # Run cleaning scripts in order
    scripts = [
        ('clean_items.py', 'Item Data Cleaning'),
        ('clean_monsters.py', 'Monster Data Cleaning'),
        ('clean_spells.py', 'Spell Data Cleaning'),
        ('validate_cleaned.py', 'Data Validation'),
    ]

    for script, description in scripts:
        success, elapsed = run_script(script, description)
        results[description] = {
            "success": success,
            "time": elapsed
        }

        if not success:
            print(f"\n❌ Stopping pipeline due to failure in: {description}")
            break

    # Generate summary report
    total_elapsed = time.time() - total_start

    print_banner("Cleaning Pipeline Complete")

    print(f"\n⏱️  Total time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} minutes)")
    print(f"\n📊 Summary:")

    for desc, result in results.items():
        status = "✅" if result["success"] else "❌"
        print(f"  {status} {desc}: {result['time']:.1f}s")

    # Save report
    report_file = Path('cleaned_data/CLEANING_REPORT.md')
    with open(report_file, 'w') as f:
        f.write("# Data Cleaning Report\n\n")
        f.write(f"**Total Time**: {total_elapsed:.1f}s ({total_elapsed/60:.1f} minutes)\n\n")
        f.write("## Operations\n\n")

        for desc, result in results.items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            f.write(f"- **{desc}**: {status} ({result['time']:.1f}s)\n")

        f.write("\n## Files Generated\n\n")
        f.write("```\n")
        f.write("cleaned_data/\n")
        f.write("├── items.json\n")
        f.write("├── monsters.json\n")
        f.write("├── spells.json\n")
        f.write("├── VALIDATION_REPORT.json\n")
        f.write("├── VALIDATION_REPORT.md\n")
        f.write("└── CLEANING_REPORT.md\n")
        f.write("```\n")

    print(f"\n📄 Report saved to: {report_file}")

    # Check if all succeeded
    all_success = all(r["success"] for r in results.values())

    if all_success:
        print("\n🎉 All cleaning operations completed successfully!")
        print("\n✅ Ready for Phase 1: Schema Design")
    else:
        print("\n⚠️  Some operations failed. Please review errors above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
