"""
Script to verify the conversion was successful
"""
from convert_tasks_to_pbis import WorkItemConverter


def verify_conversion(feature_id: int, new_pbi_ids: list):
    """Verify that the new PBIs are properly linked to the feature"""
    client = WorkItemConverter()

    print(f"\nVerifying conversion for Feature {feature_id}")
    print("="*70)

    # Get feature and its children
    feature = client.get_work_item_details(feature_id)
    feature_title = feature['fields'].get('System.Title', 'Unknown')
    print(f"\nFeature {feature_id}: {feature_title}\n")

    # Get all children
    relations = feature.get('relations', [])
    children = []

    for relation in relations:
        if relation.get('rel') == 'System.LinkTypes.Hierarchy-Forward':
            child_url = relation.get('url', '')
            child_id = int(child_url.split('/')[-1])
            child = client.get_work_item_details(child_id)
            children.append(child)

    print(f"Child Work Items ({len(children)} total):")
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
            marker = "✓ NEW" if item_id in new_pbi_ids else ""
            print(f"  {item_id}: {title} [{state}] {marker}")

    # Check if new PBIs are present
    print("\n" + "="*70)
    print("Verification Results:")
    print("="*70)

    pbi_ids = [child['id'] for child in children if child['fields'].get('System.WorkItemType') == 'Product Backlog Item']

    all_found = all(pbi_id in pbi_ids for pbi_id in new_pbi_ids)

    if all_found:
        print("✓ All new PBIs are properly linked to the feature")
        print(f"✓ Feature now has {len(pbi_ids)} Product Backlog Item(s)")
    else:
        print("✗ Some PBIs may not be properly linked")

    return all_found


if __name__ == "__main__":
    # Verify the conversion
    FEATURE_ID = 2140
    NEW_PBI_IDS = [2143, 2144]  # From the conversion output

    verify_conversion(FEATURE_ID, NEW_PBI_IDS)
