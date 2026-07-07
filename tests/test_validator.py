"""Tests for validator."""

from iniforge.ini_parser import parse_ini
from iniforge.validator import Severity, format_validation_report, validate_config


class TestValidator:
    """Tests for configuration validation."""

    def test_valid_config(self):
        content = "[database]\nhost = localhost\nport = 5432"
        config = parse_ini(content)
        result = validate_config(config)
        assert result.valid is True
        assert result.score == 100

    def test_empty_key(self):
        content = "[section]\n = value"
        config = parse_ini(content)
        result = validate_config(config)
        assert len(result.errors) > 0
        assert result.valid is False

    def test_duplicate_keys(self):
        content = "[section]\nkey = value1\nkey = value2"
        config = parse_ini(content)
        result = validate_config(config)
        warnings = [i for i in result.issues if i.severity == Severity.WARNING]
        assert len(warnings) > 0

    def test_empty_values(self):
        content = "[section]\nkey ="
        config = parse_ini(content)
        result = validate_config(config)
        infos = [i for i in result.issues if i.severity == Severity.INFO]
        assert len(infos) > 0

    def test_sensitive_values(self):
        content = "[section]\npassword = secret123\napi_key = abc123"
        config = parse_ini(content)
        result = validate_config(config)
        warnings = [i for i in result.issues if i.rule == "sensitive-values"]
        assert len(warnings) == 2

    def test_sensitive_values_with_reference(self):
        content = "[section]\npassword = ${DB_PASSWORD}"
        config = parse_ini(content)
        result = validate_config(config)
        warnings = [i for i in result.issues if i.rule == "sensitive-values"]
        assert len(warnings) == 0

    def test_unmatched_quote(self):
        content = '[section]\nkey = "unmatched'
        config = parse_ini(content)
        result = validate_config(config)
        warnings = [i for i in result.issues if i.rule == "format-consistency"]
        assert len(warnings) > 0

    def test_schema_validation(self):
        content = "[database]\nhost = localhost"
        config = parse_ini(content)
        schema = {"required": ["database.host", "database.port"]}
        result = validate_config(config, schema=schema)
        errors = [i for i in result.issues if i.rule == "schema-required"]
        assert len(errors) == 1
        assert "database.port" in errors[0].message

    def test_schema_pattern(self):
        content = "[server]\nport = not_a_number"
        config = parse_ini(content)
        schema = {"patterns": {"server.port": r"^\d+$"}}
        result = validate_config(config, schema=schema)
        warnings = [i for i in result.issues if i.rule == "schema-pattern"]
        assert len(warnings) == 1

    def test_score_calculation(self):
        content = "[section]\nkey = value"
        config = parse_ini(content)
        result = validate_config(config)
        assert result.score == 100

    def test_score_with_issues(self):
        content = "[section]\n = \npassword = hardcoded"
        config = parse_ini(content)
        result = validate_config(config)
        assert result.score < 100

    def test_format_report(self):
        content = "[section]\nkey = value"
        config = parse_ini(content)
        result = validate_config(config)
        report = format_validation_report(result)
        assert "100/100" in report
        assert "VALID" in report

    def test_format_report_with_issues(self):
        content = "[section]\npassword = hardcoded"
        config = parse_ini(content)
        result = validate_config(config)
        report = format_validation_report(result)
        assert "sensitive-values" in report
