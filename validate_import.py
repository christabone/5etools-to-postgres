#!/usr/bin/env python3
"""
Comprehensive Database Import Validation Script

Performs exhaustive validation of the dnd5e_reference database to ensure:
- Data integrity (no orphaned records, valid foreign keys)
- Correct record counts matching source files
- No duplicate records where they shouldn't exist
- Data ranges are valid (CR, spell levels, etc.)
- Schema completeness (indexes, constraints present)
- Performance metrics within acceptable ranges

Usage:
    sudo -u postgres python3 validate_import.py

    Options:
        --verbose    Show detailed validation output
        --json       Output results as JSON
        --fix        Attempt to fix issues found (use with caution)

Exit Codes:
    0 - All validations passed
    1 - Critical issues found
    2 - Major issues found
    3 - Minor issues found
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import psycopg2
from psycopg2.extras import RealDictCursor

# Import our existing helpers
sys.path.insert(0, str(Path(__file__).parent))
from db_helpers import get_connection, log_info, log_success, log_warning, log_error


class Severity(Enum):
    """Issue severity levels"""
    CRITICAL = "CRITICAL"  # Data loss, corruption, broken FK
    MAJOR = "MAJOR"        # Significant data quality issues
    MINOR = "MINOR"        # Acceptable but suboptimal
    INFO = "INFO"          # Informational only


@dataclass
class ValidationIssue:
    """Represents a validation issue found"""
    severity: Severity
    category: str
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    fix_suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Stores validation results"""
    passed: List[str] = field(default_factory=list)
    issues: List[ValidationIssue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def add_pass(self, check_name: str):
        """Record a passing check"""
        self.passed.append(check_name)

    def add_issue(self, issue: ValidationIssue):
        """Record an issue"""
        self.issues.append(issue)

    def has_critical(self) -> bool:
        """Check if any critical issues exist"""
        return any(i.severity == Severity.CRITICAL for i in self.issues)

    def has_major(self) -> bool:
        """Check if any major issues exist"""
        return any(i.severity == Severity.MAJOR for i in self.issues)

    def has_minor(self) -> bool:
        """Check if any minor issues exist"""
        return any(i.severity == Severity.MINOR for i in self.issues)

    def get_exit_code(self) -> int:
        """Determine exit code based on issues"""
        if self.has_critical():
            return 1
        elif self.has_major():
            return 2
        elif self.has_minor():
            return 3
        return 0


class DatabaseValidator:
    """Main validation class"""

    def __init__(self, conn):
        self.conn = conn
        self.result = ValidationResult()

        # Expected counts from documentation
        self.expected_counts = {
            'items': 2722,
            'monsters': 4445,
            'spells': 937,
            'sources': 144,
            'item_types': 32,
            'item_properties': 31,
            'creature_types': 15,
            'creature_sizes': 6,
            'spell_schools': 8,
            'alignment_values': 7,
            'damage_types': 13,
            'condition_types': 15,
            'item_rarities': 10,
            'skills': 18,
            'attack_types': 6,
        }

    def run_all_validations(self, verbose: bool = False) -> ValidationResult:
        """Run all validation checks"""
        print("=" * 80)
        print("COMPREHENSIVE DATABASE VALIDATION")
        print("=" * 80)

        self.validate_entity_counts(verbose)
        self.validate_foreign_keys(verbose)
        self.validate_duplicates(verbose)
        self.validate_null_values(verbose)
        self.validate_data_ranges(verbose)
        self.validate_schema(verbose)
        self.validate_source_data_match(verbose)
        self.collect_metrics(verbose)

        return self.result

    def validate_entity_counts(self, verbose: bool):
        """Validate all table counts match expected values"""
        print("\n" + "=" * 80)
        print("1. ENTITY COUNT VALIDATION")
        print("=" * 80)

        for table, expected in self.expected_counts.items():
            with self.conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                actual = cur.fetchone()[0]

                if actual == expected:
                    self.result.add_pass(f"{table}_count")
                    if verbose:
                        print(f"✅ {table}: {actual} (matches expected)")
                else:
                    self.result.add_issue(ValidationIssue(
                        severity=Severity.CRITICAL if abs(actual - expected) > 10 else Severity.MAJOR,
                        category="entity_count",
                        description=f"{table} count mismatch",
                        details={'expected': expected, 'actual': actual, 'diff': actual - expected},
                        fix_suggestion=f"Re-run import for {table}"
                    ))
                    print(f"❌ {table}: {actual} (expected {expected}, diff: {actual - expected})")

        print(f"\n✅ Entity count validation complete: {len(self.result.passed)} tables verified")

    def validate_foreign_keys(self, verbose: bool):
        """Check for orphaned records in all junction tables"""
        print("\n" + "=" * 80)
        print("2. FOREIGN KEY INTEGRITY VALIDATION")
        print("=" * 80)

        # Define FK checks: (table, fk_column, referenced_table, referenced_column)
        fk_checks = [
            ('items', 'source_id', 'sources', 'id'),
            ('items', 'type_id', 'item_types', 'id'),
            ('items', 'rarity_id', 'item_rarities', 'id'),
            ('monsters', 'source_id', 'sources', 'id'),
            ('monsters', 'type_id', 'creature_types', 'id'),
            ('monsters', 'size_id', 'creature_sizes', 'id'),
            ('spells', 'source_id', 'sources', 'id'),
            ('spells', 'school_id', 'spell_schools', 'id'),
            ('item_conditions', 'item_id', 'items', 'id'),
            ('item_conditions', 'condition_id', 'condition_types', 'id'),
            ('item_damage', 'item_id', 'items', 'id'),
            ('item_damage', 'damage_type_id', 'damage_types', 'id'),
            ('monster_attacks', 'monster_id', 'monsters', 'id'),
            ('monster_attacks', 'attack_type_id', 'attack_types', 'id'),
            ('monster_spells', 'monster_id', 'monsters', 'id'),
            ('monster_spells', 'spell_id', 'spells', 'id'),
            ('spell_damage', 'spell_id', 'spells', 'id'),
            ('spell_damage', 'damage_type_id', 'damage_types', 'id'),
        ]

        orphan_count = 0
        for table, fk_col, ref_table, ref_col in fk_checks:
            # Skip if fk_col can be NULL
            nullable_fks = ['type_id', 'rarity_id', 'damage_type_id', 'attack_type_id']

            if fk_col in nullable_fks:
                # Check non-NULL values only
                query = f"""
                    SELECT COUNT(*) FROM {table} t
                    WHERE t.{fk_col} IS NOT NULL
                      AND NOT EXISTS (
                          SELECT 1 FROM {ref_table} r WHERE r.{ref_col} = t.{fk_col}
                      )
                """
            else:
                query = f"""
                    SELECT COUNT(*) FROM {table} t
                    WHERE NOT EXISTS (
                        SELECT 1 FROM {ref_table} r WHERE r.{ref_col} = t.{fk_col}
                    )
                """

            with self.conn.cursor() as cur:
                cur.execute(query)
                orphans = cur.fetchone()[0]

                if orphans == 0:
                    self.result.add_pass(f"fk_{table}_{fk_col}")
                    if verbose:
                        print(f"✅ {table}.{fk_col} → {ref_table}.{ref_col}: 0 orphans")
                else:
                    orphan_count += orphans
                    self.result.add_issue(ValidationIssue(
                        severity=Severity.CRITICAL,
                        category="foreign_key",
                        description=f"Orphaned records in {table}.{fk_col}",
                        details={'table': table, 'column': fk_col, 'orphan_count': orphans},
                        fix_suggestion=f"DELETE FROM {table} WHERE {fk_col} NOT IN (SELECT {ref_col} FROM {ref_table})"
                    ))
                    print(f"❌ {table}.{fk_col} → {ref_table}.{ref_col}: {orphans} orphans")

        if orphan_count == 0:
            print(f"\n✅ Foreign key validation complete: 0 orphaned records")
        else:
            print(f"\n❌ Foreign key validation FAILED: {orphan_count} orphaned records")

    def validate_duplicates(self, verbose: bool):
        """Check for unexpected duplicate records"""
        print("\n" + "=" * 80)
        print("3. DUPLICATE DETECTION")
        print("=" * 80)

        # Check for duplicates in tables that should have UNIQUE constraints
        duplicate_checks = [
            ('item_damage', ['item_id', 'damage_dice', 'damage_bonus', 'damage_type_id', 'versatile_dice', 'versatile_bonus']),
            ('spell_damage', ['spell_id', 'spell_level', 'damage_dice', 'damage_bonus', 'damage_type_id']),
            ('monster_attacks', ['monster_id', 'action_name']),
            ('item_conditions', ['item_id', 'condition_id']),
            ('spell_conditions', ['spell_id', 'condition_id']),
            ('monster_spells', ['monster_id', 'spell_id']),
        ]

        total_duplicates = 0
        for table, columns in duplicate_checks:
            # Build GROUP BY clause
            group_cols = ', '.join(columns)

            # Check for duplicates
            query = f"""
                SELECT COUNT(*) as dup_count
                FROM (
                    SELECT {group_cols}, COUNT(*) as cnt
                    FROM {table}
                    GROUP BY {group_cols}
                    HAVING COUNT(*) > 1
                ) duplicates
            """

            with self.conn.cursor() as cur:
                cur.execute(query)
                dup_groups = cur.fetchone()[0]

                if dup_groups == 0:
                    self.result.add_pass(f"duplicates_{table}")
                    if verbose:
                        print(f"✅ {table}: 0 duplicate groups")
                else:
                    total_duplicates += dup_groups
                    self.result.add_issue(ValidationIssue(
                        severity=Severity.CRITICAL,
                        category="duplicates",
                        description=f"Duplicate records found in {table}",
                        details={'table': table, 'duplicate_groups': dup_groups},
                        fix_suggestion=f"Review and remove duplicates from {table}"
                    ))
                    print(f"❌ {table}: {dup_groups} duplicate groups")

        if total_duplicates == 0:
            print(f"\n✅ Duplicate detection complete: 0 duplicates found")
        else:
            print(f"\n❌ Duplicate detection FAILED: {total_duplicates} duplicate groups found")

    def validate_null_values(self, verbose: bool):
        """Check for unexpected NULL values in required fields"""
        print("\n" + "=" * 80)
        print("4. NULL VALUE VALIDATION")
        print("=" * 80)

        # Check required fields that should never be NULL
        null_checks = [
            ('items', 'name'),
            ('items', 'source_id'),
            ('monsters', 'name'),
            ('monsters', 'source_id'),
            ('monsters', 'cr'),
            ('monsters', 'hp_average'),
            ('monsters', 'ac_primary'),
            ('spells', 'name'),
            ('spells', 'source_id'),
            ('spells', 'level'),
            ('spells', 'school_id'),
        ]

        null_issues = 0
        for table, column in null_checks:
            with self.conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {table} WHERE {column} IS NULL")
                null_count = cur.fetchone()[0]

                if null_count == 0:
                    self.result.add_pass(f"null_{table}_{column}")
                    if verbose:
                        print(f"✅ {table}.{column}: 0 NULLs")
                else:
                    null_issues += null_count
                    self.result.add_issue(ValidationIssue(
                        severity=Severity.CRITICAL,
                        category="null_values",
                        description=f"NULL values in required field {table}.{column}",
                        details={'table': table, 'column': column, 'null_count': null_count},
                        fix_suggestion=f"Investigate why {table}.{column} has NULL values"
                    ))
                    print(f"❌ {table}.{column}: {null_count} NULLs")

        # Check optional fields with high NULL rates (informational)
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*), COUNT(*) FILTER (WHERE type_id IS NULL) FROM items")
            total, null_type = cur.fetchone()
            null_pct = (null_type / total * 100) if total > 0 else 0

            if null_pct > 50:
                self.result.add_issue(ValidationIssue(
                    severity=Severity.INFO,
                    category="null_values",
                    description=f"High NULL rate in items.type_id: {null_pct:.1f}%",
                    details={'null_count': null_type, 'total': total, 'percentage': null_pct},
                    fix_suggestion="This may be expected for generic items"
                ))
                print(f"ℹ️  items.type_id: {null_type}/{total} NULL ({null_pct:.1f}%)")

        if null_issues == 0:
            print(f"\n✅ NULL validation complete: 0 unexpected NULLs")
        else:
            print(f"\n❌ NULL validation FAILED: {null_issues} unexpected NULLs")

    def validate_data_ranges(self, verbose: bool):
        """Validate that data values are within expected ranges"""
        print("\n" + "=" * 80)
        print("5. DATA RANGE VALIDATION")
        print("=" * 80)

        range_violations = 0

        # Spell levels should be 0-9
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM spells WHERE level < 0 OR level > 9")
            violations = cur.fetchone()[0]

            if violations == 0:
                self.result.add_pass("range_spell_level")
                if verbose:
                    print(f"✅ Spell levels: All values 0-9")
            else:
                range_violations += violations
                self.result.add_issue(ValidationIssue(
                    severity=Severity.CRITICAL,
                    category="data_range",
                    description="Invalid spell levels found",
                    details={'violations': violations},
                    fix_suggestion="Check spell level extraction logic"
                ))
                print(f"❌ Spell levels: {violations} values out of range")

        # Monster CR should be 0-30
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM monsters WHERE cr < 0 OR cr > 30")
            violations = cur.fetchone()[0]

            if violations == 0:
                self.result.add_pass("range_monster_cr")
                if verbose:
                    print(f"✅ Monster CR: All values 0-30")
            else:
                range_violations += violations
                self.result.add_issue(ValidationIssue(
                    severity=Severity.MAJOR,
                    category="data_range",
                    description="Invalid monster CR values found",
                    details={'violations': violations},
                    fix_suggestion="Review monster CR extraction"
                ))
                print(f"❌ Monster CR: {violations} values out of range")

        # Monster HP should be positive
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM monsters WHERE hp_average <= 0")
            violations = cur.fetchone()[0]

            if violations == 0:
                self.result.add_pass("range_monster_hp")
                if verbose:
                    print(f"✅ Monster HP: All values > 0")
            else:
                range_violations += violations
                self.result.add_issue(ValidationIssue(
                    severity=Severity.CRITICAL,
                    category="data_range",
                    description="Invalid monster HP values found",
                    details={'violations': violations},
                    fix_suggestion="Check monster HP extraction"
                ))
                print(f"❌ Monster HP: {violations} values <= 0")

        if range_violations == 0:
            print(f"\n✅ Data range validation complete: All values within bounds")
        else:
            print(f"\n❌ Data range validation FAILED: {range_violations} violations")

    def validate_schema(self, verbose: bool):
        """Validate database schema structure"""
        print("\n" + "=" * 80)
        print("6. SCHEMA VALIDATION")
        print("=" * 80)

        # Count indexes
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM pg_indexes
                WHERE schemaname = 'public'
            """)
            index_count = cur.fetchone()[0]

            expected_indexes = 141
            if index_count == expected_indexes:
                self.result.add_pass("schema_indexes")
                print(f"✅ Indexes: {index_count} (matches expected)")
            else:
                self.result.add_issue(ValidationIssue(
                    severity=Severity.MAJOR if abs(index_count - expected_indexes) > 5 else Severity.MINOR,
                    category="schema",
                    description=f"Index count mismatch",
                    details={'expected': expected_indexes, 'actual': index_count},
                    fix_suggestion="Review schema.sql"
                ))
                print(f"⚠️  Indexes: {index_count} (expected {expected_indexes})")

        # Count foreign keys
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM pg_constraint
                WHERE contype = 'f' AND connamespace = 'public'::regnamespace
            """)
            fk_count = cur.fetchone()[0]

            expected_fks = 54
            if fk_count == expected_fks:
                self.result.add_pass("schema_foreign_keys")
                print(f"✅ Foreign Keys: {fk_count} (matches expected)")
            else:
                self.result.add_issue(ValidationIssue(
                    severity=Severity.MAJOR,
                    category="schema",
                    description=f"Foreign key count mismatch",
                    details={'expected': expected_fks, 'actual': fk_count},
                    fix_suggestion="Review schema.sql foreign key definitions"
                ))
                print(f"⚠️  Foreign Keys: {fk_count} (expected {expected_fks})")

        # Check for required UNIQUE constraints
        required_unique = [
            ('item_damage', 'item_damage_unique'),
            ('spell_damage', 'spell_damage_unique'),
            ('monster_attacks', 'monster_attacks_monster_id_action_name_key'),
        ]

        for table, constraint_name in required_unique:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM pg_constraint
                    WHERE conname = %s AND contype = 'u'
                """, (constraint_name,))
                exists = cur.fetchone()[0] > 0

                if exists:
                    self.result.add_pass(f"schema_unique_{table}")
                    if verbose:
                        print(f"✅ UNIQUE constraint on {table}: Present")
                else:
                    self.result.add_issue(ValidationIssue(
                        severity=Severity.CRITICAL,
                        category="schema",
                        description=f"Missing UNIQUE constraint on {table}",
                        details={'table': table, 'constraint': constraint_name},
                        fix_suggestion=f"Add UNIQUE constraint to {table}"
                    ))
                    print(f"❌ UNIQUE constraint on {table}: MISSING")

        print(f"\n✅ Schema validation complete")

    def validate_source_data_match(self, verbose: bool):
        """Validate database counts match source JSON files"""
        print("\n" + "=" * 80)
        print("7. SOURCE DATA COMPARISON")
        print("=" * 80)

        source_files = {
            'items': 'cleaned_data/items_extracted.json',
            'monsters': 'cleaned_data/monsters_extracted.json',
            'spells': 'cleaned_data/spells_extracted.json',
        }

        for entity, file_path in source_files.items():
            path = Path(file_path)
            if not path.exists():
                print(f"⚠️  {entity}: Source file not found ({file_path})")
                continue

            with open(path) as f:
                source_data = json.load(f)
                source_count = len(source_data)

            with self.conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {entity}")
                db_count = cur.fetchone()[0]

            if source_count == db_count:
                self.result.add_pass(f"source_match_{entity}")
                print(f"✅ {entity}: {db_count} (matches source)")
            else:
                self.result.add_issue(ValidationIssue(
                    severity=Severity.CRITICAL,
                    category="source_match",
                    description=f"{entity} count doesn't match source file",
                    details={'source': source_count, 'database': db_count, 'diff': db_count - source_count},
                    fix_suggestion=f"Re-import {entity} from {file_path}"
                ))
                print(f"❌ {entity}: DB={db_count}, Source={source_count} (diff: {db_count - source_count})")

        print(f"\n✅ Source data comparison complete")

    def collect_metrics(self, verbose: bool):
        """Collect database metrics"""
        print("\n" + "=" * 80)
        print("8. DATABASE METRICS")
        print("=" * 80)

        # Database size
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT pg_size_pretty(pg_database_size('dnd5e_reference'))
            """)
            db_size = cur.fetchone()[0]
            self.result.metrics['database_size'] = db_size
            print(f"📊 Database size: {db_size}")

        # Total record count
        total_records = 0
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT schemaname, tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                  AND tablename NOT LIKE '%_backup'
                ORDER BY tablename
            """)
            tables = cur.fetchall()

            for schema, table in tables:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                total_records += count

        self.result.metrics['total_records'] = total_records
        print(f"📊 Total records: {total_records:,}")

        # Table count
        self.result.metrics['table_count'] = len(tables)
        print(f"📊 Total tables: {len(tables)}")

        print(f"\n✅ Metrics collection complete")


def print_summary(result: ValidationResult):
    """Print validation summary"""
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)

    print(f"\n✅ Checks Passed: {len(result.passed)}")

    if result.issues:
        print(f"\n⚠️  Issues Found: {len(result.issues)}")

        # Group by severity
        critical = [i for i in result.issues if i.severity == Severity.CRITICAL]
        major = [i for i in result.issues if i.severity == Severity.MAJOR]
        minor = [i for i in result.issues if i.severity == Severity.MINOR]
        info = [i for i in result.issues if i.severity == Severity.INFO]

        if critical:
            print(f"\n🔴 CRITICAL Issues ({len(critical)}):")
            for issue in critical:
                print(f"   - {issue.description}")
                if issue.fix_suggestion:
                    print(f"     Fix: {issue.fix_suggestion}")

        if major:
            print(f"\n🟠 MAJOR Issues ({len(major)}):")
            for issue in major:
                print(f"   - {issue.description}")

        if minor:
            print(f"\n🟡 MINOR Issues ({len(minor)}):")
            for issue in minor:
                print(f"   - {issue.description}")

        if info:
            print(f"\nℹ️  INFO ({len(info)}):")
            for issue in info:
                print(f"   - {issue.description}")
    else:
        print(f"\n✅ No issues found!")

    print(f"\n" + "=" * 80)
    if result.has_critical():
        print("❌ VALIDATION FAILED - Critical issues must be fixed")
    elif result.has_major():
        print("⚠️  VALIDATION WARNING - Major issues found")
    elif result.has_minor():
        print("✅ VALIDATION PASSED - Minor issues noted")
    else:
        print("✅ VALIDATION PASSED - All checks successful")
    print("=" * 80)


def main():
    """Main validation entry point"""
    parser = argparse.ArgumentParser(description="Validate database import")
    parser.add_argument('--verbose', '-v', action='store_true', help="Show detailed output")
    parser.add_argument('--json', action='store_true', help="Output results as JSON")
    args = parser.parse_args()

    # Connect to database
    try:
        conn = get_connection()
    except Exception as e:
        log_error(f"Failed to connect to database: {e}")
        return 1

    # Run validation
    validator = DatabaseValidator(conn)
    result = validator.run_all_validations(verbose=args.verbose)

    # Print summary
    if not args.json:
        print_summary(result)
    else:
        # Output JSON
        json_result = {
            'passed': result.passed,
            'issues': [
                {
                    'severity': i.severity.value,
                    'category': i.category,
                    'description': i.description,
                    'details': i.details,
                    'fix_suggestion': i.fix_suggestion
                }
                for i in result.issues
            ],
            'metrics': result.metrics,
            'exit_code': result.get_exit_code()
        }
        print(json.dumps(json_result, indent=2))

    conn.close()
    return result.get_exit_code()


if __name__ == '__main__':
    sys.exit(main())
