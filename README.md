# Cheat Sheet Generator

A tool to generate optimized cheat sheets from YAML hotkey definitions, designed for paper printing in black and white.

## Features

- Parse hotkey definitions from YAML files
- Generate optimized PDF cheat sheets for A4 or letter paper
- Support for sections and subsections
- Configurable layout (columns, font size, margins, orientation)
- Multi-row layouts (fill top half before bottom)
- Smart section breaks to prevent orphaned headers
- Multi-page support for large cheat sheets
- Command-line interface with validation

![Example](images/image.png)

`.pdf` version of image above is in the repo (`hotkeys.pdf`)

## Installation

### Option 1: Download Pre-built Executable

Download the latest executable for your platform from the [releases page](../../releases).

### Option 2: Build from Source

Requires [Python 3.10+](https://www.python.org/downloads/).

**Standard Python approach:**

Create and activate virtual environment (Linux/macOS):

```bash
python -m venv .venv && source .venv/bin/activate
```

Create and activate virtual environment (Windows):

```bash
python -m venv .venv && .venv\Scripts\activate
```

Install dependencies and build:

```bash
pip install -e ".[dev]" && python build_executable.py && deactivate
```

**Using [Poetry](https://python-poetry.org/):**

Install dependencies and build:

```bash
poetry install --all-extras
poetry run python build_executable.py
```

The executable will be created in the `dist/` directory.

## Usage

Run the executable or use the installed command:

```bash
cheatsheet-gen hotkeys.yaml
cheatsheet-gen hotkeys.yaml -o output.pdf -p letter -r portrait
```

### Command Line Options

```bash
cheatsheet-gen [OPTIONS] YAML_FILE

Options:
  -o, --output PATH          Output PDF file path
  -v, --validate            Only validate the YAML file
  -e, --estimate-pages      Estimate number of pages and exit
  -p, --paper-size TEXT     Paper size: letter or a4 (default: letter)
  -r, --orientation TEXT    Orientation: portrait or landscape (default: portrait)
  -t, --fill-top-half       Fill top half of page first (2-row layout)
  --help                    Show this message and exit
```

### Examples

```bash
# Generate PDF with custom output path
cheatsheet-gen hotkeys.yaml -o my_cheatsheet.pdf

# Validate YAML file without generating PDF
cheatsheet-gen hotkeys.yaml --validate

# Estimate how many pages the cheat sheet will have
cheatsheet-gen hotkeys.yaml --estimate-pages

# Generate US Letter in Portrait with 2-row layout
cheatsheet-gen hotkeys.yaml -p letter -r portrait -t
```

## YAML Format

The YAML file should follow this structure:

```yaml
title: "Your Cheat Sheet Title"

config:
  font_size: 7              # Base font size
  header_font_size: 9       # Header font size
  columns: 3                # Number of columns
  row_height: 10            # Height per hotkey row
  margin: 30                # Page margins in points
  section_spacing: 8        # Space between sections
  subsection_spacing: 4     # Space between subsections
  paper_size: letter        # letter or a4
  orientation: portrait     # portrait or landscape
  fill_top_half: true       # Fill top half before bottom (2-row layout)
  section_align_flush: true # Remove spacing at top of columns
  section_no_awkward_breaks: true  # Prevent orphaned headers

sections:
  Section Name:
    Subsection Name:
      "hotkey": "description"
      "another-key": "what it does"

    # Direct hotkeys under section (no subsection)
    "direct-key": "direct description"

  Another Section:
    "key": "description"
```

### Example YAML Structure

```yaml
title: "Vim Cheat Sheet"

config:
  columns: 3
  paper_size: letter
  orientation: portrait

sections:
  Movement:
    Basic:
      "h j k l": "Left/down/up/right"
      "w b": "Next/previous word"

    "gg G": "First/last line"

  Editing:
    "i a": "Insert before/after cursor"
    "o O": "New line below/above"
```

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `font_size` | 7 | Base font size for hotkey descriptions |
| `header_font_size` | 10 | Font size for section headers |
| `columns` | 5 | Number of columns per page |
| `row_height` | 11 | Height per hotkey row in points |
| `margin` | 25 | Page margins in points |
| `section_spacing` | 8 | Space between sections |
| `subsection_spacing` | 4 | Space between subsections |
| `paper_size` | `letter` | Paper size: `letter` or `a4` |
| `orientation` | `portrait` | Page orientation: `portrait` or `landscape` |
| `fill_top_half` | `false` | Fill top half before bottom (2-row layout) |
| `section_align_flush` | `true` | Remove spacing at top of columns |
| `section_no_awkward_breaks` | `true` | Prevent orphaned headers |

## Sample Hotkeys Included

The included `hotkeys.yaml` file contains comprehensive hotkey references for:

- **Tmux**: Session, window, and pane management
- **AstroVim**: Navigation, file operations, LSP features, Neo-tree
- **Git**: Basic commands, branching, history, stashing
- **Windows**: Window management, virtual desktops, file explorer
- **Linux Terminal**: Navigation, file operations, text processing
- **Vim Motions**: Movement, text objects, editing commands

## Development

### Setup

**Standard Python approach:**

Activate virtual environment and install development dependencies:

```bash
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

**Using [uv](https://docs.astral.sh/uv/):**

Install dependencies and setup pre-commit:

```bash
uv sync --all-extras
source .venv/bin/activate
pre-commit install
```

If preferred, you can use `uv run` instead of activating:
- `uv run pre-commit install`
- `uv run pytest`
- `uv run black src tests`

**Using [Poetry](https://python-poetry.org/):**

Install dependencies and setup pre-commit:

```bash
poetry install --all-extras
poetry shell
pre-commit install
```

If preferred, you can use `poetry run` instead of activating:
- `poetry run pre-commit install`
- `poetry run pytest`
- `poetry run black src tests`

### Running Tests

Run tests:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=src/cheatsheet_generator --cov-report=html
```

### Code Formatting and Linting

Format code:

```bash
black src tests
```

Sort imports:

```bash
isort src tests
```

Lint code:

```bash
flake8 src tests
```

Run all checks:

```bash
pre-commit run --all-files
```

### Building Executables

Build standalone executable:

```bash
python build_executable.py
```

### CI/CD

The project includes GitHub Actions workflows for testing and building executables for Linux, Windows, and macOS. Releases are created automatically when tags are pushed.

## Project Structure

```
cheatsheet_generator/
├── src/cheatsheet_generator/
│   ├── __init__.py
│   ├── models.py          # Data models
│   ├── parser.py          # YAML parser
│   ├── generator.py       # PDF generator
│   └── cli.py             # Command line interface
├── tests/
│   ├── test_models.py
│   ├── test_parser.py
│   ├── test_generator.py
│   └── test_cli.py
├── hotkeys.yaml           # Sample hotkey definitions
├── pyproject.toml         # Poetry configuration
├── poetry.lock            # Dependency lock file
└── README.md
```

## Dependencies

- [PyYAML](https://pyyaml.org/): YAML parsing
- [ReportLab](https://www.reportlab.com/): PDF generation
- [Click](https://click.palletsprojects.com/): Command line interface
- [Pillow](https://python-pillow.org/): Image processing support

## Testing

The project includes comprehensive test coverage for:

- Data models validation
- YAML parsing and validation
- PDF generation functionality
- Command line interface
- Error handling and edge cases

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE).
