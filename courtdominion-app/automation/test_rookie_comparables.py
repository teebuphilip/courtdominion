"""
Test script for rookie comparables functionality
"""

from dbb2_projections import get_rookie_comparable, find_player_id_by_name, load_cache

if __name__ == "__main__":
    print("Testing Rookie Comparables...")

    # Load cache
    cache = load_cache()

    if not cache:
        print("ERROR: No cache found. Cannot test without cache data.")
        exit(1)

    print(f"Cache loaded: {len(cache)} players\n")

    # Test finding Anthony Davis by name
    print("Test 1: Find Anthony Davis by name")
    ad_id = find_player_id_by_name("Anthony Davis", cache)
    if ad_id:
        print(f"  ✓ Found Anthony Davis with ID: {ad_id}")
        ad_stats = cache.get(ad_id)
        if ad_stats:
            print(f"  ✓ Stats: {ad_stats.get('points_per_game')} PPG")
    else:
        print("  ✗ Anthony Davis not found in cache")

    print()

    # Test rookie comparable lookup
    print("Test 2: Get comparable for Cooper Flagg")
    comparable_id = get_rookie_comparable("Cooper Flagg", cache)
    if comparable_id:
        comparable_stats = cache.get(comparable_id)
        comparable_name = comparable_stats.get('player_name', 'Unknown') if comparable_stats else 'Unknown'
        print(f"  ✓ Found comparable: {comparable_name} (ID: {comparable_id})")
        if comparable_stats:
            print(f"  ✓ Comparable stats: {comparable_stats.get('points_per_game')} PPG")
    else:
        print("  ✗ No comparable found for Cooper Flagg")

    print("\nTest completed!")
