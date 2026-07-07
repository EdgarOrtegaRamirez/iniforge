"""Dot-notation query engine for configuration files."""

from __future__ import annotations

from typing import Any

from .models import ConfigFile


def query_config(config: ConfigFile, query: str) -> Any:
    """Query a configuration file using dot notation.

    Supports:
    - "key" — get global key
    - "section.key" — get key in section
    - "section.*" — get all keys in section
    - "*" — get all sections
    - "section" — get entire section
    - "key1,key2" — get multiple keys (comma-separated)
    - "key1:default" — get with default value

    Args:
        config: Parsed configuration file
        query: Dot-notation query string

    Returns:
        Query result (string, dict, list, or None)
    """
    query = query.strip()

    # Empty query returns full config
    if not query:
        return config.to_dict()

    # Multiple keys (comma-separated)
    if "," in query and "." not in query:
        keys = [k.strip() for k in query.split(",")]
        result = {}
        for key in keys:
            val = config.get(key)
            if val is not None:
                result[key] = val
        return result

    # Wildcard: get all sections
    if query == "*":
        result = {}
        for section in config.sections:
            result[section.name] = section.to_dict()
        return result

    # Wildcard: get all keys in section
    if query.endswith(".*"):
        section_name = query[:-2]
        section = config.get_section(section_name)
        if section:
            return section.to_dict()
        return None

    # Default value syntax: key:default
    if ":" in query and "." not in query.split(":")[0]:
        key, default = query.split(":", 1)
        val = config.get(key.strip())
        return val if val is not None else default

    # Simple key lookup
    val = config.get(query)
    if val is not None:
        return val

    # Check if it's a section name
    section = config.get_section(query)
    if section:
        return section.to_dict()

    return None


def list_keys(config: ConfigFile, pattern: str = "") -> list[str]:
    """List all keys, optionally filtered by pattern.

    Args:
        config: Parsed configuration file
        pattern: Optional glob-like pattern (supports * and ?)

    Returns:
        List of matching keys
    """
    import fnmatch

    all_keys = config.keys()

    if not pattern:
        return all_keys

    return [k for k in all_keys if fnmatch.fnmatch(k, pattern)]


def get_value(config: ConfigFile, key: str, default: str | None = None) -> str | None:
    """Get a single value with optional default.

    Args:
        config: Parsed configuration file
        key: Dot-notation key
        default: Default value if key not found

    Returns:
        Value or default
    """
    return config.get(key, default)


def get_section_keys(config: ConfigFile, section: str) -> list[str]:
    """Get all keys in a section.

    Args:
        config: Parsed configuration file
        section: Section name

    Returns:
        List of keys in the section
    """
    sec = config.get_section(section)
    if sec:
        return sec.keys()
    return []
