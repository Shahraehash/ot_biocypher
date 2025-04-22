# ot_biocypher - Development of an Open Targets Biocypher for Neo4j Adaptation

This project creates a biological knowledge graph from OpenTargets data and loads it into a Neo4j database. The knowledge graph captures relationships between diseases, targets, and molecules, providing a comprehensive resource for drug discovery and biomedical research.

## Overview

The pipeline processes OpenTargets data through the following steps:
1. Download raw JSON data from OpenTargets FTP server
2. Generate molecular embeddings using Recursion's MolE foundation model
3. Process and transform the data into a graph structure
4. Generate CSV files for Neo4j import
5. Deploy the knowledge graph to a remote Neo4j instance

## Prerequisites

- Python 3.7+
- pandas
- paramiko (for SSH operations)
- Access to a Neo4j instance
- Recursion's MolE foundation model (for generating molecular embeddings)

## Installation

Clone this repository and install the required dependencies:

```bash
git clone <repository-url>
cd ot_biocypher
```

## Usage

### 1. Download OpenTargets Data

Run the provided shell script to download data from the OpenTargets FTP server:

```bash
bash json_download.sh
```

This will download JSON files for targets, diseases, molecules, and evidence into the `data/` directory.

### 2. Generate Molecular Embeddings

Generate molecular embeddings using Recursion's MolE foundation model. The embeddings should be saved as:

```
data/Molecule_Embeddings.csv
```

This output CSV file should contain the following columns:
- `chembl_id`: The ChEMBL ID of the molecule
- `canonical_smiles`: The canonical SMILES
- `embedding`: The vector embedding of the molecule

You can access the pretrained model code at: https://codeocean.com/capsule/2105466/tree/v1. In `How_to_use_MolE.ipynb`, 
add a cell at the bottom that copies the information from `generate_molecular_embeddings_mole.ipynb`. For the input data, provide a CSV with two columns: `chembl_ids` and `canonical_smiles`. 


### 3. Construct Knowledge Graph

Run the knowledge graph construction script:

```bash
python construct_KG.py
```

This script will:
- Process disease, target, molecule, and evidence data
- Generate the following CSV files in the `neo4j_data/` directory:
  - `Disease.csv`: Node data for diseases
  - `Molecule.csv`: Node data for molecules
  - `Targets.csv`: Node data for targets
  - `Relationships.csv`: Edge data connecting nodes
- Create a Neo4j import command in `neo4j_txt_command.txt`

### 4. Deploy to Remote Neo4j Instance

To deploy the knowledge graph to a remote Neo4j instance:

```bash
python add_KG_to_remote.py
```

This script will:
- Connect to the remote server via SSH
- Upload CSV files to the Neo4j import directory
- Execute the import command to load the data into Neo4j

## Data Structure

### Node Types
- **Disease**: Represents a disease or condition
- **Target**: Represents a biological target (typically a protein)
- **Molecule**: Represents a chemical compound or drug

### Relationship Types
- **Known_Molecule_Link_To_Target**: Links molecules to their target proteins
- **Known_Molecule_Link_To_Disease**: Links molecules to diseases they treat
- Various evidence-based relationships from OpenTargets sources

## Configuration

The data processing is configured through `adapter_config.json`, which defines:
- Required fields for each node type
- Field mappings between source data and graph properties
- Evidence source configurations


## Acknowledgments

- OpenTargets for providing the data
- Recursion for the MolE foundation model