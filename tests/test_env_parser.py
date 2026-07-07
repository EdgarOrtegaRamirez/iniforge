"""Tests for .env parser."""

from iniforge.env_parser import parse_env, serialize_env


class TestEnvParser:
    """Tests for .env file parsing."""

    def test_parse_simple(self):
        content = "KEY1=value1\nKEY2=value2"
        config = parse_env(content)
        assert config.format == "env"
        assert config.get("KEY1") == "value1"
        assert config.get("KEY2") == "value2"

    def test_parse_with_export(self):
        content = "export KEY1=value1\nexport KEY2=value2"
        config = parse_env(content)
        assert config.get("KEY1") == "value1"
        assert config.get("KEY2") == "value2"

    def test_parse_quoted_values(self):
        content = "KEY1=\"value1\"\nKEY2='value2'"
        config = parse_env(content)
        assert config.get("KEY1") == "value1"
        assert config.get("KEY2") == "value2"

    def test_parse_empty_values(self):
        content = 'KEY1=\nKEY2=""'
        config = parse_env(content)
        assert config.get("KEY1") == ""

    def test_parse_comments(self):
        content = "# Database config\nDB_HOST=localhost\n# Server config\nPORT=8080"
        config = parse_env(content)
        assert config.get("DB_HOST") == "localhost"
        assert config.get("PORT") == "8080"

    def test_parse_variable_expansion(self):
        content = "BASE_URL=http://localhost\nAPI_URL=${BASE_URL}/api"
        config = parse_env(content)
        assert config.get("API_URL") == "http://localhost/api"

    def test_parse_dollar_expansion(self):
        content = "HOST=localhost\nPORT=8080\nURL=$HOST:$PORT"
        config = parse_env(content)
        assert config.get("URL") == "localhost:8080"

    def test_parse_multiline_quoted(self):
        content = 'KEY1="line1\nline2\nline3"'
        config = parse_env(content)
        assert "line1" in config.get("KEY1")
        assert "line2" in config.get("KEY1")

    def test_parse_spaces_in_values(self):
        content = 'KEY1=hello world\nKEY2="hello world"'
        config = parse_env(content)
        assert config.get("KEY1") == "hello world"

    def test_serialize_simple(self):
        content = "KEY1=value1\nKEY2=value2"
        config = parse_env(content)
        output = serialize_env(config)
        assert "KEY1=value1" in output
        assert "KEY2=value2" in output

    def test_serialize_spaces(self):
        content = "KEY1=hello world"
        config = parse_env(content)
        output = serialize_env(config)
        assert 'KEY1="hello world"' in output

    def test_roundtrip(self):
        content = "DB_HOST=localhost\nDB_PORT=5432\nDB_NAME=mydb"
        config = parse_env(content)
        output = serialize_env(config)
        config2 = parse_env(output)
        assert config.get("DB_HOST") == config2.get("DB_HOST")
        assert config.get("DB_PORT") == config2.get("DB_PORT")

    def test_docker_compose_example(self):
        content = """\
# Docker Compose Environment
POSTGRES_DB=myapp
POSTGRES_USER=admin
POSTGRES_PASSWORD=secret123
REDIS_URL=redis://cache:6379

# Application
APP_PORT=3000
APP_ENV=development
"""
        config = parse_env(content)
        assert config.get("POSTGRES_DB") == "myapp"
        assert config.get("REDIS_URL") == "redis://cache:6379"
        assert config.get("APP_PORT") == "3000"

    def test_to_dict(self):
        content = "KEY1=value1\nKEY2=value2"
        config = parse_env(content)
        d = config.to_dict()
        assert d["KEY1"] == "value1"
        assert d["KEY2"] == "value2"
