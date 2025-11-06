#!/usr/bin/env python3
"""
5etools-to-postgres Master Pipeline Orchestrator

This script runs the complete data pipeline from raw 5etools JSON to PostgreSQL database.
It includes validation checkpoints between each phase to catch errors early.

Usage:
    # Full pipeline with drop-and-replace
    python3 run_pipeline.py --mode full --drop

    # Resume from a specific phase
    python3 run_pipeline.py --mode resume --from-phase 2

    # Dry run (validation only, no database changes)
    python3 run_pipeline.py --mode dry-run

    # Skip certain phases
    python3 run_pipeline.py --mode full --skip-analysis --drop

Options:
    --mode {full,resume,dry-run}    Pipeline execution mode
    --from-phase N                  Resume from phase N (requires --mode resume)
    --drop                          Drop and recreate database before import
    --skip-analysis                 Skip Phase 0 (analysis) - use existing analysis
    --skip-cleaning                 Skip Phase 0.5 (cleaning) - use existing cleaned data
    --skip-extraction               Skip Phase 0.6 (extraction) - use existing extracted data
    --verbose                       Show detailed output from each script
    --stop-on-warning              Stop pipeline if any warnings are found
"""

import argparse
import subprocess
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum


class PhaseStatus(Enum):
    """Phase execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PhaseResult:
    """Result from executing a phase"""
    phase: str
    status: PhaseStatus
    duration: float
    output: str = ""
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict = field(default_factory=dict)


@dataclass
class Checkpoint:
    """Validation checkpoint between phases"""
    name: str
    description: str
    validation_func: callable
    critical: bool = True  # If True, failure stops pipeline


class PipelineOrchestrator:
    """Master orchestrator for the complete data pipeline"""

    def __init__(self, args):
        self.args = args
        self.start_time = datetime.now()
        self.results: List[PhaseResult] = []
        self.project_dir = Path(__file__).parent

        # Ensure we're in the project directory
        import os
        os.chdir(self.project_dir)

    def run(self) -> int:
        """
        Execute the complete pipeline.
        Returns exit code: 0 = success, 1 = failure
        """
        print("=" * 80)
        print("5etools-to-postgres Data Pipeline")
        print("=" * 80)
        print(f"Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Mode: {self.args.mode}")
        print(f"Project directory: {self.project_dir}")
        print("=" * 80)
        print()

        try:
            if self.args.mode == "dry-run":
                return self.run_dry_run()
            elif self.args.mode == "resume":
                return self.run_resume()
            else:  # full
                return self.run_full()

        except KeyboardInterrupt:
            print("\n\n⚠️  Pipeline interrupted by user")
            return 130
        except Exception as e:
            print(f"\n\n❌ Pipeline failed with unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return 1
        finally:
            self.print_summary()

    def run_full(self) -> int:
        """Run the complete pipeline from start to finish"""

        # Phase 0: Analysis (optional)
        if not self.args.skip_analysis:
            if not self.run_phase_0():
                return 1
        else:
            print("⏭️  Skipping Phase 0 (Analysis) - using existing analysis")
            self.results.append(PhaseResult("Phase 0: Analysis", PhaseStatus.SKIPPED, 0.0))

        # Phase 0.5: Cleaning (optional)
        if not self.args.skip_cleaning:
            if not self.run_phase_0_5():
                return 1
        else:
            print("⏭️  Skipping Phase 0.5 (Cleaning) - using existing cleaned data")
            self.results.append(PhaseResult("Phase 0.5: Cleaning", PhaseStatus.SKIPPED, 0.0))

        # Phase 0.6: Extraction (optional)
        if not self.args.skip_extraction:
            if not self.run_phase_0_6():
                return 1
        else:
            print("⏭️  Skipping Phase 0.6 (Extraction) - using existing extracted data")
            self.results.append(PhaseResult("Phase 0.6: Extraction", PhaseStatus.SKIPPED, 0.0))

        # Checkpoint: Verify extracted data
        if not self.checkpoint_extracted_data():
            return 1

        # Phase 1: Schema (drop and recreate if requested)
        if not self.run_phase_1():
            return 1

        # Checkpoint: Verify schema
        if not self.checkpoint_schema():
            return 1

        # Phase 2: Import
        if not self.run_phase_2():
            return 1

        # Checkpoint: Validate import
        if not self.checkpoint_import():
            return 1

        # Phase 3: Testing
        if not self.run_phase_3():
            return 1

        print("\n✅ Pipeline completed successfully!")
        return 0

    def run_resume(self) -> int:
        """Resume pipeline from a specific phase"""
        start_phase = self.args.from_phase
        print(f"📍 Resuming pipeline from Phase {start_phase}")

        if start_phase <= 0:
            return self.run_full()
        elif start_phase == 1:
            return self.run_phase_1() and self.checkpoint_schema() and \
                   self.run_phase_2() and self.checkpoint_import() and \
                   self.run_phase_3()
        elif start_phase == 2:
            return self.run_phase_2() and self.checkpoint_import() and \
                   self.run_phase_3()
        elif start_phase == 3:
            return self.run_phase_3()
        else:
            print(f"❌ Invalid phase number: {start_phase}")
            return 1

    def run_dry_run(self) -> int:
        """Validate all files and configurations without making changes"""
        print("🔍 Running dry-run validation...")
        print()

        checks = [
            ("Source data", self.check_source_data),
            ("Cleaned data", self.check_cleaned_data),
            ("Extracted data", self.check_extracted_data),
            ("Database schema", self.check_schema_file),
            ("Database connection", self.check_database_connection),
            ("Import scripts", self.check_import_scripts),
            ("Test scripts", self.check_test_scripts),
        ]

        all_passed = True
        for name, check_func in checks:
            try:
                print(f"Checking {name}...", end=" ")
                check_func()
                print("✅")
            except Exception as e:
                print(f"❌ {e}")
                all_passed = False

        print()
        if all_passed:
            print("✅ All dry-run checks passed")
            return 0
        else:
            print("❌ Some dry-run checks failed")
            return 1

    # ========================================================================
    # PHASE EXECUTION
    # ========================================================================

    def run_phase_0(self) -> bool:
        """Phase 0: Data Structure Analysis"""
        print("\n" + "=" * 80)
        print("PHASE 0: Data Structure Analysis")
        print("=" * 80)

        # Note: Analysis is typically only run once per 5etools version
        # Most pipeline runs will skip this phase
        print("⚠️  Phase 0 (Analysis) is typically run once per 5etools version")
        print("    Use --skip-analysis for normal pipeline runs")
        print()

        scripts = [
            "analyze_json_structure.py",
            "analyze_field_types.py",
            "analyze_controlled_vocab.py",
            "analyze_relationships.py",
        ]

        for script in scripts:
            result = self.run_script(script, "Phase 0: Analysis")
            if result.status == PhaseStatus.FAILED:
                return False

        return True

    def run_phase_0_5(self) -> bool:
        """Phase 0.5: Data Cleaning & Normalization"""
        print("\n" + "=" * 80)
        print("PHASE 0.5: Data Cleaning & Normalization")
        print("=" * 80)

        result = self.run_script("clean_all.py", "Phase 0.5: Cleaning")
        return result.status != PhaseStatus.FAILED

    def run_phase_0_6(self) -> bool:
        """Phase 0.6: Markup Extraction"""
        print("\n" + "=" * 80)
        print("PHASE 0.6: Markup Extraction & Advanced Normalization")
        print("=" * 80)

        result = self.run_script("extract_all.py", "Phase 0.6: Extraction")
        return result.status != PhaseStatus.FAILED

    def run_phase_1(self) -> bool:
        """Phase 1: Schema Creation"""
        print("\n" + "=" * 80)
        print("PHASE 1: Database Schema")
        print("=" * 80)

        if self.args.drop:
            print("🗑️  Dropping and recreating database...")
            result = self.run_sql_command([
                "DROP DATABASE IF EXISTS dnd5e_reference;",
                "CREATE DATABASE dnd5e_reference;"
            ], "Drop & Create Database")
            if result.status == PhaseStatus.FAILED:
                return False

        print("📐 Creating schema...")
        result = self.run_sql_file("schema.sql", "Create Schema")
        if result.status == PhaseStatus.FAILED:
            return False

        print("📊 Importing controlled vocabulary...")
        result = self.run_sql_file("import_controlled_vocab.sql", "Import Controlled Vocab")
        return result.status != PhaseStatus.FAILED

    def run_phase_2(self) -> bool:
        """Phase 2: Data Import"""
        print("\n" + "=" * 80)
        print("PHASE 2: Data Import")
        print("=" * 80)

        scripts = [
            ("import_items.py", "Import Items"),
            ("import_monsters.py", "Import Monsters"),
            ("import_spells.py", "Import Spells"),
            ("import_extracted_data.py", "Import Relationships"),
        ]

        for script, description in scripts:
            result = self.run_script(script, f"Phase 2: {description}")
            if result.status == PhaseStatus.FAILED:
                return False

        return True

    def run_phase_3(self) -> bool:
        """Phase 3: Validation & Testing"""
        print("\n" + "=" * 80)
        print("PHASE 3: Validation & Testing")
        print("=" * 80)

        # Run validation
        print("🔍 Running database validation...")
        result = self.run_script("validate_import.py", "Phase 3: Validation", args=["-v"])
        if result.status == PhaseStatus.FAILED:
            return False

        # Run tests
        print("🧪 Running test suite...")
        result = self.run_command(
            ["./run_tests.sh", "-v", "--tb=short"],
            "Phase 3: Testing"
        )
        return result.status != PhaseStatus.FAILED

    # ========================================================================
    # CHECKPOINTS
    # ========================================================================

    def checkpoint_extracted_data(self) -> bool:
        """Checkpoint: Verify extracted data files exist and are valid"""
        print("\n" + "-" * 80)
        print("CHECKPOINT: Extracted Data Validation")
        print("-" * 80)

        required_files = [
            "cleaned_data/items_extracted.json",
            "cleaned_data/monsters_extracted.json",
            "cleaned_data/spells_extracted.json",
            "extraction_data/conditions_extracted.json",
            "extraction_data/damage_extracted.json",
            "extraction_data/cross_refs_extracted.json",
        ]

        for filepath in required_files:
            if not (self.project_dir / filepath).exists():
                print(f"❌ Missing required file: {filepath}")
                return False

            # Validate JSON
            try:
                with open(self.project_dir / filepath) as f:
                    data = json.load(f)
                    count = len(data) if isinstance(data, list) else len(data.get('items', []))
                    print(f"✅ {filepath}: {count:,} records")
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON in {filepath}: {e}")
                return False

        print("✅ All extracted data files valid")
        return True

    def checkpoint_schema(self) -> bool:
        """Checkpoint: Verify database schema is correctly created"""
        print("\n" + "-" * 80)
        print("CHECKPOINT: Schema Validation")
        print("-" * 80)

        # Check table count
        result = self.run_sql_query(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';",
            "Count Tables"
        )
        if result.status == PhaseStatus.FAILED:
            return False

        table_count = int(result.output.strip().split('\n')[-1].strip())
        expected_tables = 38
        if table_count != expected_tables:
            print(f"❌ Expected {expected_tables} tables, found {table_count}")
            return False
        print(f"✅ Schema has correct table count: {table_count}")

        # Check index count
        result = self.run_sql_query(
            "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public';",
            "Count Indexes"
        )
        if result.status == PhaseStatus.FAILED:
            return False

        index_count = int(result.output.strip().split('\n')[-1].strip())
        min_indexes = 140  # Allow some variance
        if index_count < min_indexes:
            print(f"⚠️  Expected ~141 indexes, found {index_count}")
        else:
            print(f"✅ Schema has sufficient indexes: {index_count}")

        print("✅ Schema validation passed")
        return True

    def checkpoint_import(self) -> bool:
        """Checkpoint: Validate import results"""
        print("\n" + "-" * 80)
        print("CHECKPOINT: Import Validation")
        print("-" * 80)

        # Run the validation script
        result = self.run_script("validate_import.py", "Import Validation", args=["--json"])

        if result.status == PhaseStatus.FAILED:
            print("❌ Import validation failed")
            return False
        elif result.status == PhaseStatus.WARNING:
            if self.args.stop_on_warning:
                print("❌ Stopping pipeline due to warnings (--stop-on-warning)")
                return False
            else:
                print("⚠️  Import validation passed with warnings")
                return True

        print("✅ Import validation passed")
        return True

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def run_script(self, script: str, phase: str, args: List[str] = None) -> PhaseResult:
        """Run a Python script and capture results"""
        cmd = ["python3", script]
        if args:
            cmd.extend(args)
        return self.run_command(cmd, phase)

    def run_command(self, cmd: List[str], phase: str) -> PhaseResult:
        """Run a shell command and capture results"""
        start = time.time()

        print(f"\n▶️  Running: {' '.join(cmd)}")

        try:
            if self.args.verbose:
                # Stream output in real-time
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

                output_lines = []
                for line in process.stdout:
                    print(line, end='')
                    output_lines.append(line)

                process.wait()
                output = ''.join(output_lines)
                returncode = process.returncode
            else:
                # Capture output silently
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False
                )
                output = result.stdout + result.stderr
                returncode = result.returncode

            duration = time.time() - start

            if returncode == 0:
                status = PhaseStatus.SUCCESS
                print(f"✅ {phase} completed in {duration:.1f}s")
            elif returncode == 3:
                status = PhaseStatus.WARNING
                print(f"⚠️  {phase} completed with warnings in {duration:.1f}s")
            else:
                status = PhaseStatus.FAILED
                print(f"❌ {phase} failed (exit code {returncode}) after {duration:.1f}s")
                print(f"Output:\n{output}")

            result = PhaseResult(
                phase=phase,
                status=status,
                duration=duration,
                output=output
            )
            self.results.append(result)
            return result

        except Exception as e:
            duration = time.time() - start
            print(f"❌ {phase} failed with exception: {e}")
            result = PhaseResult(
                phase=phase,
                status=PhaseStatus.FAILED,
                duration=duration,
                errors=[str(e)]
            )
            self.results.append(result)
            return result

    def run_sql_file(self, filepath: str, phase: str) -> PhaseResult:
        """Run a SQL file against the database"""
        cmd = [
            "sudo", "-u", "postgres",
            "psql", "-d", "dnd5e_reference",
            "-f", filepath
        ]
        return self.run_command(cmd, phase)

    def run_sql_command(self, statements: List[str], phase: str) -> PhaseResult:
        """Run SQL statements against the postgres server"""
        cmd = ["sudo", "-u", "postgres", "psql", "-c", "; ".join(statements)]
        return self.run_command(cmd, phase)

    def run_sql_query(self, query: str, phase: str) -> PhaseResult:
        """Run a SQL query and return results"""
        cmd = [
            "sudo", "-u", "postgres",
            "psql", "-d", "dnd5e_reference",
            "-t", "-c", query
        ]
        return self.run_command(cmd, phase)

    # ========================================================================
    # VALIDATION CHECKS
    # ========================================================================

    def check_source_data(self):
        """Check that source data directory exists"""
        # This would check the 5etools-src directory
        # For now, just a placeholder
        pass

    def check_cleaned_data(self):
        """Check that cleaned data files exist"""
        required = ["items.json", "monsters.json", "spells.json"]
        for filename in required:
            path = self.project_dir / "cleaned_data" / filename
            if not path.exists():
                raise FileNotFoundError(f"Missing cleaned data: {filename}")

    def check_extracted_data(self):
        """Check that extracted data files exist"""
        required = [
            "items_extracted.json",
            "monsters_extracted.json",
            "spells_extracted.json"
        ]
        for filename in required:
            path = self.project_dir / "cleaned_data" / filename
            if not path.exists():
                raise FileNotFoundError(f"Missing extracted data: {filename}")

    def check_schema_file(self):
        """Check that schema.sql exists"""
        if not (self.project_dir / "schema.sql").exists():
            raise FileNotFoundError("Missing schema.sql")

    def check_database_connection(self):
        """Check that we can connect to PostgreSQL"""
        result = subprocess.run(
            ["sudo", "-u", "postgres", "psql", "-c", "SELECT 1"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise ConnectionError("Cannot connect to PostgreSQL")

    def check_import_scripts(self):
        """Check that all import scripts exist"""
        required = [
            "import_items.py",
            "import_monsters.py",
            "import_spells.py",
            "import_extracted_data.py"
        ]
        for script in required:
            if not (self.project_dir / script).exists():
                raise FileNotFoundError(f"Missing import script: {script}")

    def check_test_scripts(self):
        """Check that test infrastructure exists"""
        if not (self.project_dir / "validate_import.py").exists():
            raise FileNotFoundError("Missing validate_import.py")
        if not (self.project_dir / "test_database.py").exists():
            raise FileNotFoundError("Missing test_database.py")

    # ========================================================================
    # SUMMARY
    # ========================================================================

    def print_summary(self):
        """Print pipeline execution summary"""
        duration = (datetime.now() - self.start_time).total_seconds()

        print("\n" + "=" * 80)
        print("PIPELINE SUMMARY")
        print("=" * 80)
        print(f"Total duration: {duration:.1f}s ({duration/60:.1f} minutes)")
        print()

        if not self.results:
            print("No phases executed")
            return

        # Count statuses
        counts = {status: 0 for status in PhaseStatus}
        for result in self.results:
            counts[result.status] += 1

        # Print results table
        print(f"{'Phase':<40} {'Status':<12} {'Duration':>10}")
        print("-" * 80)
        for result in self.results:
            status_symbol = {
                PhaseStatus.SUCCESS: "✅",
                PhaseStatus.WARNING: "⚠️ ",
                PhaseStatus.FAILED: "❌",
                PhaseStatus.SKIPPED: "⏭️ "
            }.get(result.status, "❓")

            print(f"{result.phase:<40} {status_symbol} {result.status.value:<10} {result.duration:>8.1f}s")

        print("-" * 80)
        print(f"Total: {len(self.results)} phases | " +
              f"Success: {counts[PhaseStatus.SUCCESS]} | " +
              f"Warning: {counts[PhaseStatus.WARNING]} | " +
              f"Failed: {counts[PhaseStatus.FAILED]} | " +
              f"Skipped: {counts[PhaseStatus.SKIPPED]}")
        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="5etools-to-postgres Master Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--mode",
        choices=["full", "resume", "dry-run"],
        default="full",
        help="Pipeline execution mode"
    )

    parser.add_argument(
        "--from-phase",
        type=int,
        metavar="N",
        help="Resume from phase N (requires --mode resume)"
    )

    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop and recreate database before import"
    )

    parser.add_argument(
        "--skip-analysis",
        action="store_true",
        help="Skip Phase 0 (analysis) - use existing analysis"
    )

    parser.add_argument(
        "--skip-cleaning",
        action="store_true",
        help="Skip Phase 0.5 (cleaning) - use existing cleaned data"
    )

    parser.add_argument(
        "--skip-extraction",
        action="store_true",
        help="Skip Phase 0.6 (extraction) - use existing extracted data"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output from each script"
    )

    parser.add_argument(
        "--stop-on-warning",
        action="store_true",
        help="Stop pipeline if any warnings are found"
    )

    args = parser.parse_args()

    # Validation
    if args.mode == "resume" and args.from_phase is None:
        parser.error("--mode resume requires --from-phase N")

    orchestrator = PipelineOrchestrator(args)
    exit_code = orchestrator.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
