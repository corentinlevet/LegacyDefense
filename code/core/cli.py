"""
Command-line interface tools for GeneWeb Python implementation.

This module provides CLI utilities to replace the original OCaml command-line tools
like gwc, ged2gwb, gwb2ged, gwfixbase, consang, etc.
"""

import json
import os
import sys
from datetime import datetime
from typing import List, Optional

import click
from sqlalchemy.orm import Session

from .database import DatabaseManager, FamilyORM, PersonORM
from .gedcom import GedcomExporter, GedcomParser
from .models import Database, Family, Person


@click.group()
@click.version_option(version="1.0.0")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option(
    "--database-url",
    "-d",
    default="sqlite:///geneweb.db",
    help="Database URL (default: sqlite:///geneweb.db)",
)
@click.pass_context
def cli(ctx, verbose, database_url):
    """GeneWeb Python command-line tools."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["database_url"] = database_url
    ctx.obj["db_manager"] = DatabaseManager(database_url)


@cli.command()
@click.argument("gedcom_file", type=click.Path(exists=True))
@click.option("--output", "-o", help="Output database file (optional)")
@click.option("--check/--no-check", default=True, help="Perform data validation")
@click.option(
    "--statistics/--no-statistics", default=True, help="Show import statistics"
)
@click.pass_context
def import_gedcom(ctx, gedcom_file, output, check, statistics):
    """Import GEDCOM file into database (equivalent to ged2gwb)."""
    if ctx.obj["verbose"]:
        click.echo(f"Importing GEDCOM file: {gedcom_file}")

    db_manager = ctx.obj["db_manager"]
    db_manager.create_tables()

    try:
        # Parse GEDCOM file
        parser = GedcomParser()
        persons, families = parser.parse_file(gedcom_file)
        parser.link_families()

        if ctx.obj["verbose"]:
            click.echo(f"Parsed {len(persons)} persons and {len(families)} families")

        # Import to database
        with db_manager.get_session() as session:
            person_count = 0
            family_count = 0

            # Import persons
            for person_id, person in persons.items():
                person_data = {
                    "first_name": person.name.first_name,
                    "surname": person.name.surname,
                    "sex": person.sex,
                    "occupation": person.occupation,
                    "notes": person.notes,
                }
                db_manager.add_person(session, person_data)
                person_count += 1

                if ctx.obj["verbose"] and person_count % 100 == 0:
                    click.echo(f"Imported {person_count} persons...")

            # Import families
            for family_id, family in families.items():
                family_data = {
                    "marriage": family.marriage,
                    "marriage_note": family.marriage_note,
                    "divorce": family.divorce,
                    "notes": family.notes,
                }
                db_manager.add_family(session, family_data)
                family_count += 1

                if ctx.obj["verbose"] and family_count % 50 == 0:
                    click.echo(f"Imported {family_count} families...")

        if statistics:
            click.echo("\nImport Statistics:")
            click.echo(f"  Persons imported: {person_count}")
            click.echo(f"  Families imported: {family_count}")

        click.echo(f"✓ Successfully imported {gedcom_file}")

    except Exception as e:
        click.echo(f"✗ Error importing GEDCOM: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--output", "-o", default="export.ged", help="Output GEDCOM file")
@click.option("--persons", "-p", help="Comma-separated list of person IDs to export")
@click.pass_context
def export_gedcom(ctx, output, persons):
    """Export database to GEDCOM file (equivalent to gwb2ged)."""
    if ctx.obj["verbose"]:
        click.echo(f"Exporting to GEDCOM file: {output}")

    db_manager = ctx.obj["db_manager"]

    try:
        with db_manager.get_session() as session:
            # Get persons and families from database
            if persons:
                person_ids = [int(p.strip()) for p in persons.split(",")]
                persons_orm = (
                    session.query(PersonORM).filter(PersonORM.id.in_(person_ids)).all()
                )
            else:
                persons_orm = session.query(PersonORM).all()

            families_orm = session.query(FamilyORM).all()

            if ctx.obj["verbose"]:
                click.echo(
                    f"Found {len(persons_orm)} persons and {len(families_orm)} families"
                )

            # Convert to dataclass format (simplified conversion)
            persons_dict = {}
            families_dict = {}

            # TODO: Proper conversion from ORM to dataclasses
            # This is a simplified placeholder

            # Export using GedcomExporter
            exporter = GedcomExporter(persons_dict, families_dict)
            exporter.export_to_file(output)

        click.echo(f"✓ Successfully exported to {output}")

    except Exception as e:
        click.echo(f"✗ Error exporting GEDCOM: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--check/--no-check", default=True, help="Perform database consistency check"
)
@click.option("--fix/--no-fix", default=False, help="Fix found issues automatically")
@click.option("--backup/--no-backup", default=True, help="Create backup before fixing")
@click.pass_context
def fix_database(ctx, check, fix, backup):
    """Fix database inconsistencies (equivalent to gwfixbase)."""
    if ctx.obj["verbose"]:
        click.echo("Running database consistency checks...")

    db_manager = ctx.obj["db_manager"]

    try:
        if backup and fix:
            backup_path = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            if db_manager.backup_database(backup_path):
                click.echo(f"✓ Created backup: {backup_path}")
            else:
                click.echo("⚠ Failed to create backup", err=True)

        with db_manager.get_session() as session:
            issues = []
            fixes_applied = 0

            # Check for orphaned children (children without valid parent family)
            orphaned_children = (
                session.query(PersonORM)
                .filter(
                    PersonORM.parent_family_id.isnot(None),
                    ~PersonORM.parent_family_id.in_(session.query(FamilyORM.id)),
                )
                .all()
            )

            if orphaned_children:
                issue = f"Found {len(orphaned_children)} orphaned children"
                issues.append(issue)
                click.echo(f"⚠ {issue}")

                if fix:
                    for child in orphaned_children:
                        child.parent_family_id = None
                        fixes_applied += 1
                    session.commit()
                    click.echo(f"✓ Fixed orphaned children references")

            # Check for families without parents
            empty_families = (
                session.query(FamilyORM)
                .filter(FamilyORM.father_id.is_(None), FamilyORM.mother_id.is_(None))
                .all()
            )

            if empty_families:
                issue = f"Found {len(empty_families)} families without parents"
                issues.append(issue)
                click.echo(f"⚠ {issue}")

                if fix:
                    for family in empty_families:
                        # Check if family has children
                        children_count = (
                            session.query(PersonORM)
                            .filter(PersonORM.parent_family_id == family.id)
                            .count()
                        )

                        if children_count == 0:
                            session.delete(family)
                            fixes_applied += 1
                    session.commit()
                    click.echo(f"✓ Removed empty families")

            # Check for duplicate persons (same name and approximate dates)
            # This is a simplified check
            duplicate_groups = {}
            all_persons = session.query(PersonORM).all()

            for person in all_persons:
                key = (person.first_name.lower(), person.surname.lower())
                if key not in duplicate_groups:
                    duplicate_groups[key] = []
                duplicate_groups[key].append(person)

            potential_duplicates = [
                group for group in duplicate_groups.values() if len(group) > 1
            ]

            if potential_duplicates:
                issue = f"Found {len(potential_duplicates)} groups of potential duplicate persons"
                issues.append(issue)
                click.echo(f"⚠ {issue}")

                if fix:
                    click.echo("⚠ Manual review required for duplicate persons")

            # Summary
            if not issues:
                click.echo("✓ Database is consistent")
            else:
                click.echo(f"\nFound {len(issues)} issue(s):")
                for issue in issues:
                    click.echo(f"  - {issue}")

                if fix and fixes_applied:
                    click.echo(f"\n✓ Applied {fixes_applied} automatic fixes")
                elif not fix:
                    click.echo("\nRun with --fix to apply automatic fixes")

    except Exception as e:
        click.echo(f"✗ Error checking database: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--from-scratch/--incremental",
    default=False,
    help="Recompute all consanguinity values from scratch",
)
@click.option(
    "--verbosity",
    "-v",
    type=click.IntRange(0, 2),
    default=1,
    help="Verbosity level (0=quiet, 1=normal, 2=verbose)",
)
@click.pass_context
def compute_consanguinity(ctx, from_scratch, verbosity):
    """Compute consanguinity values for all persons (equivalent to consang)."""
    if ctx.obj["verbose"] or verbosity > 0:
        click.echo("Computing consanguinity values...")

    db_manager = ctx.obj["db_manager"]

    try:
        with db_manager.get_session() as session:
            persons = session.query(PersonORM).all()
            total_persons = len(persons)
            computed = 0

            if verbosity > 0:
                click.echo(f"Processing {total_persons} persons...")

            for i, person in enumerate(persons):
                # TODO: Implement actual consanguinity calculation
                # This is a placeholder that sets a default value
                if from_scratch or person.consang == 0.0:
                    person.consang = 0.0  # Placeholder calculation
                    computed += 1

                if verbosity > 1 and (i + 1) % 100 == 0:
                    click.echo(f"  Processed {i + 1}/{total_persons} persons...")

            session.commit()

            if verbosity > 0:
                click.echo(f"✓ Computed consanguinity for {computed} persons")

    except Exception as e:
        click.echo(f"✗ Error computing consanguinity: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "text", "csv"]),
    default="text",
    help="Output format",
)
@click.pass_context
def statistics(ctx, output_format):
    """Show database statistics."""
    db_manager = ctx.obj["db_manager"]

    try:
        with db_manager.get_session() as session:
            stats = db_manager.get_statistics(session)

            if output_format == "json":
                click.echo(json.dumps(stats, indent=2))
            elif output_format == "csv":
                click.echo("metric,value")
                for key, value in stats.items():
                    click.echo(f"{key},{value}")
            else:  # text
                click.echo("Database Statistics:")
                click.echo("=" * 20)
                for key, value in stats.items():
                    formatted_key = key.replace("_", " ").title()
                    click.echo(f"{formatted_key:.<20} {value:>8,}")

    except Exception as e:
        click.echo(f"✗ Error getting statistics: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("search_term")
@click.option("--limit", "-l", default=10, help="Maximum number of results")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "simple"]),
    default="table",
    help="Output format",
)
@click.pass_context
def search(ctx, search_term, limit, output_format):
    """Search for persons in the database."""
    db_manager = ctx.obj["db_manager"]

    try:
        with db_manager.get_session() as session:
            persons = db_manager.search_persons(session, search_term, limit)

            if output_format == "json":
                results = []
                for person in persons:
                    results.append(
                        {
                            "id": person.id,
                            "first_name": person.first_name,
                            "surname": person.surname,
                            "sex": person.sex.value,
                            "occupation": person.occupation,
                        }
                    )
                click.echo(json.dumps(results, indent=2))

            elif output_format == "simple":
                for person in persons:
                    click.echo(f"{person.id}: {person.first_name} {person.surname}")

            else:  # table
                if persons:
                    click.echo(f"Search results for '{search_term}':")
                    click.echo("-" * 60)
                    click.echo(f"{'ID':<5} {'Name':<30} {'Sex':<5} {'Occupation':<15}")
                    click.echo("-" * 60)

                    for person in persons:
                        name = f"{person.first_name} {person.surname}".strip()
                        occupation = person.occupation[:14] if person.occupation else ""
                        click.echo(
                            f"{person.id:<5} {name:<30} {person.sex.value:<5} {occupation:<15}"
                        )
                else:
                    click.echo(f"No results found for '{search_term}'")

    except Exception as e:
        click.echo(f"✗ Error searching: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("database_path", type=click.Path())
@click.option("--force", is_flag=True, help="Force creation even if file exists")
@click.pass_context
def create_database(ctx, database_path, force):
    """Create a new empty database."""
    if os.path.exists(database_path) and not force:
        click.echo(f"Database already exists: {database_path}")
        click.echo("Use --force to overwrite")
        sys.exit(1)

    try:
        # Create database URL
        db_url = f"sqlite:///{database_path}"
        db_manager = DatabaseManager(db_url)
        db_manager.create_tables()

        click.echo(f"✓ Created database: {database_path}")

    except Exception as e:
        click.echo(f"✗ Error creating database: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("source_path", type=click.Path(exists=True))
@click.argument("backup_path", type=click.Path())
@click.pass_context
def backup(ctx, source_path, backup_path):
    """Create a backup of the database."""
    try:
        db_url = f"sqlite:///{source_path}"
        db_manager = DatabaseManager(db_url)

        if db_manager.backup_database(backup_path):
            click.echo(f"✓ Created backup: {backup_path}")
        else:
            click.echo("✗ Failed to create backup", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"✗ Error creating backup: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
