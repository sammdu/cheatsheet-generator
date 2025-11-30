"""Command line interface for cheat sheet generator."""

import sys
from pathlib import Path

import click

from cheatsheet_generator.generator import PDFGenerator
from cheatsheet_generator.parser import YAMLParser


@click.command()
@click.argument("yaml_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output PDF file path (default: same name as input with .pdf extension)",
)
@click.option(
    "--validate",
    "-v",
    is_flag=True,
    help="Only validate the YAML file without generating PDF",
)
@click.option(
    "--estimate-pages", "-e", is_flag=True, help="Estimate number of pages and exit"
)
@click.option(
    "--paper-size",
    "-p",
    type=click.Choice(["letter", "a4"], case_sensitive=False),
    help="Paper size (default: letter)",
)
@click.option(
    "--orientation",
    "-r",
    type=click.Choice(["portrait", "landscape"], case_sensitive=False),
    help="Page orientation (default: portrait)",
)
@click.option(
    "--fill-top-half",
    "-t",
    is_flag=True,
    help="Fill top half of page first (2-row layout)",
)
def main(
    yaml_file: Path,
    output: Path,
    validate: bool,
    estimate_pages: bool,
    paper_size: str,
    orientation: str,
    fill_top_half: bool,
):
    """Generate a cheat sheet PDF from a YAML hotkey definition file.

    YAML_FILE: Path to the YAML file containing hotkey definitions.
    """
    try:
        errors = YAMLParser.validate_yaml(yaml_file)
        if errors:
            click.echo("YAML validation errors:", err=True)
            for error in errors:
                click.echo(f"  - {error}", err=True)
            sys.exit(1)

        if validate:
            click.echo("✓ YAML file is valid")
            return

        cheat_sheet = YAMLParser.parse_file(yaml_file)

        # Override config with CLI parameters if provided
        if paper_size:
            cheat_sheet.config.paper_size = paper_size.lower()
        if orientation:
            cheat_sheet.config.orientation = orientation.lower()
        if fill_top_half:
            cheat_sheet.config.fill_top_half = True

        click.echo(f"Parsed {len(cheat_sheet.hotkeys)} hotkeys from {yaml_file}")

        if estimate_pages:
            generator = PDFGenerator(cheat_sheet)
            pages = generator.estimate_pages()
            click.echo(f"Estimated pages: {pages}")
            return

        if output is None:
            output = yaml_file.with_suffix(".pdf")

        generator = PDFGenerator(cheat_sheet)
        generator.generate(output)

        pages = generator.estimate_pages()
        click.echo(f"✓ Generated cheat sheet: {output}")
        click.echo(f"  - Title: {cheat_sheet.title}")
        click.echo(f"  - Hotkeys: {len(cheat_sheet.hotkeys)}")
        click.echo(f"  - Estimated pages: {pages}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
