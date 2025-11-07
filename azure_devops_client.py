"""
Azure DevOps REST API Client for RLG-Analytics Organization
"""
import os
import base64
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AzureDevOpsClient:
    """Client for interacting with Azure DevOps REST API"""

    def __init__(self):
        """Initialize the Azure DevOps client with credentials from .env"""
        self.org_name = os.getenv('AZURE_DEVOPS_ORG')
        self.pat = os.getenv('AZURE_DEVOPS_PAT')
        self.org_url = os.getenv('AZURE_DEVOPS_ORG_URL')

        if not all([self.org_name, self.pat, self.org_url]):
            raise ValueError("Missing required environment variables. Check your .env file.")

        # Create authorization header
        auth_string = f":{self.pat}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        self.headers = {
            'Authorization': f'Basic {encoded_auth}',
            'Content-Type': 'application/json'
        }

        self.api_version = '7.1'

    def _make_request(self, endpoint: str, method: str = 'GET', data: Optional[Dict] = None) -> Dict:
        """Make a request to Azure DevOps REST API"""
        url = f"{self.org_url}/{endpoint}"

        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            print(f"Response: {response.text}")
            raise
        except Exception as e:
            print(f"Error making request: {e}")
            raise

    def test_connection(self) -> bool:
        """Test the connection to Azure DevOps"""
        try:
            projects = self.get_projects()
            print(f"✓ Successfully connected to {self.org_name}")
            print(f"✓ Found {len(projects)} project(s)")
            return True
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False

    def get_projects(self) -> List[Dict]:
        """Get all projects in the organization"""
        endpoint = f"_apis/projects?api-version={self.api_version}"
        result = self._make_request(endpoint)
        return result.get('value', [])

    def get_project_details(self, project_name: str) -> Dict:
        """Get details of a specific project"""
        endpoint = f"_apis/projects/{project_name}?api-version={self.api_version}"
        return self._make_request(endpoint)

    def get_repositories(self, project_name: str) -> List[Dict]:
        """Get all repositories in a project"""
        endpoint = f"{project_name}/_apis/git/repositories?api-version={self.api_version}"
        result = self._make_request(endpoint)
        return result.get('value', [])

    def get_work_items(self, project_name: str, wiql_query: Optional[str] = None) -> List[Dict]:
        """Get work items using WIQL query"""
        if wiql_query is None:
            # Default query: get recent work items
            wiql_query = f"SELECT [System.Id], [System.Title], [System.State] FROM WorkItems WHERE [System.TeamProject] = '{project_name}' ORDER BY [System.ChangedDate] DESC"

        endpoint = f"{project_name}/_apis/wit/wiql?api-version={self.api_version}"
        data = {"query": wiql_query}
        result = self._make_request(endpoint, method='POST', data=data)
        return result.get('workItems', [])

    def get_builds(self, project_name: str, top: int = 10) -> List[Dict]:
        """Get recent builds for a project"""
        endpoint = f"{project_name}/_apis/build/builds?api-version={self.api_version}&$top={top}"
        result = self._make_request(endpoint)
        return result.get('value', [])

    def get_pipelines(self, project_name: str) -> List[Dict]:
        """Get all pipelines in a project"""
        endpoint = f"{project_name}/_apis/pipelines?api-version={self.api_version}"
        result = self._make_request(endpoint)
        return result.get('value', [])

    def print_projects_summary(self):
        """Print a summary of all projects"""
        print("\n" + "="*60)
        print(f"Projects in {self.org_name}")
        print("="*60)

        projects = self.get_projects()
        for i, project in enumerate(projects, 1):
            print(f"\n{i}. {project['name']}")
            print(f"   ID: {project['id']}")
            print(f"   Description: {project.get('description', 'N/A')}")
            print(f"   State: {project.get('state', 'N/A')}")
            print(f"   Visibility: {project.get('visibility', 'N/A')}")
            print(f"   URL: {project.get('url', 'N/A')}")

    def print_repositories_summary(self, project_name: str):
        """Print a summary of all repositories in a project"""
        print("\n" + "="*60)
        print(f"Repositories in {project_name}")
        print("="*60)

        repos = self.get_repositories(project_name)
        for i, repo in enumerate(repos, 1):
            print(f"\n{i}. {repo['name']}")
            print(f"   ID: {repo['id']}")
            print(f"   Default Branch: {repo.get('defaultBranch', 'N/A')}")
            print(f"   Size: {repo.get('size', 0)} bytes")
            print(f"   Web URL: {repo.get('webUrl', 'N/A')}")


def main():
    """Main function to demonstrate Azure DevOps client usage"""
    print("Azure DevOps Client - RLG-Analytics Organization")
    print("="*60)

    # Initialize client
    client = AzureDevOpsClient()

    # Test connection
    print("\nTesting connection...")
    if client.test_connection():
        print("\n✓ Connection successful!")

        # Print projects summary
        client.print_projects_summary()

        # Get first project and list its repositories
        projects = client.get_projects()
        if projects:
            first_project = projects[0]['name']
            client.print_repositories_summary(first_project)
    else:
        print("\n✗ Connection failed. Please check your credentials.")


if __name__ == "__main__":
    main()
