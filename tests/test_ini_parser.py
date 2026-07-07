"""Tests for INI parser."""

import pytest

from iniforge.ini_parser import IniParseError, parse_ini, serialize_ini


class TestIniParser:
    """Tests for INI file parsing."""

    def test_parse_simple(self):
        content = "[section]\nkey1 = value1\nkey2 = value2"
        config = parse_ini(content)
        assert config.format == "ini"
        assert len(config.sections) == 1
        assert config.sections[0].name == "section"
        assert config.get("section.key1") == "value1"
        assert config.get("section.key2") == "value2"

    def test_parse_globals(self):
        content = "key1 = value1\nkey2 = value2"
        config = parse_ini(content)
        assert len(config.sections) == 0
        assert config.get("key1") == "value1"
        assert config.get("key2") == "value2"

    def test_parse_multiple_sections(self):
        content = "[database]\nhost = localhost\nport = 5432\n\n[server]\nhost = 0.0.0.0\nport = 8080"
        config = parse_ini(content)
        assert len(config.sections) == 2
        assert config.get("database.host") == "localhost"
        assert config.get("server.port") == "8080"

    def test_parse_comments(self):
        content = "# This is a comment\n[section]\n; Another comment\nkey = value"
        config = parse_ini(content)
        assert len(config.sections) == 1
        assert config.sections[0].comment == "This is a comment"
        assert config.get("section.key") == "value"

    def test_parse_inline_comments(self):
        content = "[section]\nkey = value  # inline comment"
        config = parse_ini(content)
        assert config.get("section.key") == "value"

    def test_parse_empty_values(self):
        content = "[section]\nkey ="
        config = parse_ini(content)
        assert config.get("section.key") == ""

    def test_parse_multiline_values(self):
        content = "[section]\nkey = line1\n    line2\n    line3"
        config = parse_ini(content)
        assert config.get("section.key") == "line1line2line3"

    def test_parse_backslash_continuation(self):
        content = "[section]\nkey = line1\\\n    line2"
        config = parse_ini(content)
        assert config.get("section.key") == "line1line2"

    def test_parse_interpolation(self):
        content = "[section]\nbase = hello\nfull = ${base}_world"
        config = parse_ini(content)
        assert config.get("section.full") == "hello_world"

    def test_parse_percent_interpolation(self):
        content = "[section]\nbase = hello\nfull = %(base)s_world"
        config = parse_ini(content)
        assert config.get("section.full") == "hello_world"

    def test_parse_unclosed_section(self):
        content = "[section\nkey = value"
        with pytest.raises(IniParseError):
            parse_ini(content)

    def test_parse_section_with_spaces(self):
        content = "[my section]\nkey = value"
        config = parse_ini(content)
        assert config.sections[0].name == "my section"

    def test_parse_complex_values(self):
        content = "[section]\nurl = http://example.com:8080/path?q=1&r=2\npath = /usr/local/bin"
        config = parse_ini(content)
        assert config.get("section.url") == "http://example.com:8080/path?q=1&r=2"

    def test_serialize_simple(self):
        content = "[section]\nkey1 = value1\nkey2 = value2"
        config = parse_ini(content)
        output = serialize_ini(config)
        assert "[section]" in output
        assert "key1 = value1" in output
        assert "key2 = value2" in output

    def test_serialize_globals(self):
        content = "key1 = value1"
        config = parse_ini(content)
        output = serialize_ini(config)
        assert "key1 = value1" in output

    def test_roundtrip(self):
        content = "[database]\nhost = localhost\nport = 5432\n\n[server]\nhost = 0.0.0.0\nport = 8080"
        config = parse_ini(content)
        output = serialize_ini(config)
        config2 = parse_ini(output)
        assert config.to_dict() == config2.to_dict()

    def test_to_dict(self):
        content = "[section]\nkey = value"
        config = parse_ini(content)
        d = config.to_dict()
        assert "section" in d
        assert d["section"]["key"] == "value"

    def test_case_insensitive_sections(self):
        content = "[Section]\nkey = value"
        config = parse_ini(content)
        assert config.get("section.key") == "value"
        assert config.get("SECTION.key") == "value"
