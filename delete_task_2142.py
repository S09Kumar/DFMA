"""
Script to delete Task 2142
"""
from delete_work_items import WorkItemDeleter


def main():
    """Main function"""
    # Task to delete
    WORK_ITEM_IDS = [2142]

    print("Azure DevOps Work Item Deleter")
    print("="*70)
    print(f"Work items to delete: {WORK_ITEM_IDS}")

    # Initialize deleter
    deleter = WorkItemDeleter()

    # Perform deletion
    deleter.delete_work_items(WORK_ITEM_IDS)


if __name__ == "__main__":
    main()
