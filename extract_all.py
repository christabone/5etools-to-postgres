#!/usr/bin/env python3
"""
Master script to run all Phase 0.6 extraction scripts in order.

This script orchestrates the complete extraction pipeline:
1. extract_names.py - Clean names and extract variants
2. normalize_bonuses.py - Convert bonus strings to integers
3. normalize_type_codes.py - Handle $ prefixes in type codes
4. extract_conditions.py - Extract condition references
5. extract_damage.py - Extract damage information
6. extract_cross_refs.py - Extract cross-references
7. validate_extraction.py - Verify all extraction work

Usage:
    python3 extract_all.py
"""

import subprocess
import sys
import time
from pathlib import Path


def run_script(script_name: str, description: str) -> bool:
    """
    Run a Python script and return success status.

    Args:
        script_name: Name of the script to run
        description: Human-readable description

    Returns:
        True if script succeeded, False otherwise
    """
    print(f"\n{'=' * 60}")
    print(f"Running: {description}")
    print(f"Script: {script_name}")
    print('=' * 60)

    start_time = time.time()

    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=False,  # Let output go to console
            text=True,
            check=True
        )

        elapsed = time.time() - start_time
        print(f"\n✓ Completed in {elapsed:.1f} seconds")
        return True

    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start_time
        print(f"\n✗ Failed after {elapsed:.1f} seconds")
        print(f"Error: {e}")
        return False


def main():
    """Run all extraction scripts in order."""
    print("=" * 60)
    print("Phase 0.6: Complete Extraction Pipeline")
    print("=" * 60)
    print("\nThis will run all extraction scripts in sequence.")
    print("Estimated time: 2-3 minutes")
    print()

    start_time = time.time()

    # Define the pipeline
    pipeline = [
        ('extract_names.py', 'Extract and clean name fields'),
        ('normalize_bonuses.py', 'Normalize bonus fields to integers'),
        ('normalize_type_codes.py', 'Normalize type codes'),
        ('extract_conditions.py', 'Extract condition references'),
        ('extract_damage.py', 'Extract damage information'),
        ('extract_cross_refs.py', 'Extract cross-references'),
        ('validate_extraction.py', 'Validate all extraction work'),
    ]

    # Run each script
    results = {}
    for script_name, description in pipeline:
        success = run_script(script_name, description)
        results[script_name] = success

        if not success:
            print(f"\n❌ Pipeline failed at: {script_name}")
            print("Please fix the errors and run again.")
            return 1

    # All scripts succeeded
    total_time = time.time() - start_time

    print("\n" + "=" * 60)
    print("Pipeline Complete!")
    print("=" * 60)
    print(f"\nTotal time: {total_time:.1f} seconds")
    print("\n✅ All extraction scripts completed successfully!")
    print("\nGenerated files:")
    print("  - cleaned_data/items_extracted.json")
    print("  - cleaned_data/monsters_extracted.json")
    print("  - cleaned_data/spells_extracted.json")
    print("  - extraction_data/conditions_extracted.json")
    print("  - extraction_data/damage_extracted.json")
    print("  - extraction_data/cross_refs_extracted.json")
    print("  - cleaned_data/EXTRACTION_VALIDATION.md")

    print("\nNext steps:")
    print("  - Review extraction_data/ files")
    print("  - Run Phase 2: Import scripts (when ready)")

    return 0


if __name__ == "__main__":
    exit(main())
