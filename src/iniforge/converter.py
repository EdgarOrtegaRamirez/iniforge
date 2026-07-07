"""Format conversion between configuration file types."""

from __future__ import annotations

import json

from .env_parser import serialize_env
from .ini_parser import serialize_ini
from .models import ConfigFile
from .properties_parser import serialize_properties


def convert_config(
    config: ConfigFile,
    target_format: str,
) -> str:
    """Convert a configuration file to a different format.

    Supported formats:
    - "ini": INI format with [sections]
    - "properties": Java .properties format
    - "env": Docker .env format
    - "json": JSON format
    - "yaml": YAML format (basic)
    - "toml": TOML format (basic)

    Args:
        config: Parsed configuration file
        target_format: Target format name

    Returns:
        Serialized string in target format

    Raises:
        ValueError: If target format is not supported
    """
    target = target_format.lower().strip()

    if target == "ini":
        return serialize_ini(config)
    elif target == "properties":
        return serialize_properties(config)
    elif target == "env":
        return serialize_env(config)
    elif target == "json":
        return _to_json(config)
    elif target == "yaml":
        return _to_yaml(config)
    elif target == "toml":
        return _to_toml(config)
    else:
        raise ValueError(f"Unsupported target format: {target_format}")


def detect_format(content: str) -> str:
    """Detect the format of a configuration string.

    Args:
        content: Configuration string

    Returns:
        Detected format name
    """
    stripped = content.strip()

    # Check for JSON
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            json.loads(stripped)
            return "json"
        except json.JSONDecodeError:
            pass

    # Check for INI (has [section] headers)
    for line in stripped.split("\n"):
        line = line.strip()
        if line.startswith("[") and "]" in line:
            return "ini"

    # Check for key=value format (env or properties)
    has_key_value = False
    has_dotted_key = False
    has_bang_comment = False

    for line in stripped.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            # Check for ! comment (Java properties style)
            if line.lstrip().startswith("!"):
                has_bang_comment = True
            continue
        if line.startswith("!"):
            has_bang_comment = True
            continue
        if "=" in line:
            has_key_value = True
            # Check for dotted keys (Java properties style)
            key = line.split("=", 1)[0].strip()
            if "." in key:
                has_dotted_key = True

    if has_key_value:
        # Java properties: uses ! comments or dotted keys (e.g., app.name=value)
        if has_bang_comment or has_dotted_key:
            return "properties"
        return "env"

    return "unknown"


def _to_json(config: ConfigFile) -> str:
    """Convert to JSON format."""
    return json.dumps(config.to_dict(), indent=2, ensure_ascii=False)


def _to_yaml(config: ConfigFile) -> str:
    """Convert to basic YAML format (no external dependencies)."""
    lines = []
    _dict_to_yaml(config.to_dict(), lines, indent=0)
    return "\n".join(lines)


def _dict_to_yaml(data: dict, lines: list[str], indent: int = 0) -> None:
    """Recursively convert dict to YAML lines."""
    prefix = "  " * indent
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            _dict_to_yaml(value, lines, indent + 1)
        elif isinstance(value, str):
            # Quote if contains special characters
            if any(c in value for c in (":", "#", "\n", "'", '"')):
                escaped = value.replace("\\", "\\\\").replace('"', '\\"')
                lines.append(f'{prefix}{key}: "{escaped}"')
            else:
                lines.append(f"{prefix}{key}: {value}")
        else:
            lines.append(f"{prefix}{key}: {value}")


def _to_toml(config: ConfigFile) -> str:
    """Convert to basic TOML format (no external dependencies)."""
    lines = []

    # Global entries
    for entry in config.globals.entries:
        lines.append(f"{entry.key} = {_toml_value(entry.value)}")

    if config.globals.entries:
        lines.append("")

    # Sections
    for section in config.sections:
        lines.append(f"[{section.name}]")
        for entry in section.entries:
            lines.append(f"{entry.key} = {_toml_value(entry.value)}")
        lines.append("")

    return "\n".join(lines)


def _toml_value(value: str) -> str:
    """Format a value for TOML output."""
    # Try to detect types
    if value.lower() in ("true", "false"):
        return value.lower()
    try:
        int(value)
        return value
    except ValueError:
        pass
    try:
        float(value)
        return value
    except ValueError:
        pass
    # String — quote it
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
