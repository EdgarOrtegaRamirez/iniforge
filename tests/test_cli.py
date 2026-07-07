"""Tests for CLI."""

import pytest

from iniforge.cli import main


class TestCLI:
    """Tests for CLI commands."""

    def setup_method(self):
        self.ini_content = """\
# Database configuration
[database]
host = localhost
port = 5432
name = mydb

# Server configuration
[server]
host = 0.0.0.0
port = 8080
debug = true
"""
        self.env_content = """\
# App config
DB_HOST=localhost
DB_PORT=5432
APP_PORT=8080
"""

    def test_version(self):
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])
        assert exc_info.value.code == 0

    def test_parse_ini(self, tmp_path):
        f = tmp_path / "test.ini"
        f.write_text(self.ini_content)
        result = main(["parse", str(f)])
        assert result == 0

    def test_parse_ini_json(self, tmp_path):
        f = tmp_path / "test.ini"
        f.write_text(self.ini_content)
        result = main(["parse", str(f), "--json"])
        assert result == 0

    def test_parse_env(self, tmp_path):
        f = tmp_path / "test.env"
        f.write_text(self.env_content)
        result = main(["parse", str(f)])
        assert result == 0

    def test_query(self, tmp_path):
        f = tmp_path / "test.ini"
        f.write_text(self.ini_content)
        result = main(["query", str(f), "database.host"])
        assert result == 0

    def test_diff(self, tmp_path):
        f1 = tmp_path / "base.ini"
        f2 = tmp_path / "modified.ini"
        f1.write_text("[s]\nkey1 = old\nkey2 = keep")
        f2.write_text("[s]\nkey1 = new\nkey3 = added")
        result = main(["diff", str(f1), str(f2)])
        assert result == 1  # differences found

    def test_diff_identical(self, tmp_path):
        f1 = tmp_path / "base.ini"
        f2 = tmp_path / "copy.ini"
        f1.write_text("[s]\nkey1 = value")
        f2.write_text("[s]\nkey1 = value")
        result = main(["diff", str(f1), str(f2)])
        assert result == 0

    def test_merge(self, tmp_path):
        f1 = tmp_path / "base.ini"
        f2 = tmp_path / "override.ini"
        f1.write_text("[s]\nkey1 = old\nkey2 = keep")
        f2.write_text("[s]\nkey1 = new")
        result = main(["merge", str(f1), str(f2)])
        assert result == 0

    def test_convert(self, tmp_path):
        f = tmp_path / "test.ini"
        f.write_text("[s]\nkey = value")
        result = main(["convert", str(f), "--to", "json"])
        assert result == 0

    def test_validate(self, tmp_path):
        f = tmp_path / "test.ini"
        f.write_text("[s]\nkey = value")
        result = main(["validate", str(f)])
        assert result == 0

    def test_info(self, tmp_path):
        f = tmp_path / "test.ini"
        f.write_text("[s]\nkey = value")
        result = main(["info", str(f)])
        assert result == 0

    def test_detect(self, tmp_path):
        f = tmp_path / "test.ini"
        f.write_text("[section]\nkey = value")
        result = main(["detect", str(f)])
        assert result == 0

    def test_file_not_found(self):
        result = main(["parse", "/nonexistent/file.ini"])
        assert result == 1
