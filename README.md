# IniForge

Configuration File Processing Toolkit — parse, query, diff, merge, and convert INI, .properties, and .env files.

## Features

- **Multi-format parsing**: Hand-written parsers for INI, Java .properties, and Docker .env files
- **Dot-notation query**: Query config values using `section.key` syntax
- **Structural diff**: Compare two config files and see exactly what changed
- **Smart merge**: Multiple merge strategies (override, keep, union, deep)
- **Format conversion**: Convert between INI, .properties, .env, JSON, YAML, TOML
- **Validation**: Schema validation, security checks, health scoring
- **Zero dependencies**: Uses only Python stdlib
- **CLI + Library**: Usable both as command-line tool and Python library

## Quick Start

### Install

```bash
pip install iniforge
```

### Parse a config file

```bash
# Auto-detect format
iniforge parse config.ini

# Output as JSON
iniforge parse config.ini --json

# Show sections only
iniforge parse config.ini --sections
```

### Query values

```bash
# Get a specific value
iniforge query config.ini database.host

# Get all keys in a section
iniforge query config.ini "database.*"

# Get all sections
iniforge query config.ini "*"
```

### Diff two configs

```bash
# Compare two files
iniforge diff base.ini modified.ini

# Unified diff format
iniforge diff base.ini modified.ini --unified
```

### Merge configs

```bash
# Override strategy (default)
iniforge merge base.ini override.ini

# Keep original values
iniforge merge base.ini override.ini --strategy keep

# Union unique values
iniforge merge base.ini override.ini --strategy union
```

### Convert formats

```bash
# Convert INI to JSON
iniforge convert config.ini --to json

# Convert .env to YAML
iniforge convert .env --to yaml

# Save to file
iniforge convert config.ini --to json --output config.json
```

### Validate

```bash
# Basic validation
iniforge validate config.ini

# Output as JSON
iniforge validate config.ini --json
```

## Python API

```python
from iniforge import parse_ini, parse_env, query_config, diff_configs, merge_configs, convert_config

# Parse
config = parse_ini("[database]\nhost = localhost\nport = 5432")

# Query
host = query_config(config, "database.host")  # "localhost"
section = query_config(config, "database")    # {"host": "localhost", "port": "5432"}
all_sections = query_config(config, "*")      # All sections

# Diff
config1 = parse_ini("key1 = old")
config2 = parse_ini("key1 = new")
diff = diff_configs(config1, config2)
print(diff.summary)  # {"added": 0, "removed": 0, "modified": 1, "total": 1}

# Merge
config1 = parse_ini("[s]\nkey1 = old\nkey2 = keep")
config2 = parse_ini("[s]\nkey1 = new")
merged = merge_configs(config1, config2)
print(merged.get("s.key1"))  # "new"

# Convert
config = parse_ini("[s]\nkey = value")
json_str = convert_config(config, "json")
yaml_str = convert_config(config, "yaml")
```

## Supported Formats

| Format | Extensions | Description |
|--------|-----------|-------------|
| INI | `.ini`, `.cfg`, `.conf` | Standard INI with sections, comments, interpolation |
| Properties | `.properties` | Java-style key=value with # and ! comments |
| Env | `.env`, `.env.*` | Docker-style environment files |
| JSON | `.json` | JSON object format |
| YAML | `.yaml`, `.yml` | YAML format (output only) |
| TOML | `.toml` | TOML format (output only) |

## Architecture

```
iniforge/
├── src/iniforge/
│   ├── __init__.py          # Package exports
│   ├── models.py            # ConfigFile, ConfigSection, ConfigEntry
│   ├── ini_parser.py        # Hand-written INI parser
│   ├── properties_parser.py # Java .properties parser
│   ├── env_parser.py        # Docker .env parser
│   ├── query.py             # Dot-notation query engine
│   ├── diff.py              # Structural diff engine
│   ├── merge.py             # Multi-strategy merge engine
│   ├── converter.py         # Format conversion
│   ├── validator.py         # Validation engine
│   └── cli.py               # CLI interface
└── tests/
    ├── test_ini_parser.py
    ├── test_properties_parser.py
    ├── test_env_parser.py
    ├── test_query.py
    ├── test_diff.py
    ├── test_merge.py
    ├── test_converter.py
    ├── test_validator.py
    └── test_cli.py
```

## License

MIT
