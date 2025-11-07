"""
Script to delete work items from Azure DevOps
"""
from convert_tasks_to_pbis import WorkItemConverter
import requests


class WorkItemDeleter(WorkItemConverter):
    """Extended client for deleting work items"""

    def delete_work_item(self, work_item_id: int) -> bool:
        """Delete a work item (moves to recycle bin)"""
        endpoint = f"_apis/wit/workitems/{work_item_id}?api-version={self.api_version}"
        url = f"{self.org_url}/{endpoint}"

        try:
            response = requests.delete(url, headers=self.headers)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error deleting work item {work_item_id}: {e}")
            return False

    def delete_work_items(self, work_item_ids: list):
        """Delete multiple work items"""
        print(f"\n{'='*70}")
        print(f"Deleting Work Items")
        print(f"{'='*70}\n")

        deleted = []
        failed = []

        for work_item_id in work_item_ids:
            print(f"Processing work item {work_item_id}...")

            try:
                # Get work item details first
                work_item = self.get_work_item_details(work_item_id)
                work_item_type = work_item['fields'].get('System.WorkItemType', 'Unknown')
                title = work_item['fields'].get('System.Title', 'Untitled')

                print(f"  Type: {work_item_type}")
                print(f"  Title: {title}")

                # Delete the work item
                if self.delete_work_item(work_item_id):
                    print(f"  ✓ Successfully deleted work item {work_item_id}\n")
                    deleted.append({
                        'id': work_item_id,
                        'type': work_item_type,
                        'title': title
                    })
                else:
                    print(f"  ✗ Failed to delete work item {work_item_id}\n")
                    failed.append(work_item_id)

            except Exception as e:
                print(f"  ✗ Error: {e}\n")
                failed.append(work_item_id)

        # Summary
        print(f"{'='*70}")
        print(f"Deletion Summary")
        print(f"{'='*70}")
        print(f"Total work items: {len(work_item_ids)}")
        print(f"Successfully deleted: {len(deleted)}")
        print(f"Failed: {len(failed)}\n")

        if deleted:
            print("Deleted work items:")
            for item in deleted:
                print(f"  {item['id']} ({item['type']}): {item['title']}")

        if failed:
            print("\nFailed deletions:")
            for item_id in failed:
                print(f"  {item_id}")

        print("\nNote: Deleted work items are moved to the Recycle Bin and can be restored.")

        return deleted, failed


def main():
    """Main function"""
    # Work items to delete
    WORK_ITEM_IDS = [2141, 2144]

    print("Azure DevOps Work Item Deleter")
    print("="*70)
    print(f"Work items to delete: {WORK_ITEM_IDS}")

    # Initialize deleter
    deleter = WorkItemDeleter()

    # Perform deletion
    deleter.delete_work_items(WORK_ITEM_IDS)


if __name__ == "__main__":
    main()
