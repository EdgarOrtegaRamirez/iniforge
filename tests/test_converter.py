"""Tests for converter."""

import json

import pytest

from iniforge.converter import convert_config, detect_format
from iniforge.env_parser import parse_env
from iniforge.ini_parser import parse_ini


class TestConverter:
    """Tests for format conversion."""

    def test_detect_ini(self):
        content = "[section]\nkey = value"
        assert detect_format(content) == "ini"

    def test_detect_env(self):
        content = "KEY=value\nKEY2=value2"
        assert detect_format(content) == "env"

    def test_detect_properties(self):
        content = "! Comment\nkey=value"
        assert detect_format(content) == "properties"

    def test_detect_json(self):
        content = '{"key": "value"}'
        assert detect_format(content) == "json"

    def test_convert_ini_to_json(self):
        config = parse_ini("[database]\nhost = localhost\nport = 5432")
        output = convert_config(config, "json")
        data = json.loads(output)
        assert data["database"]["host"] == "localhost"

    def test_convert_ini_to_yaml(self):
        config = parse_ini("[database]\nhost = localhost\nport = 5432")
        output = convert_config(config, "yaml")
        assert "database:" in output
        assert "host: localhost" in output

    def test_convert_ini_to_toml(self):
        config = parse_ini("[database]\nhost = localhost\nport = 5432")
        output = convert_config(config, "toml")
        assert "[database]" in output
        assert 'host = "localhost"' in output

    def test_convert_ini_to_env(self):
        config = parse_ini("[database]\nhost = localhost\nport = 5432")
        output = convert_config(config, "env")
        assert "host=localhost" in output
        assert "port=5432" in output

    def test_convert_ini_to_properties(self):
        config = parse_ini("key1 = value1\nkey2 = value2")
        output = convert_config(config, "properties")
        assert "key1=value1" in output

    def test_convert_env_to_json(self):
        config = parse_env("DB_HOST=localhost\nDB_PORT=5432")
        output = convert_config(config, "json")
        data = json.loads(output)
        assert data["DB_HOST"] == "localhost"

    def test_convert_unsupported(self):
        config = parse_ini("key = value")
        with pytest.raises(ValueError):
            convert_config(config, "xml")

    def test_convert_ini_to_ini(self):
        config = parse_ini("[s]\nkey = value")
        output = convert_config(config, "ini")
        assert "[s]" in output
        assert "key = value" in output
