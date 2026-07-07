"""Docker/docker-compose .env file parser."""

from __future__ import annotations

from .models import ConfigEntry, ConfigFile


class EnvParseError(Exception):
    """Error raised when .env parsing fails."""

    def __init__(self, message: str, line: int = 0, context: str = ""):
        self.line = line
        self.context = context
        super().__init__(f"Line {line}: {message}" + (f"\n  Context: {context}" if context else ""))


def parse_env(content: str, source_file: str = "") -> ConfigFile:
    """Parse .env format (Docker-style environment files).

    Supports:
    - KEY=value pairs
    - Comments: #
    - Quoted values: "value", 'value'
    - Multi-line values with quotes
    - Variable expansion: $VAR, ${VAR}
    - Export prefix: export KEY=value
    - Empty values: KEY= or KEY=""

    Args:
        content: .env format string
        source_file: Source file path for error reporting

    Returns:
        Parsed ConfigFile

    Raises:
        EnvParseError: If parsing fails
    """
    config = ConfigFile(format="env", source_file=source_file)
    lines = content.split("\n")
    i = 0
    pending_comment = ""
    current_key: str | None = None

    while i < len(lines):
        line = lines[i]
        i += 1

        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            if current_key:
                current_key = None
            continue

        # Comment lines
        if stripped.startswith("#"):
            pending_comment += stripped[1:].strip() + "\n"
            continue

        # Handle multi-line continuation (quoted value that spans lines)
        if current_key:
            # This line is a continuation of a multi-line value
            last_entry = config.globals.entries[-1]
            # Check if this line closes a quote
            if stripped.startswith(("'", '"')):
                quote_char = stripped[0]
                last_entry.value += "\n" + stripped[1:].rstrip(quote_char)
                current_key = None
            else:
                last_entry.value += "\n" + stripped
            continue

        # Remove export prefix if present
        if stripped.startswith("export "):
            stripped = stripped[7:].strip()

        # Parse key=value
        key, value = _parse_env_line(stripped)

        # Check if value starts a multi-line string
        if value.startswith(("'", '"')) and not value.endswith(value[0]):
            current_key = key
            # Start multi-line value (keep the opening quote)
            value = value[1:]

        # Expand variables
        value = _expand_variables(value, config)

        entry = ConfigEntry(
            key=key,
            value=value,
            line_number=i,
            comment=pending_comment.strip(),
        )
        pending_comment = ""
        config.globals.entries.append(entry)

    return config


def _parse_env_line(line: str) -> tuple[str, str]:
    """Parse a single KEY=value line."""
    # Find the first = sign
    idx = line.find("=")
    if idx == -1:
        return line, ""

    key = line[:idx].strip()
    value = line[idx + 1 :].strip()

    # Handle quoted values
    if len(value) >= 2 and (
        (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'"))
    ):
        value = value[1:-1]

    return key, value


def _expand_variables(value: str, config: ConfigFile) -> str:
    """Expand $VAR and ${VAR} references."""
    import re

    # Build lookup from already-parsed entries
    flat: dict[str, str] = {}
    for entry in config.globals.entries:
        flat[entry.key] = entry.value

    def replace_var(match: re.Match) -> str:
        var_name = match.group(1) or match.group(2)
        return flat.get(var_name, match.group(0))  # Keep original if not found

    # ${VAR} syntax
    result = re.sub(r"\$\{([^}]+)\}", replace_var, value)
    # $VAR syntax (word characters only)
    result = re.sub(r"\$([A-Za-z_][A-Za-z0-9_]*)", replace_var, result)

    return result


def serialize_env(config: ConfigFile) -> str:
    """Serialize a ConfigFile back to .env format."""
    lines: list[str] = []

    for entry in config.globals.entries:
        if entry.comment:
            lines.append(f"# {entry.comment}")
        if " " in entry.value or "\n" in entry.value:
            # Quote values with spaces or newlines
            lines.append(f'{entry.key}="{entry.value}"')
        else:
            lines.append(f"{entry.key}={entry.value}")

    for section in config.sections:
        if section.comment:
            lines.append(f"\n# {section.comment}")
        lines.append(f"# --- {section.name} ---")
        for entry in section.entries:
            if entry.comment:
                lines.append(f"# {entry.comment}")
            if " " in entry.value or "\n" in entry.value:
                lines.append(f'{entry.key}="{entry.value}"')
            else:
                lines.append(f"{entry.key}={entry.value}")

    return "\n".join(lines)
