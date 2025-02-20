# src/utils/config.py
import json
import os
from typing import Optional

DEFAULT_CONFIG_PATH = "config.json"
DEFAULT_CONFIG = {
    "openai_api_key": "",
    "anthropic_api_key": "",
    "use_anthropic": False,
    "debug_mode": False
}

def load_config():
    """Load configuration from config.json"""
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def save_config(config: dict, config_path: str = DEFAULT_CONFIG_PATH) -> None:
    """Save configuration to JSON file"""
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")

def get_vendor() -> str:
    """Get the vendor from config"""
    config = load_config()
    return config.get('use_vendor', 'openai').lower()  # Default to OpenAI if not specified

def get_api_key(vendor: str) -> str:
    """Get API key for specified vendor"""
    config = load_config()
    key_mapping = {
        'openai': 'openai_api_key',
        'anthropic': 'anthropic_api_key',
        'gemini': 'gemini_api_key'
    }
    key_name = key_mapping.get(vendor.lower())
    if not key_name:
        raise ValueError(f"Unsupported vendor: {vendor}")
    return config.get(key_name)

def get_debug_mode() -> bool:
    """Get debug mode setting"""
    config = load_config()
    return config.get('debug_mode', False)