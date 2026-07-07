"""Configuration file merge engine with multiple strategies."""

from __future__ import annotations

from enum import Enum

from .models import ConfigEntry, ConfigFile, ConfigSection


class MergeStrategy(str, Enum):
    """Strategy for merging conflicting values."""

    OVERRIDE = "override"  # Second value wins
    KEEP_ORIGINAL = "keep"  # First value wins
    UNION = "union"  # Merge all unique values (comma-separated)
    DEEP = "deep"  # Deep merge sections


def merge_configs(
    config1: ConfigFile,
    config2: ConfigFile,
    strategy: MergeStrategy = MergeStrategy.OVERRIDE,
) -> ConfigFile:
    """Merge two configuration files.

    Args:
        config1: Base configuration
        config2: Override configuration
        strategy: Merge strategy for conflicts

    Returns:
        New merged ConfigFile
    """
    result = ConfigFile(
        format=config1.format,
        source_file=config1.source_file,
    )

    # Merge globals
    result.globals = _merge_section(config1.globals, config2.globals, strategy)

    # Merge sections
    sections1 = {s.name: s for s in config1.sections}
    sections2 = {s.name: s for s in config2.sections}

    all_section_names = []
    seen = set()
    for s in config1.sections + config2.sections:
        if s.name not in seen:
            all_section_names.append(s.name)
            seen.add(s.name)

    for section_name in all_section_names:
        sec1 = sections1.get(section_name)
        sec2 = sections2.get(section_name)

        if sec1 is None:
            # Only in config2
            result.sections.append(
                ConfigSection(
                    name=section_name,
                    entries=list(sec2.entries),
                    comment=sec2.comment,
                )
            )
        elif sec2 is None:
            # Only in config1
            result.sections.append(
                ConfigSection(
                    name=section_name,
                    entries=list(sec1.entries),
                    comment=sec1.comment,
                )
            )
        else:
            # In both — merge
            merged = _merge_section(sec1, sec2, strategy)
            merged.name = section_name
            result.sections.append(merged)

    return result


def _merge_section(
    section1: ConfigSection,
    section2: ConfigSection,
    strategy: MergeStrategy,
) -> ConfigSection:
    """Merge two sections."""
    result = ConfigSection(name=section1.name)

    # Build entry maps
    entries1 = {e.key: e for e in section1.entries}
    entries2 = {e.key: e for e in section2.entries}

    all_keys = list(dict.fromkeys(list(entries1.keys()) + list(entries2.keys())))

    for key in all_keys:
        e1 = entries1.get(key)
        e2 = entries2.get(key)

        if e1 is None:
            # Only in section2
            result.entries.append(
                ConfigEntry(
                    key=key,
                    value=e2.value,
                    line_number=e2.line_number,
                    comment=e2.comment,
                )
            )
        elif e2 is None:
            # Only in section1
            result.entries.append(
                ConfigEntry(
                    key=key,
                    value=e1.value,
                    line_number=e1.line_number,
                    comment=e1.comment,
                )
            )
        else:
            # In both — apply strategy
            if strategy == MergeStrategy.OVERRIDE:
                result.entries.append(
                    ConfigEntry(
                        key=key,
                        value=e2.value,
                        line_number=e2.line_number,
                        comment=e2.comment or e1.comment,
                    )
                )
            elif strategy == MergeStrategy.KEEP_ORIGINAL:
                result.entries.append(
                    ConfigEntry(
                        key=key,
                        value=e1.value,
                        line_number=e1.line_number,
                        comment=e1.comment,
                    )
                )
            elif strategy == MergeStrategy.UNION:
                # Combine unique values
                vals1 = set(e1.value.split(","))
                vals2 = set(e2.value.split(","))
                combined = vals1 | vals2
                result.entries.append(
                    ConfigEntry(
                        key=key,
                        value=",".join(sorted(combined)),
                        line_number=e1.line_number,
                        comment=e1.comment,
                    )
                )
            elif strategy == MergeStrategy.DEEP:
                # For non-section entries, just override
                result.entries.append(
                    ConfigEntry(
                        key=key,
                        value=e2.value,
                        line_number=e2.line_number,
                        comment=e2.comment or e1.comment,
                    )
                )

    return result


def merge_files(
    files: list[ConfigFile],
    strategy: MergeStrategy = MergeStrategy.OVERRIDE,
) -> ConfigFile:
    """Merge multiple configuration files in order.

    Args:
        files: List of configuration files (later files override earlier ones)
        strategy: Merge strategy for conflicts

    Returns:
        New merged ConfigFile
    """
    if not files:
        return ConfigFile(format="unknown")

    result = files[0]
    for f in files[1:]:
        result = merge_configs(result, f, strategy)

    return result
