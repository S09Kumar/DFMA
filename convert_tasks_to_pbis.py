"""
Script to convert tasks under a feature to Product Backlog Items
"""
from azure_devops_client import AzureDevOpsClient
import requests
import json


class WorkItemConverter(AzureDevOpsClient):
    """Extended client for converting work items"""

    def get_work_item_details(self, work_item_id: int) -> dict:
        """Get detailed information about a work item"""
        endpoint = f"_apis/wit/workitems/{work_item_id}?$expand=all&api-version={self.api_version}"
        return self._make_request(endpoint)

    def get_child_work_items(self, parent_id: int) -> list:
        """Get all child work items of a parent"""
        # First get the parent work item to find children
        parent = self.get_work_item_details(parent_id)

        children = []
        relations = parent.get('relations', [])

        for relation in relations:
            if relation.get('rel') == 'System.LinkTypes.Hierarchy-Forward':
                # Extract work item ID from URL
                child_url = relation.get('url', '')
                child_id = int(child_url.split('/')[-1])
                child_details = self.get_work_item_details(child_id)
                children.append(child_details)

        return children

    def create_pbi_from_task(self, task: dict, parent_feature_id: int, project_name: str) -> dict:
        """Create a Product Backlog Item from a task"""
        # Prepare the fields for the new PBI
        fields = task.get('fields', {})

        # Build JSON Patch document for creating PBI
        patch_document = [
            {
                "op": "add",
                "path": "/fields/System.Title",
                "value": fields.get('System.Title', 'Untitled')
            },
            {
                "op": "add",
                "path": "/fields/System.WorkItemType",
                "value": "Product Backlog Item"
            }
        ]

        # Add optional fields if they exist
        if fields.get('System.Description'):
            patch_document.append({
                "op": "add",
                "path": "/fields/System.Description",
                "value": fields.get('System.Description')
            })

        if fields.get('System.AssignedTo'):
            patch_document.append({
                "op": "add",
                "path": "/fields/System.AssignedTo",
                "value": fields.get('System.AssignedTo').get('uniqueName')
            })

        if fields.get('System.Tags'):
            patch_document.append({
                "op": "add",
                "path": "/fields/System.Tags",
                "value": fields.get('System.Tags')
            })

        if fields.get('Microsoft.VSTS.Scheduling.Effort'):
            patch_document.append({
                "op": "add",
                "path": "/fields/Microsoft.VSTS.Scheduling.Effort",
                "value": fields.get('Microsoft.VSTS.Scheduling.Effort')
            })

        if fields.get('Microsoft.VSTS.Common.Priority'):
            patch_document.append({
                "op": "add",
                "path": "/fields/Microsoft.VSTS.Common.Priority",
                "value": fields.get('Microsoft.VSTS.Common.Priority')
            })

        # Add area path and iteration path
        if fields.get('System.AreaPath'):
            patch_document.append({
                "op": "add",
                "path": "/fields/System.AreaPath",
                "value": fields.get('System.AreaPath')
            })

        if fields.get('System.IterationPath'):
            patch_document.append({
                "op": "add",
                "path": "/fields/System.IterationPath",
                "value": fields.get('System.IterationPath')
            })

        # Link to parent feature
        patch_document.append({
            "op": "add",
            "path": "/relations/-",
            "value": {
                "rel": "System.LinkTypes.Hierarchy-Reverse",
                "url": f"{self.org_url}/_apis/wit/workItems/{parent_feature_id}"
            }
        })

        # Create the PBI
        endpoint = f"{project_name}/_apis/wit/workitems/$Product Backlog Item?api-version={self.api_version}"
        url = f"{self.org_url}/{endpoint}"

        headers = self.headers.copy()
        headers['Content-Type'] = 'application/json-patch+json'

        response = requests.post(url, headers=headers, json=patch_document)
        response.raise_for_status()

        return response.json()

    def update_work_item_state(self, work_item_id: int, state: str, project_name: str) -> dict:
        """Update the state of a work item"""
        patch_document = [
            {
                "op": "add",
                "path": "/fields/System.State",
                "value": state
            }
        ]

        endpoint = f"_apis/wit/workitems/{work_item_id}?api-version={self.api_version}"
        url = f"{self.org_url}/{endpoint}"

        headers = self.headers.copy()
        headers['Content-Type'] = 'application/json-patch+json'

        response = requests.patch(url, headers=headers, json=patch_document)
        response.raise_for_status()

        return response.json()

    def convert_tasks_to_pbis(self, feature_id: int, project_name: str, close_old_tasks: bool = False):
        """Convert all tasks under a feature to Product Backlog Items"""
        print(f"\n{'='*70}")
        print(f"Converting Tasks to PBIs for Feature {feature_id}")
        print(f"{'='*70}\n")

        # Get feature details
        print(f"Retrieving feature {feature_id}...")
        feature = self.get_work_item_details(feature_id)
        feature_title = feature['fields'].get('System.Title', 'Unknown')
        print(f"✓ Feature: {feature_title}\n")

        # Get child tasks
        print("Retrieving child work items...")
        children = self.get_child_work_items(feature_id)
        tasks = [child for child in children if child['fields'].get('System.WorkItemType') == 'Task']

        print(f"✓ Found {len(tasks)} task(s) to convert\n")

        if not tasks:
            print("No tasks found under this feature.")
            return

        # Convert each task
        converted = []
        for i, task in enumerate(tasks, 1):
            task_id = task['id']
            task_title = task['fields'].get('System.Title', 'Untitled')

            print(f"{i}. Converting Task {task_id}: {task_title}")

            try:
                # Create new PBI
                new_pbi = self.create_pbi_from_task(task, feature_id, project_name)
                new_pbi_id = new_pbi['id']

                print(f"   ✓ Created PBI {new_pbi_id}")

                # Optionally close the old task
                if close_old_tasks:
                    self.update_work_item_state(task_id, 'Closed', project_name)
                    print(f"   ✓ Closed old Task {task_id}")

                converted.append({
                    'old_task_id': task_id,
                    'new_pbi_id': new_pbi_id,
                    'title': task_title
                })

                print(f"   ✓ Conversion complete\n")

            except Exception as e:
                print(f"   ✗ Error converting task {task_id}: {e}\n")

        # Summary
        print(f"{'='*70}")
        print(f"Conversion Summary")
        print(f"{'='*70}")
        print(f"Total tasks: {len(tasks)}")
        print(f"Successfully converted: {len(converted)}")
        print(f"Failed: {len(tasks) - len(converted)}\n")

        if converted:
            print("Converted work items:")
            for item in converted:
                print(f"  Task {item['old_task_id']} → PBI {item['new_pbi_id']}: {item['title']}")

        return converted


def main():
    """Main function"""
    # Configuration
    FEATURE_ID = 2140
    PROJECT_NAME = "IS-Operations"
    CLOSE_OLD_TASKS = False  # Set to True to close old tasks after conversion

    print("Azure DevOps Work Item Converter")
    print("="*70)

    # Initialize converter
    converter = WorkItemConverter()

    # Perform conversion
    converter.convert_tasks_to_pbis(
        feature_id=FEATURE_ID,
        project_name=PROJECT_NAME,
        close_old_tasks=CLOSE_OLD_TASKS
    )


if __name__ == "__main__":
    main()
