"""Java-style .properties file parser."""

from __future__ import annotations

from .models import ConfigEntry, ConfigFile


class PropertiesParseError(Exception):
    """Error raised when .properties parsing fails."""

    def __init__(self, message: str, line: int = 0, context: str = ""):
        self.line = line
        self.context = context
        super().__init__(f"Line {line}: {message}" + (f"\n  Context: {context}" if context else ""))


def parse_properties(content: str, source_file: str = "") -> ConfigFile:
    """Parse Java .properties format.

    Supports:
    - key=value and key:value syntax
    - Comments: # and !
    - Multi-line values with backslash continuation
    - Unicode escapes: \\uXXXX
    - Key separators: =, :, and whitespace

    Args:
        content: .properties format string
        source_file: Source file path for error reporting

    Returns:
        Parsed ConfigFile

    Raises:
        PropertiesParseError: If parsing fails
    """
    config = ConfigFile(format="properties", source_file=source_file)
    lines = content.split("\n")
    i = 0
    pending_comment = ""

    while i < len(lines):
        line = lines[i]
        i += 1

        # Skip empty lines
        stripped = line.strip()
        if not stripped:
            continue

        # Comment lines
        if stripped.startswith("#") or stripped.startswith("!"):
            pending_comment += stripped[1:].strip() + "\n"
            continue

        # Unescaped continuation (no backslash, just wrapped line)
        # Check if this line has a key separator
        has_separator = False
        for sep in ("=", ":"):
            if sep in stripped:
                has_separator = True
                break
        # Also check for whitespace separator (key value)
        if not has_separator:
            parts = stripped.split(None, 1)
            if len(parts) == 2 and not parts[0].startswith("#") and not parts[0].startswith("!"):
                has_separator = True
            elif len(parts) == 1 and not stripped.startswith("#") and not stripped.startswith("!"):
                # Standalone key with no value
                has_separator = True

        if not has_separator:
            # Continuation of previous value
            if config.globals.entries:
                last_entry = config.globals.entries[-1]
                last_entry.value += stripped
            continue

        # Parse key-value
        key, value = _parse_line(stripped)

        # Check for multi-line continuation
        while value.endswith("\\") and i < len(lines):
            value = value[:-1]  # Remove trailing backslash
            next_line = lines[i].strip()
            i += 1
            value += next_line

        # Decode Unicode escapes
        key = _decode_unicode(key)
        value = _decode_unicode(value)

        entry = ConfigEntry(
            key=key,
            value=value,
            line_number=i,
            comment=pending_comment.strip(),
        )
        pending_comment = ""
        config.globals.entries.append(entry)

    return config


def _parse_line(line: str) -> tuple[str, str]:
    """Parse a single key=value line."""
    # Try = separator first
    for sep in ("=", ":"):
        idx = line.find(sep)
        if idx != -1:
            key = line[:idx].strip()
            value = line[idx + 1 :].strip()
            return key, value

    # Try whitespace separator
    parts = line.split(None, 1)
    if len(parts) == 2:
        return parts[0], parts[1]

    # No separator found
    return line, ""


def _decode_unicode(text: str) -> str:
    """Decode \\uXXXX unicode escapes."""
    import re

    def replace_unicode(match: re.Match) -> str:
        code = int(match.group(1), 16)
        return chr(code)

    return re.sub(r"\\u([0-9a-fA-F]{4})", replace_unicode, text)


def serialize_properties(config: ConfigFile) -> str:
    """Serialize a ConfigFile back to .properties format."""
    lines: list[str] = []

    for entry in config.globals.entries:
        if entry.comment:
            lines.append(f"# {entry.comment}")
        lines.append(f"{entry.key}={entry.value}")

    for section in config.sections:
        if section.comment:
            lines.append(f"# {section.comment}")
        lines.append(f"# Section: {section.name}")
        for entry in section.entries:
            if entry.comment:
                lines.append(f"# {entry.comment}")
            lines.append(f"{entry.key}={entry.value}")

    return "\n".join(lines)
