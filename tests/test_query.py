"""Tests for query engine."""

from iniforge.ini_parser import parse_ini
from iniforge.query import get_section_keys, get_value, list_keys, query_config


class TestQuery:
    """Tests for configuration query engine."""

    def setup_method(self):
        self.content = """\
# Global settings
app_name = myapp
version = 1.0

[database]
host = localhost
port = 5432
name = mydb

[server]
host = 0.0.0.0
port = 8080
debug = true
"""
        self.config = parse_ini(self.content)

    def test_query_global_key(self):
        assert query_config(self.config, "app_name") == "myapp"

    def test_query_section_key(self):
        assert query_config(self.config, "database.host") == "localhost"

    def test_query_nonexistent_key(self):
        assert query_config(self.config, "nonexistent") is None

    def test_query_section(self):
        result = query_config(self.config, "database")
        assert isinstance(result, dict)
        assert result["host"] == "localhost"

    def test_query_wildcard_all(self):
        result = query_config(self.config, "*")
        assert isinstance(result, dict)
        assert "database" in result
        assert "server" in result

    def test_query_section_wildcard(self):
        result = query_config(self.config, "database.*")
        assert isinstance(result, dict)
        assert result["host"] == "localhost"
        assert result["port"] == "5432"

    def test_query_with_default(self):
        assert query_config(self.config, "nonexistent:default") == "default"

    def test_list_keys(self):
        keys = list_keys(self.config)
        assert "app_name" in keys
        assert "database.host" in keys
        assert "server.port" in keys

    def test_list_keys_with_pattern(self):
        keys = list_keys(self.config, "*.host")
        assert "database.host" in keys
        assert "server.host" in keys
        assert "database.port" not in keys

    def test_get_value(self):
        assert get_value(self.config, "database.host") == "localhost"
        assert get_value(self.config, "nonexistent", "default") == "default"

    def test_get_section_keys(self):
        keys = get_section_keys(self.config, "database")
        assert "host" in keys
        assert "port" in keys
        assert "name" in keys

    def test_get_section_keys_nonexistent(self):
        keys = get_section_keys(self.config, "nonexistent")
        assert keys == []
