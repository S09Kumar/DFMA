"""
Script to query work items assigned to a specific user
"""
from convert_tasks_to_pbis import WorkItemConverter
import requests


class UserWorkItemQuery(WorkItemConverter):
    """Extended client for querying user work items"""

    def get_user_work_items(self, project_name: str, user_email: str, work_item_types: list = None):
        """Get work items assigned to a specific user"""
        if work_item_types is None:
            work_item_types = ['Feature', 'Product Backlog Item']

        # Build WIQL query
        types_clause = ", ".join([f"'{wit}'" for wit in work_item_types])
        wiql_query = f"""
        SELECT [System.Id], [System.WorkItemType], [System.Title], [System.State],
               [System.AssignedTo], [System.AreaPath], [System.IterationPath],
               [Microsoft.VSTS.Scheduling.Effort], [Microsoft.VSTS.Common.Priority]
        FROM WorkItems
        WHERE [System.TeamProject] = '{project_name}'
        AND [System.WorkItemType] IN ({types_clause})
        AND [System.AssignedTo] = '{user_email}'
        ORDER BY [System.WorkItemType], [System.ChangedDate] DESC
        """

        endpoint = f"{project_name}/_apis/wit/wiql?api-version={self.api_version}"
        url = f"{self.org_url}/{endpoint}"

        data = {"query": wiql_query}

        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            result = response.json()

            work_items = result.get('workItems', [])

            # Get full details for each work item
            detailed_items = []
            for item in work_items:
                work_item_id = item['id']
                details = self.get_work_item_details(work_item_id)
                detailed_items.append(details)

            return detailed_items

        except Exception as e:
            print(f"Error querying work items: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return []

    def display_user_work_items(self, project_name: str, user_email: str):
        """Display all features and PBIs for a user"""
        print(f"\n{'='*80}")
        print(f"Work Items for: {user_email}")
        print(f"Project: {project_name}")
        print(f"{'='*80}\n")

        work_items = self.get_user_work_items(project_name, user_email)

        if not work_items:
            print("No Features or Product Backlog Items found for this user.")
            return

        # Group by work item type
        by_type = {}
        for item in work_items:
            work_item_type = item['fields'].get('System.WorkItemType', 'Unknown')
            if work_item_type not in by_type:
                by_type[work_item_type] = []
            by_type[work_item_type].append(item)

        # Display Features
        if 'Feature' in by_type:
            features = by_type['Feature']
            print(f"FEATURES ({len(features)}):")
            print("-"*80)
            for i, feature in enumerate(features, 1):
                self._display_work_item(feature, i)
            print()

        # Display Product Backlog Items
        if 'Product Backlog Item' in by_type:
            pbis = by_type['Product Backlog Item']
            print(f"PRODUCT BACKLOG ITEMS ({len(pbis)}):")
            print("-"*80)
            for i, pbi in enumerate(pbis, 1):
                self._display_work_item(pbi, i)
            print()

        # Summary
        total = len(work_items)
        features_count = len(by_type.get('Feature', []))
        pbis_count = len(by_type.get('Product Backlog Item', []))

        print("="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Total Work Items: {total}")
        print(f"  Features: {features_count}")
        print(f"  Product Backlog Items: {pbis_count}")

    def _display_work_item(self, item: dict, index: int):
        """Display a single work item with formatting"""
        fields = item.get('fields', {})

        item_id = item['id']
        title = fields.get('System.Title', 'Untitled')
        state = fields.get('System.State', 'Unknown')
        area_path = fields.get('System.AreaPath', 'N/A')
        iteration = fields.get('System.IterationPath', 'N/A')
        effort = fields.get('Microsoft.VSTS.Scheduling.Effort', 'N/A')
        priority = fields.get('Microsoft.VSTS.Common.Priority', 'N/A')

        print(f"\n{index}. [{item_id}] {title}")
        print(f"   State: {state}")
        print(f"   Area: {area_path}")
        print(f"   Iteration: {iteration}")
        print(f"   Effort: {effort} | Priority: {priority}")

        # Get parent if exists
        relations = item.get('relations', [])
        for relation in relations:
            if relation.get('rel') == 'System.LinkTypes.Hierarchy-Reverse':
                parent_url = relation.get('url', '')
                parent_id = int(parent_url.split('/')[-1])
                try:
                    parent = self.get_work_item_details(parent_id)
                    parent_type = parent['fields'].get('System.WorkItemType', 'Unknown')
                    parent_title = parent['fields'].get('System.Title', 'Unknown')
                    print(f"   Parent: [{parent_id}] {parent_type}: {parent_title}")
                except:
                    pass

        # Get children count
        children_count = sum(1 for r in relations if r.get('rel') == 'System.LinkTypes.Hierarchy-Forward')
        if children_count > 0:
            print(f"   Child Work Items: {children_count}")


def main():
    """Main function"""
    PROJECT_NAME = "IS-Operations"
    USER_EMAIL = "VendorMuruganantham@rlgbuilds.onmicrosoft.com"

    print("Azure DevOps User Work Items Query")
    print("="*80)

    # Initialize query client
    client = UserWorkItemQuery()

    # Display work items
    client.display_user_work_items(PROJECT_NAME, USER_EMAIL)


if __name__ == "__main__":
    main()
