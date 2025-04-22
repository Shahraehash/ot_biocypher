from knowledge_graph_adapters.disease_adapter import create_disease_data
from knowledge_graph_adapters.evidence_adapter import create_evidence_data
from knowledge_graph_adapters.molecule_adapter import create_molecule_data
from knowledge_graph_adapters.targets_adapter import create_targets_data
from knowledge_graph_adapters.config_loader import load_config
import pandas as pd
import glob
import os
import json

def custom_max(group):
    """
    Get the row with the maximum score in a group, or the first row if no scores
    
    Args:
        group (pd.DataFrame): Group of rows
        
    Returns:
        pd.Series: Row with the maximum score or the first row
    """
    if group['score'].notna().any():  
        return group.loc[group['score'].idxmax()]
    else:
        return group.iloc[0]

def ensure_nodes_exist(relationship_df, nodes):
    """
    Ensure that all nodes in relationships exist and reorder columns
    
    Args:
        relationship_df (pd.DataFrame): DataFrame with relationships
        nodes (set): Set of node IDs
        
    Returns:
        pd.DataFrame: DataFrame with only valid relationships
    """
    # Filter relationships to only include existing nodes
    new_relationship_df = relationship_df[relationship_df[':START_ID'].isin(nodes) & relationship_df[':END_ID'].isin(nodes)]
    
    # For each group, keep the row with the maximum score
    new_relationship_df = new_relationship_df.groupby([':START_ID', ':END_ID'], group_keys=False).apply(custom_max)
    new_relationship_df = new_relationship_df.reset_index(drop=True)
    
    # Replace empty strings with "No record"
    for col in new_relationship_df.columns:
        new_relationship_df[col] = new_relationship_df[col].apply(lambda x: "No record" if x == "" else x)
    
    # Reorder columns
    middle_cols = [col for col in new_relationship_df.columns if col not in [':START_ID', ':END_ID', ':TYPE']]
    new_relationship_df_reordered = new_relationship_df[[':START_ID'] + middle_cols + [':END_ID', ':TYPE']]
    
    return new_relationship_df_reordered

def write_bash_script(node_paths, relationship_paths, output_path):
    """
    Write a Bash script for importing data into Neo4j
    
    Args:
        node_paths (list): List of node file paths
        relationship_paths (list): List of relationship file paths
        output_path (str): Path to the output script
    """
    nodes_args = ""
    for node_path in node_paths:
        nodes_args += f" --nodes={node_path}"
        
    relationships_args = ""
    for relationship_path in relationship_paths:
        relationships_args += f" --relationships={relationship_path}"

    txt_command = f"bin/neo4j-admin database import full neo4j {nodes_args} {relationships_args} --overwrite-destination --array-delimiter='|' --multiline-fields=true"
    
    with open(output_path, "w") as f:
        f.write(txt_command)

    return

if __name__ == "__main__":
    # Load configuration
    config = load_config()
    
    # Set paths
    data_path = os.environ.get("DATA_PATH", "./data/")
    save_path = os.environ.get("SAVE_PATH", "./neo4j_data/")
    
    # Ensure save path exists
    os.makedirs(save_path, exist_ok=True)
    
    print("Extracting OT data for KG")
    
    # Create disease data
    disease_df = create_disease_data(data_path + "diseases/")
    disease_df.to_csv(save_path + "Disease.csv", sep=",", index=False)
    print(f"Created Disease Dataframe: {disease_df.shape}")
    
    # Create molecule data
    molecule_df, known_target_relationships, known_disease_relationships = create_molecule_data(
        data_path + "molecule/", 
        data_path + "Molecule_Embeddings.csv"
    )
    molecule_df.to_csv(save_path + "Molecule.csv", sep=",", index=False)
    print(f"Created Molecule Dataframe: {molecule_df.shape}")
    
    # Create targets data
    targets_df = create_targets_data(data_path + "targets/")
    targets_df.to_csv(save_path + "Targets.csv", sep=",", index=False)
    print(f"Created Targets Dataframe: {targets_df.shape}")
    
    # Get all node IDs
    nodes = set(disease_df[":ID"].tolist() + molecule_df[":ID"].tolist() + targets_df[":ID"].tolist())
    
    # Create evidence data
    evidence_dfs = create_evidence_data(data_path + "evidence/", True)  # True to only include databases with drugIds
    
    # Combine all relationship DataFrames
    all_relationships = evidence_dfs + [known_target_relationships, known_disease_relationships]
    all_relationships = [df for df in all_relationships if df is not None and not df.empty]
    
    if all_relationships:
        evidence = pd.concat(all_relationships, axis=0, ignore_index=True)
        new_evidence_df = ensure_nodes_exist(evidence, nodes)
                
        # Save relationships
        new_evidence_df.to_csv(save_path + "Relationships.csv", sep=",", index=False)
        print(f"Created Evidence Dataframe: {new_evidence_df.shape}")
        
        # Create import script
        node_files = [f"import/{node}.csv" for node in ["Disease", "Molecule", "Targets"]]
            
        relationship_files = ["import/Relationships.csv"]
        write_bash_script(node_files, relationship_files, "neo4j_txt_command.txt")
        print("Created Bash Script")
    else:
        print("No valid relationships found!")