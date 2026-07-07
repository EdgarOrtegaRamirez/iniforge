"""Tests for diff engine."""

from iniforge.diff import diff_configs, format_diff_text, format_diff_unified
from iniforge.ini_parser import parse_ini


class TestDiff:
    """Tests for configuration diff engine."""

    def test_identical_configs(self):
        content = "[section]\nkey1 = value1\nkey2 = value2"
        config1 = parse_ini(content)
        config2 = parse_ini(content)
        result = diff_configs(config1, config2)
        assert result.identical is True
        assert len(result.changes) == 0

    def test_added_key(self):
        config1 = parse_ini("[section]\nkey1 = value1")
        config2 = parse_ini("[section]\nkey1 = value1\nkey2 = value2")
        result = diff_configs(config1, config2)
        assert result.identical is False
        assert len(result.added) == 1
        assert result.added[0].path == "section.key2"
        assert result.added[0].new_value == "value2"

    def test_removed_key(self):
        config1 = parse_ini("[section]\nkey1 = value1\nkey2 = value2")
        config2 = parse_ini("[section]\nkey1 = value1")
        result = diff_configs(config1, config2)
        assert len(result.removed) == 1
        assert result.removed[0].path == "section.key2"

    def test_modified_key(self):
        config1 = parse_ini("[section]\nkey1 = old_value")
        config2 = parse_ini("[section]\nkey1 = new_value")
        result = diff_configs(config1, config2)
        assert len(result.modified) == 1
        assert result.modified[0].old_value == "old_value"
        assert result.modified[0].new_value == "new_value"

    def test_added_section(self):
        config1 = parse_ini("[section1]\nkey1 = value1")
        config2 = parse_ini("[section1]\nkey1 = value1\n\n[section2]\nkey2 = value2")
        result = diff_configs(config1, config2)
        assert len(result.added) == 1
        assert result.added[0].path == "section2.key2"

    def test_removed_section(self):
        config1 = parse_ini("[section1]\nkey1 = value1\n\n[section2]\nkey2 = value2")
        config2 = parse_ini("[section1]\nkey1 = value1")
        result = diff_configs(config1, config2)
        assert len(result.removed) == 1
        assert result.removed[0].path == "section2.key2"

    def test_multiple_changes(self):
        config1 = parse_ini("[s]\nkey1 = a\nkey2 = b\nkey3 = c")
        config2 = parse_ini("[s]\nkey1 = a\nkey2 = modified\nkey4 = d")
        result = diff_configs(config1, config2)
        assert result.summary["modified"] == 1
        assert result.summary["added"] == 1
        assert result.summary["removed"] == 1

    def test_format_diff_text(self):
        config1 = parse_ini("[s]\nkey1 = old")
        config2 = parse_ini("[s]\nkey1 = new")
        result = diff_configs(config1, config2)
        text = format_diff_text(result)
        assert "~ s.key1: old -> new" in text

    def test_format_diff_unified(self):
        config1 = parse_ini("[s]\nkey1 = old")
        config2 = parse_ini("[s]\nkey1 = new")
        result = diff_configs(config1, config2)
        unified = format_diff_unified(result)
        assert "-s.key1 = old" in unified
        assert "+s.key1 = new" in unified

    def test_format_diff_identical(self):
        config1 = parse_ini("[s]\nkey1 = value")
        config2 = parse_ini("[s]\nkey1 = value")
        result = diff_configs(config1, config2)
        assert format_diff_text(result) == "No differences found."

    def test_global_keys_diff(self):
        config1 = parse_ini("key1 = value1")
        config2 = parse_ini("key1 = value1\nkey2 = value2")
        result = diff_configs(config1, config2)
        assert len(result.added) == 1
        assert result.added[0].path == "key2"
