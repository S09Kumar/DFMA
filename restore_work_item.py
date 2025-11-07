"""
Script to restore work items from Azure DevOps Recycle Bin
"""
from convert_tasks_to_pbis import WorkItemConverter
import requests


class WorkItemRestorer(WorkItemConverter):
    """Extended client for restoring work items from recycle bin"""

    def restore_work_item(self, work_item_id: int) -> bool:
        """Restore a work item from the recycle bin"""
        # Using the restore API endpoint - PATCH with empty body to restore
        patch_document = {"IsDeleted": False}

        endpoint = f"_apis/wit/recyclebin/{work_item_id}?api-version={self.api_version}"
        url = f"{self.org_url}/{endpoint}"

        try:
            response = requests.patch(url, headers=self.headers, json=patch_document)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error restoring work item {work_item_id}: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return False

    def restore_work_items(self, work_item_ids: list):
        """Restore multiple work items"""
        print(f"\n{'='*70}")
        print(f"Restoring Work Items from Recycle Bin")
        print(f"{'='*70}\n")

        restored = []
        failed = []

        for work_item_id in work_item_ids:
            print(f"Restoring work item {work_item_id}...")

            try:
                if self.restore_work_item(work_item_id):
                    print(f"  ✓ Successfully restored work item {work_item_id}\n")
                    restored.append(work_item_id)
                else:
                    print(f"  ✗ Failed to restore work item {work_item_id}\n")
                    failed.append(work_item_id)
            except Exception as e:
                print(f"  ✗ Error: {e}\n")
                failed.append(work_item_id)

        # Summary
        print(f"{'='*70}")
        print(f"Restoration Summary")
        print(f"{'='*70}")
        print(f"Total work items: {len(work_item_ids)}")
        print(f"Successfully restored: {len(restored)}")
        print(f"Failed: {len(failed)}\n")

        if restored:
            print("Restored work items:")
            for item_id in restored:
                print(f"  {item_id}")

        if failed:
            print("\nFailed restorations:")
            for item_id in failed:
                print(f"  {item_id}")

        return restored, failed


def main():
    """Main function"""
    # Work item to restore
    WORK_ITEM_IDS = [2144]  # PBI 2144: Vendor Summary Report Page

    print("Azure DevOps Work Item Restorer")
    print("="*70)
    print(f"Work items to restore: {WORK_ITEM_IDS}")

    # Initialize restorer
    restorer = WorkItemRestorer()

    # Perform restoration
    restorer.restore_work_items(WORK_ITEM_IDS)


if __name__ == "__main__":
    main()
