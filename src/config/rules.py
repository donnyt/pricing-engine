"""
Configuration rules management for the pricing engine.

This module handles loading and managing pricing rules from configuration files.
"""

import yaml
import os
from typing import Any, Dict


# Default path to the pricing rules configuration file
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../../config/pricing_rules.yaml")


def load_pricing_rules(config_path: str = CONFIG_PATH) -> Dict[str, Any]:
    """
    Load pricing rules from the YAML config file.

    Args:
        config_path: Path to the YAML configuration file.
                    Defaults to the standard config location.

    Returns:
        Dictionary containing the loaded pricing rules configuration.

    Raises:
        FileNotFoundError: If the configuration file doesn't exist.
        yaml.YAMLError: If the YAML file is malformed.
    """
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML configuration file: {e}")
