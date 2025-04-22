import pandas as pd
import glob
import json
from knowledge_graph_adapters.config_loader import get_adapter_config

def extract_disease_aspects(file):
    """
    Extract disease data from a JSON file based on the configuration
    
    Args:
        file (str): Path to the JSON file
        
    Returns:
        dict: Dictionary with disease data
    """
    config = get_adapter_config("disease")
    
    with open(file, "r") as f:
        data = [json.loads(line) for line in f]
    
    # Initialize the dictionary with the fields from config
    dictionary_of_disease = {field: [] for field in config["fields"]}
    
    for entry in data:
        # Skip entries without required fields
        if not all(field in entry for field in config["required_fields"]):
            continue
            
        for field, source_field in config["fields"].items():
            if field == ":LABEL":
                # Static value
                dictionary_of_disease[field].append(source_field)
            elif "." in source_field:
                # Handle nested fields
                parts = source_field.split(".")
                value = entry
                try:
                    for part in parts:
                        value = value[part]
                    # Check for empty string and replace with "No record"
                    dictionary_of_disease[field].append(value if value != "" else "No record")
                except (KeyError, TypeError):
                    dictionary_of_disease[field].append("No record")
            else:
                # Regular field
                value = entry.get(source_field, "No record")
                # Check for empty string and replace with "No record"
                dictionary_of_disease[field].append(value if value != "" else "No record")
            
    return dictionary_of_disease

def create_disease_data(data_path):
    """
    Create a DataFrame with disease data
    
    Args:
        data_path (str): Path to the directory with disease JSON files
        
    Returns:
        pd.DataFrame: DataFrame with disease data
    """
    list_of_dataframes = []
    for path in glob.glob(data_path + "*.json"):
        disease_dict = extract_disease_aspects(path)
        list_of_dataframes.append(pd.DataFrame(disease_dict))
    
    if not list_of_dataframes:
        return pd.DataFrame()
        
    disease_pd = pd.concat(list_of_dataframes, axis=0, ignore_index=True)
    return disease_pd