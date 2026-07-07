# AGENTS.md — Guide for AI Agents

## Project Overview

IniForge is a configuration file processing toolkit in Python. It provides:
- Hand-written parsers for INI, .properties, and .env formats
- Dot-notation query engine
- Structural diff engine
- Multi-strategy merge engine
- Format conversion (INI ↔ JSON ↔ YAML ↔ TOML)
- Validation with schema support

## Tech Stack

- **Language**: Python 3.10+
- **Build**: Hatchling
- **Testing**: pytest
- **Linting**: ruff
- **CI**: GitHub Actions
- **Dependencies**: Zero (stdlib only)

## Project Structure

```
src/iniforge/
├── __init__.py          # Package exports
├── models.py            # ConfigFile, ConfigSection, ConfigEntry
├── ini_parser.py        # Hand-written INI parser (recursive descent)
├── properties_parser.py # Java .properties parser
├── env_parser.py        # Docker .env parser
├── query.py             # Dot-notation query engine
├── diff.py              # Structural diff engine
├── merge.py             # Multi-strategy merge engine
├── converter.py         # Format conversion
├── validator.py         # Validation engine
└── cli.py               # CLI interface (argparse)
```

## Development Commands

```bash
# Install in development mode
pip install -e ".[dev]"

# Run all tests
pytest tests/ -v

# Lint code
ruff check src/ tests/

# Format code
ruff format src/ tests/
```

## Key Algorithms

- **INI Parser**: Line-by-line state machine with section tracking, multi-line continuation, and variable interpolation (${var} and %(var)s)
- **Diff Engine**: Dictionary-based comparison with section-level tracking, change classification (added/removed/modified)
- **Merge Engine**: Entry-level merge with 4 strategies (override, keep, union, deep)
- **Validator**: Rule-based validation with severity scoring (0-100)

## Common Tasks

### Adding a new parser format

1. Create `src/iniforge/<format>_parser.py`
2. Implement `parse_<format>(content: str, source_file: str) -> ConfigFile`
3. Add to converter.py's `detect_format()` and `convert_config()`
4. Add CLI support in cli.py
5. Add tests in `tests/test_<format>_parser.py`

### Adding a new validation rule

1. Add a `_check_<rule>()` function in `validator.py`
2. Register it in `validate_config()`'s check_rules list
3. Add tests in `tests/test_validator.py`

### Adding a new merge strategy

1. Add to `MergeStrategy` enum in `merge.py`
2. Implement in `_merge_section()` function
3. Add tests in `tests/test_merge.py`

## Dependencies

None — uses only Python stdlib.

## Testing Approach

- Unit tests for each parser (INI, properties, env)
- Unit tests for each engine (query, diff, merge, validator)
- CLI integration tests
- Roundtrip tests (parse → serialize → parse)
