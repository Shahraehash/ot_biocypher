import pandas as pd
import glob
import os
import json
from knowledge_graph_adapters.config_loader import get_adapter_config

def construct_dataframe(evidence_sub_folder, keys):
    """
    Construct a DataFrame from evidence JSON files
    
    Args:
        evidence_sub_folder (str): Path to the evidence subfolder
        keys (list): List of keys to extract from the JSON files
        
    Returns:
        pd.DataFrame: DataFrame with evidence data
    """
    dictionary_of_data = {key: [] for key in keys}
    
    for path in glob.glob(evidence_sub_folder + "*.json"):
        with open(path, "r") as f:
            data = [json.loads(line) for line in f]
            
        for entry in data:
            for key in keys:
                if key in entry:
                    if key == "urls":
                        # Special handling for URLs
                        list_of_urls = [elem['url'] for elem in entry[key]]
                        # Check for empty lists
                        dictionary_of_data[key].append(list_of_urls if list_of_urls else ["No record"])
                    else:
                        value = entry[key]
                        # Check for empty string and replace with "No record"
                        dictionary_of_data[key].append(value if value != "" else "No record")
                else:
                    dictionary_of_data[key].append("No record")
                    
    return pd.DataFrame(dictionary_of_data)

def rename_and_construct_relationships(dataframe):
    """
    Rename columns and construct relationships from evidence data
    
    Args:
        dataframe (pd.DataFrame): DataFrame with evidence data
        
    Returns:
        pd.DataFrame: DataFrame with relationship data
    """
    if all(col in dataframe.columns for col in ['targetId', 'diseaseId', 'drugId']):
        # Handle relationships with drug, target, and disease
        remaining_columns = [item for item in dataframe.columns if item not in ['targetId', 'diseaseId', 'drugId']]
        
        # Disease to target relationships
        subset_1 = dataframe[remaining_columns + ['targetId', 'diseaseId']]
        subset_1[':START_ID'] = subset_1['diseaseId']
        subset_1[':END_ID'] = subset_1['targetId']
        subset_1[':TYPE'] = subset_1['datasourceId'] + "DiseaseToTarget"
        
        # Drug to target relationships
        subset_2 = dataframe[remaining_columns + ['targetId', 'drugId']]
        subset_2[':START_ID'] = subset_2['drugId']
        subset_2[':END_ID'] = subset_2['targetId']
        subset_2[':TYPE'] = subset_2['datasourceId'] + "DrugToTarget"
        
        # Combine relationships
        concat_df = pd.concat([subset_1, subset_2], axis=0, ignore_index=True)
        relationship_df = concat_df[[":START_ID"] + remaining_columns + [":END_ID", ":TYPE"]] 
        return relationship_df
    
    elif all(col in dataframe.columns for col in ['targetId', 'diseaseId']):
        # Handle relationships with only target and disease
        remaining_columns = [item for item in dataframe.columns if item not in ['targetId', 'diseaseId']]
        dataframe[':START_ID'] = dataframe['diseaseId']
        dataframe[':END_ID'] = dataframe['targetId']
        dataframe[':TYPE'] = dataframe['datasourceId'] + "DiseaseToTarget"
        relationship_df = dataframe[[":START_ID"] + remaining_columns + [":END_ID", ":TYPE"]] 
        return relationship_df
    
    else:
        # No valid relationships
        return None

def create_evidence_data(evidence_folder, only_drug=False):
    """
    Create evidence data from evidence JSON files
    
    Args:
        evidence_folder (str): Path to the evidence folder
        only_drug (bool): If True, only include sources with drugId
        
    Returns:
        list: List of DataFrames with evidence data
    """
    config = get_adapter_config("evidence")
    folder_keys = config["folder_keys"]
    
    list_of_data = []
    for folder, keys in folder_keys.items():
        if only_drug and "drugId" not in keys:
            continue
            
        sub_folder_path = f"{evidence_folder}sourceid={folder}/"
        if not os.path.exists(sub_folder_path):
            continue
            
        raw_df = construct_dataframe(sub_folder_path, keys)
        edge_df = rename_and_construct_relationships(raw_df)
        
        if edge_df is not None and not edge_df.empty:
            list_of_data.append(edge_df)
            
    return list_of_data