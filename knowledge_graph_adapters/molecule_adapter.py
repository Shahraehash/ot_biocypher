import pandas as pd
import glob
import json
from knowledge_graph_adapters.config_loader import get_adapter_config

def extract_molecule_aspects(file, embedding_path):
    """
    Extract molecule data from a JSON file based on the configuration
    
    Args:
        file (str): Path to the JSON file
        embedding_path (str): Path to the embedding CSV file
        
    Returns:
        dict: Dictionary with molecule data
    """
    config = get_adapter_config("molecule")
    
    with open(file, "r") as f:
        data = [json.loads(line) for line in f]
    
    # Load embeddings
    embeddings = pd.read_csv(embedding_path)
    embedding_chembl = embeddings["chembl_id"].tolist()
    # Initialize the dictionary with the fields from config
    dictionary_of_molecules = {field: [] for field in config["fields"]}
    
    for entry in data:
        # Skip entries without required fields or not in embeddings
        if not all(field in entry for field in config["required_fields"]) or entry.get("drugType") != "Small molecule" or entry.get("id") not in embedding_chembl:
            continue
            
        for field, source_field in config["fields"].items():
            if field == ":LABEL":
                # Static value
                dictionary_of_molecules[field].append(source_field)
            elif field == "Embedding":
                # Special handling for embedding
                embedding_value = embeddings.loc[embeddings['chembl_id'] == entry["id"], 'embedding'].values[0]
                dictionary_of_molecules[field].append(embedding_value)
            elif field == "Embedding_Source":
                # Special handling for embedding source
                source_value = embeddings.loc[embeddings['chembl_id'] == entry["id"], 'source'].values[0]
                dictionary_of_molecules[field].append(source_value)
            elif "." in source_field:
                # Handle nested fields
                parts = source_field.split(".")
                value = entry
                try:
                    for part in parts:
                        value = value[part]
                    # Check for empty string and replace with "No record"
                    dictionary_of_molecules[field].append(value if value != "" else "No record")
                except (KeyError, TypeError):
                    dictionary_of_molecules[field].append("No record")
            else:
                # Regular field
                if field == "Cross_Reference_Names" and "crossReferences" in entry:
                    # Special handling for cross references
                    list_of_entries = []
                    for key in entry['crossReferences']:
                        for elem in entry['crossReferences'][key]:
                            list_of_entries.append(f'{key}:{elem}')
                    dictionary_of_molecules[field].append(list_of_entries if list_of_entries else ["No record"])
                else:
                    value = entry.get(source_field, "No record")
                    # Check for empty string and replace with "No record"
                    dictionary_of_molecules[field].append(value if value != "" else "No record")
            
    return dictionary_of_molecules

def create_links_to_disease_targets(moleculed_df):
    """
    Create relationship DataFrames from molecule data
    
    Args:
        moleculed_df (pd.DataFrame): DataFrame with molecule data
        
    Returns:
        tuple: (molecule_df, target_relationships_df, disease_relationships_df)
    """
    # Prepare molecule DataFrame
    molecule_columns = [':ID', 'CHEMBL_ID', 'Name', 'Synonym_Names', 'Cross_Reference_Names', 
                      'Canonical_Smiles', 'Drug_Type', 'Description', 'Max_Clinicial_Trial_Phase', 
                      'is_Approved', 'Embedding', 'Embedding_Source', ':LABEL']
    molecule_df = moleculed_df[molecule_columns]
    
    # Create target relationships
    sub_molecule_df_1 = moleculed_df[[':ID', 'Linked_Targets']]
    sub_molecule_df_1 = sub_molecule_df_1.explode('Linked_Targets')
    sub_molecule_df_1[':START_ID'] = sub_molecule_df_1[':ID']
    sub_molecule_df_1[':END_ID'] = sub_molecule_df_1['Linked_Targets']
    sub_molecule_df_1['score'] = 1.0
    sub_molecule_df_1[':TYPE'] = "Known_Molecule_Link_To_Target"
    target_relationships = sub_molecule_df_1[[':START_ID', 'score', ':END_ID', ':TYPE']]
    
    # Create disease relationships
    sub_molecule_df_2 = moleculed_df[[':ID', 'Linked_Diseases']]
    sub_molecule_df_2 = sub_molecule_df_2.explode('Linked_Diseases')
    sub_molecule_df_2[':START_ID'] = sub_molecule_df_2[':ID']
    sub_molecule_df_2[':END_ID'] = sub_molecule_df_2['Linked_Diseases']
    sub_molecule_df_2['score'] = 1.0
    sub_molecule_df_2[':TYPE'] = "Known_Molecule_Link_To_Disease"
    disease_relationships = sub_molecule_df_2[[':START_ID', 'score', ':END_ID', ':TYPE']]
    
    return molecule_df, target_relationships, disease_relationships

def create_molecule_data(data_path, embedding_path):
    """
    Create DataFrames with molecule data and relationships
    
    Args:
        data_path (str): Path to the directory with molecule JSON files
        embedding_path (str): Path to the embedding CSV file
        
    Returns:
        tuple: (molecule_df, target_relationships_df, disease_relationships_df)
    """
    list_of_dataframes = []
    for path in glob.glob(data_path + "*.json"):
        molecule_dict = extract_molecule_aspects(path, embedding_path)
        list_of_dataframes.append(pd.DataFrame(molecule_dict))
    
    if not list_of_dataframes:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
    molecule_pd = pd.concat(list_of_dataframes, axis=0, ignore_index=True)
    return create_links_to_disease_targets(molecule_pd)