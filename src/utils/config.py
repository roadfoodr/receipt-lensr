# src/utils/config.py
import json
import os
from typing import Optional

DEFAULT_CONFIG_PATH = "config.json"
DEFAULT_CONFIG = {
    "openai_api_key": "",
    "anthropic_api_key": "",
    "use_anthropic": False
}

def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> dict:
    """Load configuration from JSON file, creating default if not exists"""
    # print(f"Loading config from {config_path}")
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            # Create default config file if it doesn't exist
            save_config(DEFAULT_CONFIG, config_path)
            return DEFAULT_CONFIG
    except Exception as e:
        print(f"Error loading config: {e}")
        return DEFAULT_CONFIG

def save_config(config: dict, config_path: str = DEFAULT_CONFIG_PATH) -> None:
    """Save configuration to JSON file"""
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")

def get_api_key(use_anthropic: bool = False) -> Optional[str]:
    """Get the appropriate API key based on service selection"""
    config = load_config()
    return config.get('anthropic_api_key' if use_anthropic else 'openai_api_key')