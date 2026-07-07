"""Data models for configuration files."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConfigEntry:
    """A single key-value configuration entry."""

    key: str
    value: str
    line_number: int = 0
    comment: str = ""
    inline_comment: str = ""

    def __repr__(self) -> str:
        return f"ConfigEntry(key={self.key!r}, value={self.value!r})"

    def to_dict(self) -> dict[str, Any]:
        return {"key": self.key, "value": self.value, "line_number": self.line_number}


@dataclass
class ConfigSection:
    """A section in a configuration file (e.g., [section] in INI)."""

    name: str
    entries: list[ConfigEntry] = field(default_factory=list)
    comment: str = ""
    line_number: int = 0

    def __repr__(self) -> str:
        return f"ConfigSection(name={self.name!r}, entries={len(self.entries)})"

    def get(self, key: str, default: str | None = None) -> str | None:
        """Get value by key name."""
        for entry in self.entries:
            if entry.key == key:
                return entry.value
        return default

    def set(self, key: str, value: str) -> None:
        """Set or update a key-value pair."""
        for entry in self.entries:
            if entry.key == key:
                entry.value = value
                return
        self.entries.append(ConfigEntry(key=key, value=value))

    def has(self, key: str) -> bool:
        """Check if key exists."""
        return any(e.key == key for e in self.entries)

    def keys(self) -> list[str]:
        """Return all keys in this section."""
        return [e.key for e in self.entries]

    def to_dict(self) -> dict[str, str]:
        """Convert section to dictionary."""
        return {e.key: e.value for e in self.entries}


@dataclass
class ConfigFile:
    """A parsed configuration file with sections and entries."""

    format: str  # "ini", "properties", "env", "unknown"
    sections: list[ConfigSection] = field(default_factory=list)
    globals: ConfigSection = field(default_factory=lambda: ConfigSection(name=""))
    metadata: dict[str, Any] = field(default_factory=dict)
    source_file: str = ""

    def __repr__(self) -> str:
        return f"ConfigFile(format={self.format!r}, sections={len(self.sections)})"

    @property
    def all_sections(self) -> list[ConfigSection]:
        """Return all sections including the global section."""
        result = []
        if self.globals.entries:
            result.append(self.globals)
        result.extend(self.sections)
        return result

    def get_section(self, name: str) -> ConfigSection | None:
        """Get section by name (case-insensitive for INI)."""
        name_lower = name.lower()
        if name == "" or name_lower == "":
            return self.globals
        for section in self.sections:
            if section.name.lower() == name_lower:
                return section
        return None

    def get(self, key: str, default: str | None = None) -> str | None:
        """Get value using dot notation (section.key or just key for globals)."""
        if "." in key:
            # First check if the key exists literally in globals
            result = self.globals.get(key, None)
            if result is not None:
                return result
            # Then try section.key interpretation
            section_name, entry_key = key.split(".", 1)
            section = self.get_section(section_name)
            if section:
                return section.get(entry_key, default)
            return default
        return self.globals.get(key, default)

    def set(self, key: str, value: str) -> None:
        """Set value using dot notation."""
        if "." in key:
            section_name, entry_key = key.split(".", 1)
            section = self.get_section(section_name)
            if not section:
                section = ConfigSection(name=section_name)
                self.sections.append(section)
            section.set(entry_key, value)
        else:
            self.globals.set(key, value)

    def has(self, key: str) -> bool:
        """Check if key exists using dot notation."""
        if "." in key:
            section_name, entry_key = key.split(".", 1)
            section = self.get_section(section_name)
            return section.has(entry_key) if section else False
        return self.globals.has(key)

    def keys(self) -> list[str]:
        """Return all keys with dot notation."""
        result = []
        for entry in self.globals.entries:
            result.append(entry.key)
        for section in self.sections:
            for entry in section.entries:
                result.append(f"{section.name}.{entry.key}")
        return result

    def to_dict(self) -> dict[str, Any]:
        """Convert to nested dictionary."""
        result: dict[str, Any] = {}
        for entry in self.globals.entries:
            result[entry.key] = entry.value
        for section in self.sections:
            result[section.name] = section.to_dict()
        return result

    def sections_dict(self) -> dict[str, dict[str, str]]:
        """Return all sections as nested dictionaries."""
        result: dict[str, dict[str, str]] = {}
        for section in self.sections:
            result[section.name] = section.to_dict()
        return result
