"""Tests for merge engine."""

from iniforge.ini_parser import parse_ini
from iniforge.merge import MergeStrategy, merge_configs, merge_files


class TestMerge:
    """Tests for configuration merge engine."""

    def test_merge_override(self):
        config1 = parse_ini("[s]\nkey1 = old\nkey2 = keep")
        config2 = parse_ini("[s]\nkey1 = new")
        merged = merge_configs(config1, config2, MergeStrategy.OVERRIDE)
        assert merged.get("s.key1") == "new"
        assert merged.get("s.key2") == "keep"

    def test_merge_keep_original(self):
        config1 = parse_ini("[s]\nkey1 = original")
        config2 = parse_ini("[s]\nkey1 = override")
        merged = merge_configs(config1, config2, MergeStrategy.KEEP_ORIGINAL)
        assert merged.get("s.key1") == "original"

    def test_merge_union(self):
        config1 = parse_ini("[s]\nkey1 = a,c")
        config2 = parse_ini("[s]\nkey1 = b,c")
        merged = merge_configs(config1, config2, MergeStrategy.UNION)
        value = merged.get("s.key1")
        assert "a" in value
        assert "b" in value
        assert "c" in value

    def test_merge_new_section(self):
        config1 = parse_ini("[s1]\nkey1 = value1")
        config2 = parse_ini("[s2]\nkey2 = value2")
        merged = merge_configs(config1, config2)
        assert merged.get("s1.key1") == "value1"
        assert merged.get("s2.key2") == "value2"

    def test_merge_new_key(self):
        config1 = parse_ini("[s]\nkey1 = value1")
        config2 = parse_ini("[s]\nkey1 = value1\nkey2 = value2")
        merged = merge_configs(config1, config2)
        assert merged.get("s.key2") == "value2"

    def test_merge_globals(self):
        config1 = parse_ini("key1 = value1")
        config2 = parse_ini("key1 = new\nkey2 = value2")
        merged = merge_configs(config1, config2)
        assert merged.get("key1") == "new"
        assert merged.get("key2") == "value2"

    def test_merge_files(self):
        config1 = parse_ini("[s]\nkey1 = v1\nkey2 = v2")
        config2 = parse_ini("[s]\nkey2 = override\nkey3 = v3")
        config3 = parse_ini("[s]\nkey3 = override3\nkey4 = v4")
        merged = merge_files([config1, config2, config3])
        assert merged.get("s.key1") == "v1"
        assert merged.get("s.key2") == "override"
        assert merged.get("s.key3") == "override3"
        assert merged.get("s.key4") == "v4"

    def test_merge_empty_files(self):
        config = parse_ini("[s]\nkey = value")
        merged = merge_files([config])
        assert merged.get("s.key") == "value"

    def test_merge_preserves_order(self):
        config1 = parse_ini("a = 1\nb = 2\nc = 3")
        config2 = parse_ini("b = override\nd = 4")
        merged = merge_configs(config1, config2)
        keys = merged.keys()
        assert keys.index("a") < keys.index("b")
        assert keys.index("b") < keys.index("c")
        assert "d" in keys
