"""Configuration file diff engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .models import ConfigFile


class ChangeType(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"


@dataclass
class ConfigChange:
    """A single change between two configuration files."""

    path: str
    change_type: ChangeType
    old_value: str | None = None
    new_value: str | None = None

    def __repr__(self) -> str:
        if self.change_type == ChangeType.ADDED:
            return f"+ {self.path} = {self.new_value}"
        elif self.change_type == ChangeType.REMOVED:
            return f"- {self.path} = {self.old_value}"
        else:
            return f"~ {self.path}: {self.old_value} -> {self.new_value}"


@dataclass
class DiffResult:
    """Result of comparing two configuration files."""

    changes: list[ConfigChange] = field(default_factory=list)
    identical: bool = True
    summary: dict[str, int] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"DiffResult(changes={len(self.changes)}, identical={self.identical})"

    @property
    def added(self) -> list[ConfigChange]:
        return [c for c in self.changes if c.change_type == ChangeType.ADDED]

    @property
    def removed(self) -> list[ConfigChange]:
        return [c for c in self.changes if c.change_type == ChangeType.REMOVED]

    @property
    def modified(self) -> list[ConfigChange]:
        return [c for c in self.changes if c.change_type == ChangeType.MODIFIED]


def diff_configs(config1: ConfigFile, config2: ConfigFile, ignore_order: bool = True) -> DiffResult:
    """Compare two configuration files and return differences.

    Compares globals and sections separately to avoid double-counting.

    Args:
        config1: First configuration (base)
        config2: Second configuration (changed)
        ignore_order: Whether to ignore entry order within sections

    Returns:
        DiffResult with all changes
    """
    result = DiffResult()

    # Compare global entries
    globals1 = {e.key: e.value for e in config1.globals.entries}
    globals2 = {e.key: e.value for e in config2.globals.entries}
    _diff_flat(globals1, globals2, "", result)

    # Compare sections
    sections1 = {s.name: s for s in config1.sections}
    sections2 = {s.name: s for s in config2.sections}

    all_section_names = set(list(sections1.keys()) + list(sections2.keys()))

    for section_name in sorted(all_section_names):
        if section_name not in sections1:
            # Entire section added
            section = sections2[section_name]
            for entry in section.entries:
                result.changes.append(
                    ConfigChange(
                        path=f"{section_name}.{entry.key}",
                        change_type=ChangeType.ADDED,
                        new_value=entry.value,
                    )
                )
        elif section_name not in sections2:
            # Entire section removed
            section = sections1[section_name]
            for entry in section.entries:
                result.changes.append(
                    ConfigChange(
                        path=f"{section_name}.{entry.key}",
                        change_type=ChangeType.REMOVED,
                        old_value=entry.value,
                    )
                )
        else:
            # Both sections exist — compare entries
            sec1 = sections1[section_name]
            sec2 = sections2[section_name]
            dict1 = {e.key: e.value for e in sec1.entries}
            dict2 = {e.key: e.value for e in sec2.entries}
            _diff_flat(dict1, dict2, section_name, result)

    result.identical = len(result.changes) == 0
    result.summary = {
        "added": len(result.added),
        "removed": len(result.removed),
        "modified": len(result.modified),
        "total": len(result.changes),
    }

    return result


def _diff_flat(
    dict1: dict[str, str],
    dict2: dict[str, str],
    prefix: str,
    result: DiffResult,
) -> None:
    """Compare two flat dictionaries."""
    all_keys = set(dict1.keys()) | set(dict2.keys())

    for key in sorted(all_keys):
        path = f"{prefix}.{key}" if prefix else key

        if key not in dict1:
            result.changes.append(
                ConfigChange(
                    path=path,
                    change_type=ChangeType.ADDED,
                    new_value=dict2[key],
                )
            )
        elif key not in dict2:
            result.changes.append(
                ConfigChange(
                    path=path,
                    change_type=ChangeType.REMOVED,
                    old_value=dict1[key],
                )
            )
        elif dict1[key] != dict2[key]:
            result.changes.append(
                ConfigChange(
                    path=path,
                    change_type=ChangeType.MODIFIED,
                    old_value=dict1[key],
                    new_value=dict2[key],
                )
            )


def format_diff_text(result: DiffResult) -> str:
    """Format diff result as readable text."""
    if result.identical:
        return "No differences found."

    lines = []
    lines.append(f"Found {result.summary['total']} change(s):")
    lines.append(f"  Added: {result.summary['added']}")
    lines.append(f"  Removed: {result.summary['removed']}")
    lines.append(f"  Modified: {result.summary['modified']}")
    lines.append("")

    for change in result.changes:
        lines.append(str(change))

    return "\n".join(lines)


def format_diff_unified(result: DiffResult, context: int = 0) -> str:
    """Format diff result in unified diff style."""
    if result.identical:
        return ""

    lines = []
    lines.append("--- base")
    lines.append("+++ modified")

    for change in result.changes:
        if change.change_type == ChangeType.ADDED:
            lines.append(f"+{change.path} = {change.new_value}")
        elif change.change_type == ChangeType.REMOVED:
            lines.append(f"-{change.path} = {change.old_value}")
        elif change.change_type == ChangeType.MODIFIED:
            lines.append(f"-{change.path} = {change.old_value}")
            lines.append(f"+{change.path} = {change.new_value}")

    return "\n".join(lines)
