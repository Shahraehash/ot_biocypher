import json
import os

def load_config(config_path="knowledge_graph_adapters/adapter_config.json"):
    """
    Load the adapter configuration from a JSON file
    
    Args:
        config_path (str): Path to the JSON configuration file
        
    Returns:
        dict: The loaded configuration
    """
    with open(config_path, 'r') as f:
        config = json.load(f)
    return config

def get_adapter_config(adapter_type):
    """
    Get configuration for a specific adapter type
    
    Args:
        adapter_type (str): Type of adapter (disease, targets, molecule, evidence)
        
    Returns:
        dict: Configuration for the specified adapter
    """
    config = load_config()
    if adapter_type not in config:
        raise ValueError(f"Adapter type '{adapter_type}' not found in configuration")
    return config[adapter_type]