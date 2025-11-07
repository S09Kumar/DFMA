"""
Script to check the current status of a feature
"""
from convert_tasks_to_pbis import WorkItemConverter


def check_feature_status(feature_id: int):
    """Check the current work items under a feature"""
    client = WorkItemConverter()

    print(f"\nChecking Feature {feature_id} Status")
    print("="*70)

    # Get feature details
    feature = client.get_work_item_details(feature_id)
    feature_title = feature['fields'].get('System.Title', 'Unknown')
    print(f"\nFeature {feature_id}: {feature_title}\n")

    # Get all children
    relations = feature.get('relations', [])

    if not relations:
        print("No child work items found.")
        return

    children = []
    for relation in relations:
        if relation.get('rel') == 'System.LinkTypes.Hierarchy-Forward':
            try:
                child_url = relation.get('url', '')
                child_id = int(child_url.split('/')[-1])
                child = client.get_work_item_details(child_id)
                children.append(child)
            except Exception as e:
                print(f"Warning: Could not retrieve child from {child_url}: {e}")

    if not children:
        print("No active child work items found.")
        return

    print(f"Active Child Work Items ({len(children)} total):")
    print("-"*70)

    # Group by work item type
    by_type = {}
    for child in children:
        work_item_type = child['fields'].get('System.WorkItemType', 'Unknown')
        if work_item_type not in by_type:
            by_type[work_item_type] = []
        by_type[work_item_type].append(child)

    # Display grouped results
    for work_item_type, items in sorted(by_type.items()):
        print(f"\n{work_item_type}s ({len(items)}):")
        for item in items:
            item_id = item['id']
            title = item['fields'].get('System.Title', 'Untitled')
            state = item['fields'].get('System.State', 'Unknown')
            print(f"  {item_id}: {title} [{state}]")

    print("\n" + "="*70)


if __name__ == "__main__":
    FEATURE_ID = 2140
    check_feature_status(FEATURE_ID)
