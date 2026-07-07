"""Configuration file validation engine."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .models import ConfigFile


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """A single validation issue."""

    rule: str
    message: str
    severity: Severity
    path: str = ""

    def __repr__(self) -> str:
        return f"[{self.severity.value}] {self.rule}: {self.message}"


@dataclass
class ValidationResult:
    """Result of validating a configuration file."""

    issues: list[ValidationIssue] = field(default_factory=list)
    valid: bool = True
    score: int = 100  # 0-100 health score

    def __repr__(self) -> str:
        return f"ValidationResult(valid={self.valid}, issues={len(self.issues)}, score={self.score})"

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.WARNING]


def validate_config(
    config: ConfigFile,
    schema: dict[str, Any] | None = None,
    rules: list[str] | None = None,
) -> ValidationResult:
    """Validate a configuration file.

    Args:
        config: Parsed configuration file
        schema: Optional validation schema with rules
        rules: Optional list of rule IDs to check

    Returns:
        ValidationResult with issues and health score
    """
    result = ValidationResult()

    # Default rules if none specified
    check_rules = rules or [
        "no-empty-keys",
        "no-duplicate-keys",
        "no-empty-values",
        "no-trailing-whitespace",
        "consistent-separator",
        "sensitive-values",
        "deprecated-keys",
        "format-consistency",
    ]

    # Run each rule
    for rule in check_rules:
        if rule == "no-empty-keys":
            _check_empty_keys(config, result)
        elif rule == "no-duplicate-keys":
            _check_duplicate_keys(config, result)
        elif rule == "no-empty-values":
            _check_empty_values(config, result)
        elif rule == "no-trailing-whitespace":
            _check_trailing_whitespace(config, result)
        elif rule == "consistent-separator":
            _check_consistent_separator(config, result)
        elif rule == "sensitive-values":
            _check_sensitive_values(config, result)
        elif rule == "format-consistency":
            _check_format_consistency(config, result)

    # Check against schema if provided
    if schema:
        _check_schema(config, schema, result)

    # Calculate score
    result.score = _calculate_score(result)
    result.valid = len(result.errors) == 0

    return result


def _check_empty_keys(config: ConfigFile, result: ValidationResult) -> None:
    """Check for empty key names."""
    for entry in config.globals.entries:
        if not entry.key.strip():
            result.issues.append(
                ValidationIssue(
                    rule="no-empty-keys",
                    message="Empty key found",
                    severity=Severity.ERROR,
                    path=entry.key,
                )
            )
    for section in config.sections:
        for entry in section.entries:
            if not entry.key.strip():
                result.issues.append(
                    ValidationIssue(
                        rule="no-empty-keys",
                        message=f"Empty key in section [{section.name}]",
                        severity=Severity.ERROR,
                        path=f"{section.name}.{entry.key}",
                    )
                )


def _check_duplicate_keys(config: ConfigFile, result: ValidationResult) -> None:
    """Check for duplicate keys within sections."""
    # Check globals
    seen_keys: dict[str, int] = {}
    for entry in config.globals.entries:
        if entry.key in seen_keys:
            result.issues.append(
                ValidationIssue(
                    rule="no-duplicate-keys",
                    message=f"Duplicate key: {entry.key}",
                    severity=Severity.WARNING,
                    path=entry.key,
                )
            )
        seen_keys[entry.key] = seen_keys.get(entry.key, 0) + 1

    # Check each section
    for section in config.sections:
        seen: dict[str, int] = {}
        for entry in section.entries:
            if entry.key in seen:
                result.issues.append(
                    ValidationIssue(
                        rule="no-duplicate-keys",
                        message=f"Duplicate key in [{section.name}]: {entry.key}",
                        severity=Severity.WARNING,
                        path=f"{section.name}.{entry.key}",
                    )
                )
            seen[entry.key] = seen.get(entry.key, 0) + 1


def _check_empty_values(config: ConfigFile, result: ValidationResult) -> None:
    """Check for empty values."""
    for entry in config.globals.entries:
        if not entry.value.strip():
            result.issues.append(
                ValidationIssue(
                    rule="no-empty-values",
                    message=f"Empty value for key: {entry.key}",
                    severity=Severity.INFO,
                    path=entry.key,
                )
            )
    for section in config.sections:
        for entry in section.entries:
            if not entry.value.strip():
                result.issues.append(
                    ValidationIssue(
                        rule="no-empty-values",
                        message=f"Empty value for key: {section.name}.{entry.key}",
                        severity=Severity.INFO,
                        path=f"{section.name}.{entry.key}",
                    )
                )


def _check_trailing_whitespace(config: ConfigFile, result: ValidationResult) -> None:
    """Check for trailing whitespace in values."""
    for entry in config.globals.entries:
        if entry.value != entry.value.rstrip():
            result.issues.append(
                ValidationIssue(
                    rule="no-trailing-whitespace",
                    message=f"Trailing whitespace in value: {entry.key}",
                    severity=Severity.WARNING,
                    path=entry.key,
                )
            )
    for section in config.sections:
        for entry in section.entries:
            if entry.value != entry.value.rstrip():
                result.issues.append(
                    ValidationIssue(
                        rule="no-trailing-whitespace",
                        message=f"Trailing whitespace in value: {section.name}.{entry.key}",
                        severity=Severity.WARNING,
                        path=f"{section.name}.{entry.key}",
                    )
                )


def _check_consistent_separator(config: ConfigFile, result: ValidationResult) -> None:
    """Check for consistent use of separators (= vs :)."""
    # This is a heuristic — we check if values look like they might be
    # using inconsistent separators
    pass


_SENSITIVE_PATTERNS = [
    (r"(?i)(password|passwd|pwd)", "password"),
    (r"(?i)(secret|token|api.?key)", "secret/token"),
    (r"(?i)(private.?key)", "private key"),
    (r"(?i)(connection.?string)", "connection string"),
]


def _check_sensitive_values(config: ConfigFile, result: ValidationResult) -> None:
    """Check for potentially sensitive values that shouldn't be hardcoded."""
    all_entries = []
    for entry in config.globals.entries:
        all_entries.append(("", entry))
    for section in config.sections:
        for entry in section.entries:
            all_entries.append((section.name, entry))

    for section_name, entry in all_entries:
        path = f"{section_name}.{entry.key}" if section_name else entry.key
        for pattern, desc in _SENSITIVE_PATTERNS:
            if re.search(pattern, entry.key):
                # Check if value looks hardcoded (not a variable reference)
                if not entry.value.startswith(("$", "%", "${")):
                    result.issues.append(
                        ValidationIssue(
                            rule="sensitive-values",
                            message=f"Potential hardcoded {desc}: {entry.key}",
                            severity=Severity.WARNING,
                            path=path,
                        )
                    )
                break


def _check_format_consistency(config: ConfigFile, result: ValidationResult) -> None:
    """Check for format consistency issues."""
    # Check for unmatched quotes in all entries
    all_entries = []
    for entry in config.globals.entries:
        all_entries.append(("", entry))
    for section in config.sections:
        for entry in section.entries:
            all_entries.append((section.name, entry))

    for section_name, entry in all_entries:
        path = f"{section_name}.{entry.key}" if section_name else entry.key
        has_unmatched = (entry.value.startswith('"') and not entry.value.endswith('"')) or (
            entry.value.startswith("'") and not entry.value.endswith("'")
        )
        if has_unmatched:
            result.issues.append(
                ValidationIssue(
                    rule="format-consistency",
                    message=f"Unmatched quote in value: {entry.key}",
                    severity=Severity.WARNING,
                    path=path,
                )
            )


def _check_schema(config: ConfigFile, schema: dict[str, Any], result: ValidationResult) -> None:
    """Check configuration against a schema."""
    required = schema.get("required", [])
    patterns = schema.get("patterns", {})

    # Check required keys
    for key in required:
        if not config.has(key):
            result.issues.append(
                ValidationIssue(
                    rule="schema-required",
                    message=f"Missing required key: {key}",
                    severity=Severity.ERROR,
                    path=key,
                )
            )

    # Check patterns
    for key, pattern in patterns.items():
        value = config.get(key)
        if value and not re.match(pattern, value):
            result.issues.append(
                ValidationIssue(
                    rule="schema-pattern",
                    message=f"Value doesn't match pattern for {key}: {pattern}",
                    severity=Severity.WARNING,
                    path=key,
                )
            )


def _calculate_score(result: ValidationResult) -> int:
    """Calculate health score (0-100)."""
    score = 100
    for issue in result.issues:
        if issue.severity == Severity.ERROR:
            score -= 10
        elif issue.severity == Severity.WARNING:
            score -= 3
        elif issue.severity == Severity.INFO:
            score -= 1
    return max(0, min(100, score))


def format_validation_report(result: ValidationResult) -> str:
    """Format validation result as readable text."""
    lines = []
    lines.append(f"Validation Score: {result.score}/100")
    lines.append(f"Status: {'VALID' if result.valid else 'INVALID'}")
    lines.append(f"Issues: {len(result.issues)} ({len(result.errors)} errors, {len(result.warnings)} warnings)")
    lines.append("")

    if not result.issues:
        lines.append("No issues found.")
        return "\n".join(lines)

    for issue in result.issues:
        lines.append(f"[{issue.severity.value.upper():>7}] {issue.rule}: {issue.message}")
        if issue.path:
            lines.append(f"         Path: {issue.path}")

    return "\n".join(lines)
