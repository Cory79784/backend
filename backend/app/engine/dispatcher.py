"""
Query dispatcher - Slot-driven data source routing
Routes queries to appropriate data sources based on slots (domain, targets, section_hint)
"""
from typing import List, Dict, Optional
from app.engine.targets import extract_targets
from app.sources.tabular_combined import TabularCombinedSource
from app.sources.profiles_iframe import ProfilesIframeSource

# Registered data sources (priority-ordered)
SOURCES = [
    TabularCombinedSource(),   # Priority 10 - tables first
    ProfilesIframeSource(),    # Priority 50 - iframe fallback
]


def run_slot_query(
    domain: str,
    targets: List[str],
    section_hint: Optional[str] = None,
    iso3_codes: Optional[List[str]] = None
) -> Dict:
    """
    Run query through dispatcher using slots (no text query needed)
    
    This is the new slot-driven interface that replaces text-based matching.
    Data sources are selected based on domain and targets, not query keywords.
    
    Args:
        domain: Domain type ("country_profile", "commitment", "legislation")
        targets: List of target keys (country names or region keys)
        section_hint: Optional section hint (e.g., "stressors/fires")
        iso3_codes: Optional list of ISO3 country codes
        
    Returns:
        Dict with targets and hits
    """
    print(f"🎯 Slot-driven query: domain={domain}, targets={targets}, section_hint={section_hint}")
    
    all_hits: List[Dict] = []
    
    # Route based on domain
    for source in sorted(SOURCES, key=lambda s: s.priority):
        source_name = source.__class__.__name__
        
        # Determine if source should handle this domain
        should_fetch = False
        
        if source_name == "TabularCombinedSource":
            # Tables for commitment and legislation domains
            should_fetch = domain in ("commitment", "legislation")
        elif source_name == "ProfilesIframeSource":
            # Iframes for country_profile domain
            should_fetch = domain == "country_profile"
        
        if should_fetch:
            print(f"✓ Source matched: {source_name} (priority: {source.priority})")
            try:
                # Build a pseudo-query for backward compatibility with existing fetch() methods
                # This will be refactored later to pass slots directly
                pseudo_query = f"{domain} {' '.join(targets)}"
                if section_hint:
                    pseudo_query += f" {section_hint}"
                
                hits = source.fetch(pseudo_query, targets)
                print(f"  → Fetched {len(hits)} results")
                all_hits.extend(hits)
            except Exception as e:
                print(f"  ⚠️  Error fetching from {source_name}: {e}")
        else:
            print(f"✗ Source not matched: {source_name} (domain={domain})")
    
    return {
        "targets": targets,
        "hits": all_hits,
        "domain": domain,
        "section_hint": section_hint
    }


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
