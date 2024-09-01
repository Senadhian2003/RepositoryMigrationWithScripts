import requests
import json
import sys
import time
import base64

def create_and_import_repo(azure_org, azure_project, repo_name, github_username, azure_pat):
    # Azure DevOps API endpoints
    create_repo_url = f"https://dev.azure.com/{azure_org}/{azure_project}/_apis/git/repositories?api-version=6.0"
    import_repo_url = f"https://dev.azure.com/{azure_org}/{azure_project}/_apis/git/repositories/{repo_name}/importRequests?api-version=6.0"

    azure_pat_encoded = base64.b64encode(f":{azure_pat}".encode()).decode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {azure_pat_encoded}"
    }

    # Create repository in Azure DevOps
    create_repo_data = {
        "name": repo_name
    }
    response = requests.post(create_repo_url, headers=headers, json=create_repo_data)
    if response.status_code != 201:
        print(f"Failed to create repository {repo_name} in Azure DevOps. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    # Import repository from GitHub
    import_repo_data = {
        "parameters": {
            "gitSource": {
                "url": f"https://github.com/{github_username}/{repo_name}"
            }
        }
    }
    response = requests.post(import_repo_url, headers=headers, json=import_repo_data)
    if response.status_code != 201:
        print(f"Failed to start import for repository {repo_name}. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    # Get the import status URL from the response
    import_status_url = response.json()['url']

    # Poll the import status
    while True:
        response = requests.get(import_status_url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to get import status for repository {repo_name}. Status code: {response.status_code}")
            return False

        status = response.json()['status']
        if status == 'completed':
            print(f"Successfully migrated {repo_name}")
            return True
        elif status == 'failed':
            print(f"Import failed for repository {repo_name}")
            return False
        else:
            print(f"Import in progress for {repo_name}. Current status: {status}")
            time.sleep(5)  # Wait for 5 seconds before checking again

def main(repo_list_file, github_username, azure_org, azure_project, azure_pat):
    with open(repo_list_file, 'r') as file:
        repos = file.read().splitlines()

    for repo in repos:
        create_and_import_repo(azure_org, azure_project, repo, github_username, azure_pat)

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: python script.py <repo_list_file> <github_username> <azure_org> <azure_project> <azure_pat>")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
