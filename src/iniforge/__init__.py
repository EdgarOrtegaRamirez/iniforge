"""IniForge — Configuration File Processing Toolkit"""

__version__ = "1.0.0"
__author__ = "EdgarOrtegaRamirez"

from .converter import convert_config
from .diff import diff_configs
from .env_parser import parse_env
from .ini_parser import parse_ini
from .merge import merge_configs
from .models import ConfigEntry, ConfigFile, ConfigSection
from .properties_parser import parse_properties
from .query import query_config
from .validator import validate_config

__all__ = [
    "ConfigFile",
    "ConfigSection",
    "ConfigEntry",
    "parse_ini",
    "parse_properties",
    "parse_env",
    "query_config",
    "diff_configs",
    "merge_configs",
    "convert_config",
    "validate_config",
]
