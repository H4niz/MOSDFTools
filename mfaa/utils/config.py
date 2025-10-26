"""
Configuration Loader
====================

Load and manage configuration files.
"""

import yaml
from pathlib import Path
from typing import Dict, Any


class ConfigLoader:
    """Load configuration from YAML files."""

    @staticmethod
    def load_yaml(config_path: Path) -> Dict[str, Any]:
        """
        Load YAML configuration file.

        Args:
            config_path: Path to YAML file

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If YAML is malformed
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        return config or {}

    @staticmethod
    def save_yaml(config: Dict[str, Any], output_path: Path) -> None:
        """
        Save configuration to YAML file.

        Args:
            config: Configuration dictionary
            output_path: Path to output YAML file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
