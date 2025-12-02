"""
Query dispatcher - No intent recognition
Routes queries to appropriate data sources based on source matching
"""
from typing import List, Dict
from app.engine.targets import extract_targets
from app.sources.tabular_combined import TabularCombinedSource
from app.sources.profiles_iframe import ProfilesIframeSource

# Registered data sources (priority-ordered)
SOURCES = [
    TabularCombinedSource(),   # Priority 10 - tables first
    ProfilesIframeSource(),    # Priority 50 - iframe fallback
]


def run_query(query: str) -> Dict:
    """
    Run query through dispatcher (no intent recognition)
    
    Process:
    1. Extract targets (countries/regions)
    2. Find matching sources
    3. Fetch results from all matching sources
    4. Return aggregated results
    
    Args:
        query: User query string
        
    Returns:
        Dict with targets and hits
    """
    # Step 1: Extract targets
    targets = extract_targets(query)
    print(f"🎯 Extracted targets: {targets}")
    
    # Step 2 & 3: Find matching sources and fetch results
    all_hits: List[Dict] = []
    
    # Sort sources by priority (lower number = higher priority)
    for source in sorted(SOURCES, key=lambda s: s.priority):
        if source.matches(query):
            source_name = source.__class__.__name__
            print(f"✓ Source matched: {source_name} (priority: {source.priority})")
            
            try:
                hits = source.fetch(query, targets)
                print(f"  → Fetched {len(hits)} results")
                all_hits.extend(hits)
            except Exception as e:
                print(f"  ⚠️  Error fetching from {source_name}: {e}")
        else:
            source_name = source.__class__.__name__
            print(f"✗ Source not matched: {source_name}")
    
    # Step 4: Return results
    return {
        "targets": targets,
        "hits": all_hits,
    }


# --- Test function ---
def _test_dispatcher():
    """Test dispatcher with sample queries"""
    test_queries = [
        "Saudi Arabia wildfires",
        "China commitments",
        "MENA legislation",
        "Ghana restoration pledge",
        "global climate trends",
    ]
    
    print("=" * 80)
    print("Testing Query Dispatcher (No Intent)")
    print("=" * 80)
    
    for query in test_queries:
        print(f"\n{'=' * 80}")
        print(f"📝 Query: '{query}'")
        print(f"{'=' * 80}")
        
        result = run_query(query)
        
        print(f"\n📊 Results:")
        print(f"   Targets: {result['targets']}")
        print(f"   Hits: {len(result['hits'])} results")
        
        for i, hit in enumerate(result['hits'], 1):
            hit_type = hit.get('type', 'unknown')
            title = hit.get('title', 'N/A')
            print(f"     {i}. [{hit_type}] {title}")


if __name__ == "__main__":
    _test_dispatcher()
