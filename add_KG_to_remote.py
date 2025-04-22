import paramiko
import os
from dotenv import load_dotenv

load_dotenv()

# Remote server connection details from environment variables
hostname = os.getenv("HOSTNAME")
username = os.getenv("USERNAME")
ssh_key_path = os.getenv("SSH_KEY_PATH")
port = int(os.getenv("PORT", 22))  # Default to 22 if not specified
passphrase = os.getenv("PASSPHRASE")

# Path to CSV files on local machine
local_files = [
    "neo4j_data/Disease.csv",
    "neo4j_data/Molecule.csv", 
    "neo4j_data/Targets.csv",
    "neo4j_data/Relationships.csv"
]

# Remote paths
remote_import_dir = "/var/lib/neo4j/import/"

# Function to read the generated bash script
def read_import_command(script_path="neo4j_txt_command.txt"):
    try:
        with open(script_path, 'r') as f:
            import_command = f.read().strip()
        return import_command
    except FileNotFoundError:
        print(f"Error: Command file {script_path} not found. Make sure to run construct_KG.py first.")
        return None

# Establish SSH connection with key authentication
def connect_ssh(hostname, port, username, key_path, passphrase):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Load private key
    try:
        key = paramiko.Ed25519Key.from_private_key_file(filename=key_path, password=passphrase)
        ssh.connect(hostname, port, username, pkey=key)
        print(f"Successfully connected to {hostname}")
        return ssh
    except Exception as e:
        print(f"Error connecting to {hostname}: {e}")
        return None

# Upload files to remote server
def upload_files(sftp, local_files, remote_dir):
    for file in local_files:
        try:
            local_path = file
            remote_path = os.path.join(remote_dir, file)
            sftp.put(local_path, remote_path)
            print(f"Uploaded {file} to {remote_path}")
        except Exception as e:
            print(f"Error uploading {file}: {e}")

# Main execution
if __name__ == "__main__":
    # Read the import command from the generated script
    import_command = read_import_command()
    if not import_command:
        exit(1)
    
    # Connect to SSH
    ssh = connect_ssh(hostname, port, username, ssh_key_path, passphrase)
    if not ssh:
        exit(1)
    
    # Open SFTP connection
    try:
        sftp = ssh.open_sftp()
        
        # Upload CSV files to remote server
        print("Uploading files...")
        upload_files(sftp, local_files, remote_import_dir)
        
        # Execute the import command
        print(f"Executing: {import_command}")
        stdin, stdout, stderr = ssh.exec_command(import_command)
        
        # Print output
        print("Command output:")
        for line in stdout:
            print(line.strip())
        
        # Print errors, if any
        error_output = stderr.read().decode('utf-8')
        if error_output:
            print("ERROR OUTPUT:")
            print(error_output)
        
        # Close connections
        sftp.close()
        ssh.close()
        print("Operation completed.")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        try:
            sftp.close()
        except:
            pass
        try:
            ssh.close()
        except:
            pass