"""Hand-written INI parser with support for sections, comments, multi-line values, and interpolation."""

from __future__ import annotations

from .models import ConfigEntry, ConfigFile, ConfigSection


class IniParseError(Exception):
    """Error raised when INI parsing fails."""

    def __init__(self, message: str, line: int = 0, context: str = ""):
        self.line = line
        self.context = context
        super().__init__(f"Line {line}: {message}" + (f"\n  Context: {context}" if context else ""))


def parse_ini(content: str, source_file: str = "", interpolate: bool = True) -> ConfigFile:
    """Parse INI format configuration string.

    Supports:
    - Sections: [section_name]
    - Key-value pairs: key = value
    - Comments: # and ;
    - Multi-line values with continuation
    - Inline comments
    - Section and key-level comments
    - Variable interpolation: ${variable} or %(variable)s

    Args:
        content: INI format string
        source_file: Source file path for error reporting
        interpolate: Whether to resolve variable interpolation

    Returns:
        Parsed ConfigFile

    Raises:
        IniParseError: If parsing fails
    """
    config = ConfigFile(format="ini", source_file=source_file)
    current_section: ConfigSection | None = None
    lines = content.split("\n")
    i = 0
    pending_comment = ""

    while i < len(lines):
        line = lines[i]
        line_stripped = line.strip()
        i += 1

        # Check for multi-line continuation (indented line after key=value)
        if current_section is not None and current_section.entries and line_stripped:
            last_entry = current_section.entries[-1]
            is_continuation = (
                not line_stripped.startswith(("#", ";", "["))
                and "=" not in line_stripped
                and line.startswith((" ", "\t"))
            )
            if is_continuation:
                # This is a continuation line
                last_entry.value += line_stripped
                continue
        elif not current_section and config.globals.entries and line_stripped:
            last_entry = config.globals.entries[-1]
            is_continuation = (
                not line_stripped.startswith(("#", ";", "["))
                and "=" not in line_stripped
                and line.startswith((" ", "\t"))
            )
            if is_continuation:
                last_entry.value += line_stripped
                continue

        # Skip empty lines (but preserve pending comment)
        if not line_stripped:
            continue

        # Comment lines
        if line_stripped.startswith("#") or line_stripped.startswith(";"):
            pending_comment += line_stripped[1:].strip() + "\n"
            continue

        # Section header
        if line_stripped.startswith("["):
            # Find closing bracket
            close_idx = line_stripped.find("]")
            if close_idx == -1:
                raise IniParseError("Unclosed section header", line=i, context=line)

            section_name = line_stripped[1:close_idx].strip()
            inline_comment = _extract_inline_comment(line_stripped[close_idx + 1 :])

            current_section = ConfigSection(
                name=section_name,
                comment=pending_comment.strip(),
                line_number=i,
            )
            config.sections.append(current_section)
            pending_comment = ""
            continue

        # Key-value pair
        if "=" in line_stripped:
            key, value = line_stripped.split("=", 1)
            key = key.strip()
            value = value.strip()

            # Check for multi-line continuation
            while value.endswith("\\") and i < len(lines):
                value = value[:-1]  # Remove trailing backslash
                next_line = lines[i].strip()
                i += 1
                # Remove leading whitespace from continuation (but not trailing)
                value += next_line

            # Extract inline comment (only if value doesn't contain # or ; literally)
            inline_comment = _extract_inline_comment(value)
            if inline_comment:
                value = value[: -len(inline_comment)].strip()
                # Restore # or ; if it was part of the value
                if not inline_comment.startswith((" ", "\t")):
                    inline_comment = ""
                    # Re-parse: only strip trailing comments after whitespace
                    for idx in range(len(value) - 1, -1, -1):
                        if value[idx] in ("#", ";") and idx > 0 and value[idx - 1] in (" ", "\t"):
                            inline_comment = value[idx:].strip()
                            value = value[:idx].strip()
                            break

            entry = ConfigEntry(
                key=key,
                value=value,
                line_number=i,
                comment=pending_comment.strip(),
                inline_comment=inline_comment,
            )
            pending_comment = ""

            if current_section is not None:
                current_section.entries.append(entry)
            else:
                config.globals.entries.append(entry)
            continue

        # Standalone value (no key) — treat as continuation or ignore
        pending_comment += line_stripped + "\n"

    # Apply variable interpolation
    if interpolate:
        _interpolate_config(config)

    return config


def _extract_inline_comment(text: str) -> str:
    """Extract inline comment from the end of a line."""
    # Find # or ; that's preceded by whitespace
    for i in range(len(text) - 1, 1, -1):
        if text[i] in ("#", ";") and text[i - 1] in (" ", "\t"):
            return text[i:].strip()
    return ""


def _interpolate_config(config: ConfigFile) -> None:
    """Resolve ${variable} and %(variable)s interpolation."""
    # Build lookup from all entries
    flat: dict[str, str] = {}
    for entry in config.globals.entries:
        flat[entry.key] = entry.value
    for section in config.sections:
        for entry in section.entries:
            flat[f"{section.name}.{entry.key}"] = entry.value
            flat[entry.key] = entry.value  # Also allow unqualified names

    def resolve(value: str, depth: int = 0) -> str:
        if depth > 10:
            return value  # Prevent infinite recursion

        import re

        # ${variable} syntax
        result = value
        for match in re.finditer(r"\$\{([^}]+)\}", result):
            var_name = match.group(1)
            if var_name in flat:
                resolved = resolve(flat[var_name], depth + 1)
                result = result.replace(match.group(0), resolved)

        # %(variable)s syntax
        for match in re.finditer(r"%\(([^)]+)\)s", result):
            var_name = match.group(1)
            if var_name in flat:
                resolved = resolve(flat[var_name], depth + 1)
                result = result.replace(match.group(0), resolved)

        return result

    # Resolve all values
    for entry in config.globals.entries:
        entry.value = resolve(entry.value)
    for section in config.sections:
        for entry in section.entries:
            entry.value = resolve(entry.value)


def serialize_ini(config: ConfigFile) -> str:
    """Serialize a ConfigFile back to INI format."""
    lines: list[str] = []

    # Global entries
    for entry in config.globals.entries:
        line = f"{entry.key} = {entry.value}"
        if entry.inline_comment:
            line += f"  # {entry.inline_comment}"
        lines.append(line)

    if config.globals.entries:
        lines.append("")

    # Sections
    for section in config.sections:
        if section.comment:
            lines.append(f"# {section.comment}")
        lines.append(f"[{section.name}]")
        for entry in section.entries:
            line = f"{entry.key} = {entry.value}"
            if entry.inline_comment:
                line += f"  # {entry.inline_comment}"
            lines.append(line)
        lines.append("")

    return "\n".join(lines)
