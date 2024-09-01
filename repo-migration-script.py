import subprocess
import os
import sys
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    return output.decode(), error.decode(), process.returncode

def create_azure_repo(organization_url, project_name, repo_name, personal_access_token):
    # Create a connection to Azure DevOps
    credentials = BasicAuthentication('', personal_access_token)
    connection = Connection(base_url=organization_url, creds=credentials)

    # Get the core client to fetch the project details
    core_client = connection.clients.get_core_client()
    project = core_client.get_project(project_name)

    if not project:
        print(f"Project {project_name} not found.")
        return None

    # Get the Git client to create the repository
    git_client = connection.clients.get_git_client()

    # Create the repo
    repo = {
        "name": repo_name,
        "project": {"id": project.id}  # Use the project ID
    }
    created_repo = git_client.create_repository(repo)
    return created_repo.remote_url

def migrate_repo(github_username, azure_account, azure_project, repo_name, azure_pat):
    print(f"Migrating repository: {repo_name}")

    # Clone the GitHub repo
    github_url = f"https://github.com/{github_username}/{repo_name}.git"
    clone_command = f"git clone --mirror {github_url} {repo_name}"
    output, error, return_code = run_command(clone_command)
    if return_code != 0:
        print(f"Error cloning repository: {error}")
        return False

    # Change to the repo directory
    os.chdir(repo_name)

    # Create the Azure DevOps repository
    azure_url = create_azure_repo(f"https://dev.azure.com/{azure_account}", azure_project, repo_name, azure_pat)
    if not azure_url:
        print(f"Error creating Azure DevOps repository for {repo_name}")
        return False

    # Push to Azure DevOps
    push_command = f"git push --mirror {azure_url}"
    output, error, return_code = run_command(push_command)
    if return_code != 0:
        print(f"Error pushing to Azure DevOps: {error}")
        return False

    # Change back to the parent directory and remove the cloned repo
    os.chdir('..')
    run_command(f"rm -rf {repo_name}")

    print(f"Successfully migrated {repo_name}")
    return True

def main(repo_list_file, github_username, azure_account, azure_project, azure_pat):
    with open(repo_list_file, 'r') as file:
        repos = file.read().splitlines()

    for repo in repos:
        migrate_repo(github_username, azure_account, azure_project, repo, azure_pat)

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: python script.py <repo_list_file> <github_username> <azure_account> <azure_project> <azure_pat>")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])