"""Configuration module for Switzerbot.

This module re-exports from the config.py package to maintain compatibility.
"""

import importlib.util
from pathlib import Path

# Load config.py.config module using spec_from_file_location
config_py_path = Path(__file__).parent.parent / "config.py" / "config.py"
spec = importlib.util.spec_from_file_location("_config_impl", config_py_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)

Settings = config_module.Settings
settings = config_module.settings

__all__ = ["Settings", "settings"]
