"""
Query processing pipeline - decoupled business logic
Handles rule-based routing and BM25 retrieval aggregation
"""
from dataclasses import dataclass
from typing import List, Dict, Any

from app.search.router_intent import route_query  # Rule-based router (no ML)
from app.search.handlers import (
    search_country_profile,
    search_commitment,
    search_legislation,
)

FALLBACK_TARGET = "world-world"  # Fallback when no country/region detected


@dataclass
class QueryResult:
    """Query processing result"""
    domain: str              # "country_profile" | "commitment" | "legislation"
    targets: List[str]       # Target countries or region self-keys, e.g. ["saudi arabia"] or ["asia-asia"]
    hits: List[Dict[str, Any]]  # BM25 search results


def process_query(user_query: str) -> QueryResult:
    """
    Rule-based query processing pipeline (no ML):
      Layer 1: Extract countries/regions (hard constraint; supports aliases)
      Layer 2: Identify domain by keywords: commitment / legislation / country_profile
      section_hint is only used for country_profile retrieval hint (optional)
    
    Args:
        user_query: User's query string
        
    Returns:
        QueryResult with domain, targets, and aggregated hits
    """
    # Route query using rule-based router
    decision = route_query(user_query)
    
    # Use fallback target if no targets found
    targets = decision.targets or [FALLBACK_TARGET]
    
    # Aggregate hits from all targets
    all_hits: List[Dict[str, Any]] = []
    
    for target in targets:
        # Route to appropriate handler based on domain
        if decision.domain == "commitment":
            hits = search_commitment(target=target)
        elif decision.domain == "legislation":
            hits = search_legislation(target=target)
        else:  # country_profile (default)
            hits = search_country_profile(target=target, section_hint=decision.section_hint)
        
        # Attach routing target to each hit for frontend display/grouping
        for h in hits:
            h.setdefault("country", target)
        
        all_hits.extend(hits)
    
    return QueryResult(
        domain=decision.domain,
        targets=targets,
        hits=all_hits
    )


def process_query_with_grouping(user_query: str) -> Dict[str, Any]:
    """
    Process query and return results with optional country grouping
    
    Args:
        user_query: User's query string
        
    Returns:
        Dict with domain, targets, hits, and by_country grouping
    """
    result = process_query(user_query)
    
    # Group hits by country for frontend convenience
    from collections import defaultdict
    hits_by_country = defaultdict(list)
    for h in result.hits:
        country_key = h.get("country", "unknown")
        hits_by_country[country_key].append(h)
    
    return {
        "domain": result.domain,
        "targets": result.targets,
        "hits": result.hits,
        "by_country": dict(hits_by_country),  # Convert defaultdict to dict
    }


# --- Test function ---
def _test_pipeline():
    """Test pipeline with sample queries"""
    test_queries = [
        "Saudi Arabia wildfires",
        "China drought trends",
        "MENA restoration commitments",
        "Saudi logging law 2020",
        "global climate trends",
    ]
    
    print("=" * 80)
    print("Testing Query Processing Pipeline")
    print("=" * 80)
    
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        
        try:
            result = process_query(query)
            print(f"   Domain: {result.domain}")
            print(f"   Targets: {result.targets}")
            print(f"   Hits: {len(result.hits)} results")
            
            if result.hits:
                for i, hit in enumerate(result.hits[:3], 1):  # Show first 3
                    title = hit.get("title", "N/A")
                    score = hit.get("_score", 0)
                    print(f"     {i}. {title} (score: {score:.3f})")
        except Exception as e:
            print(f"   ❌ Error: {e}")


if __name__ == "__main__":
    _test_pipeline()
