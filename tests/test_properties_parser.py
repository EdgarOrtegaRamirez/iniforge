"""Tests for .properties parser."""

from iniforge.properties_parser import parse_properties, serialize_properties


class TestPropertiesParser:
    """Tests for .properties file parsing."""

    def test_parse_simple(self):
        content = "key1=value1\nkey2=value2"
        config = parse_properties(content)
        assert config.format == "properties"
        assert config.get("key1") == "value1"
        assert config.get("key2") == "value2"

    def test_parse_with_colon_separator(self):
        content = "key1:value1\nkey2:value2"
        config = parse_properties(content)
        assert config.get("key1") == "value1"

    def test_parse_with_space_separator(self):
        content = "key1 value1\nkey2 value2"
        config = parse_properties(content)
        assert config.get("key1") == "value1"

    def test_parse_comments(self):
        content = "# Comment\nkey=value\n! Another comment\nkey2=value2"
        config = parse_properties(content)
        assert config.get("key") == "value"
        assert config.get("key2") == "value2"

    def test_parse_unicode_escapes(self):
        content = "key=\\u0048\\u0065\\u006C\\u006C\\u006F"
        config = parse_properties(content)
        assert config.get("key") == "Hello"

    def test_parse_multiline_continuation(self):
        content = "key=value1\\\n    value2"
        config = parse_properties(content)
        assert config.get("key") == "value1value2"

    def test_parse_empty_value(self):
        content = "key="
        config = parse_properties(content)
        assert config.get("key") == ""

    def test_parse_no_value(self):
        content = "key"
        config = parse_properties(content)
        assert config.get("key") == ""

    def test_parse_section_comment(self):
        content = "# Section: database\nhost=localhost\nport=5432"
        config = parse_properties(content)
        assert config.get("host") == "localhost"

    def test_serialize_simple(self):
        content = "key1=value1\nkey2=value2"
        config = parse_properties(content)
        output = serialize_properties(config)
        assert "key1=value1" in output
        assert "key2=value2" in output

    def test_roundtrip(self):
        content = "key1=value1\nkey2=value2\nkey3=value3"
        config = parse_properties(content)
        output = serialize_properties(config)
        config2 = parse_properties(output)
        assert config.get("key1") == config2.get("key1")
        assert config.get("key2") == config2.get("key2")

    def test_to_dict(self):
        content = "host=localhost\nport=5432"
        config = parse_properties(content)
        d = config.to_dict()
        assert d["host"] == "localhost"
        assert d["port"] == "5432"

    def test_java_properties_example(self):
        content = """\
# Database configuration
db.host=localhost
db.port=5432
db.name=mydb
db.user=admin
db.password=secret
"""
        config = parse_properties(content)
        assert config.get("db.host") == "localhost"
        assert config.get("db.port") == "5432"
        assert config.get("db.password") == "secret"
