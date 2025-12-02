"""
Rule-based router for GeoGLI queries
Extracts targets (countries/regions) and domain (commitment/legislation/country_profile)
"""

from dataclasses import dataclass
import re


# --- 1) Aliases ---
COUNTRY_ALIASES = {
    # country: set of aliases
    "saudi arabia": {"saudi", "ksa", "kingdom of saudi arabia", "沙特", "saudi arabia"},
    "china": {"prc", "中国", "cn", "china"},
    "ghana": {"gha", "加纳", "ghana"},
    "india": {"ind", "印度", "india"},
    "brazil": {"bra", "巴西", "brazil"},
    "egypt": {"egy", "埃及", "egypt"},
    "nigeria": {"nga", "尼日利亚", "nigeria"},
    "south africa": {"zaf", "南非", "south africa"},
    "kenya": {"ken", "肯尼亚", "kenya"},
    "ethiopia": {"eth", "埃塞俄比亚", "ethiopia"},
    # ... add more as needed
}

REGION_ALIASES = {
    "mena": {"mena", "middle east and north africa", "middle east"},
    "ssa": {"ssa", "sub-saharan africa", "sub saharan africa"},
    "asia": {"asia", "asian"},
    "europe": {"europe", "eu", "european"},
    "africa": {"africa", "african"},
    "americas": {"americas", "latin america", "north america", "south america"},
    "oceania": {"oceania", "pacific"},
    # ...
}


def region_self_key(region_name: str) -> str:
    """Generate region self-key like 'Asia-Asia'"""
    return f"{region_name}-{region_name}"


# --- 2) Domain keywords ---
KW_COMMITMENT = {"commitment", "pledge", "ndc", "target", "sdg commitment", "承诺", "restore", "restoration"}
KW_LEGISLATION = {"legislation", "law", "act", "decree", "条例", "法律", "法规", "regulation", "细则"}


# --- 3) Country profile section keywords ---
SECTION_KWS = {
    "current_state": {
        "land_status": {"land cover", "wetlands", "esa 2021"},
        "socio_prod": {"agricultural production", "production index", "international usd"},
        "socio_wealth": {"total wealth", "renewable natural capital", "nonrenewable", "share of global wealth"},
    },
    "stressors": {
        "fires": {"active fires", "fires density", "fires trends", "wildfire", "fire"},
        "climate_hazards": {"drought", "inform risk", "hazard"},
        "socio_agri": {"livestock", "cereals", "area harvested", "yield", "pesticides", "nutrients", "nitrogen surplus", "budget kg/ha"},
    },
    "trends": {
        "climate": {"temperature anomaly", "precipitation anomaly", "1991-2020", "climate trend"},
        "land": {"land cover trends", "wildfires (1000 ha)", "forest area change", "forest land - share", "land degradation"},
        "socio": {"population", "urban", "rural", "exports of wood", "gdp", "agriculture value"},
    },
    "impacts": {
        "food_health": {"land productivity", "food insecure", "food index per capita", "food supply variability", "undernourishment", "wasting"},
        "land_status": {"ecological footprint", "biocapacity", "consumption trend"},
        "climate_related": {"fatalities", "disasters", "human displacements", "average annual loss"},
    }
}


@dataclass
class RouteDecision:
    """Route decision with targets, domain, and optional section hint"""
    targets: list[str]          # e.g. ["saudi arabia"] or ["asia-asia"]
    domain: str                 # "commitment" | "legislation" | "country_profile"
    section_hint: str | None    # optional, e.g. "stressors/climate_hazards"


def normalize_text(s: str) -> str:
    """Normalize text for matching"""
    return re.sub(r"\s+", " ", s.strip().lower())


def extract_targets(q: str) -> list[str]:
    """
    Extract target countries or regions from query
    Priority: countries > regions
    """
    qn = normalize_text(q)
    hits = []

    # Check countries
    for country, aliases in COUNTRY_ALIASES.items():
        if country in qn or any(a in qn for a in aliases):
            hits.append(country)

    # Check regions
    region_hits = []
    for region, aliases in REGION_ALIASES.items():
        if region in qn or any(a in qn for a in aliases):
            region_hits.append(region_self_key(region))

    # Priority: if country found → use countries; else if region found → use region self-key
    if hits:
        return hits
    if region_hits:
        return region_hits
    
    return []  # none found


def pick_domain(q: str) -> str:
    """
    Pick domain based on keywords
    Priority: commitment > legislation > country_profile (default)
    """
    qn = normalize_text(q)
    
    if any(k in qn for k in KW_COMMITMENT):
        return "commitment"
    if any(k in qn for k in KW_LEGISLATION):
        return "legislation"
    
    return "country_profile"


def pick_section_hint(q: str) -> str | None:
    """
    Pick section hint for country_profile domain
    Returns format: "top_section/sub_section" or None
    """
    qn = normalize_text(q)
    
    for top, subdict in SECTION_KWS.items():
        for sub, kws in subdict.items():
            if any(k in qn for k in kws):
                return f"{top}/{sub}"
    
    return None


def route_query(q: str) -> RouteDecision:
    """
    Main routing function
    
    Args:
        q: User query string
        
    Returns:
        RouteDecision with targets, domain, and optional section_hint
    """
    targets = extract_targets(q)
    domain = pick_domain(q)
    hint = pick_section_hint(q) if domain == "country_profile" else None
    
    return RouteDecision(targets=targets, domain=domain, section_hint=hint)


# --- Backward compatibility wrapper ---
def route(query: str) -> dict:
    """
    Legacy wrapper for backward compatibility
    Maps new RouteDecision to old slot format
    """
    decision = route_query(query)
    
    # Map to old format
    slots = {
        "targets": decision.targets,
        "domain": decision.domain,
        "section_hint": decision.section_hint,
        # Legacy fields (for compatibility)
        "intent": decision.domain,
        "country": decision.targets[0] if decision.targets else "",
        "region": "",
        "indicator": "",
        "period": ""
    }
    
    return slots


# --- Test function ---
def _test_router():
    """Test cases for the new router"""
    test_cases = [
        # Country profile queries
        ("Saudi Arabia wildfires", ["saudi arabia"], "country_profile", "stressors/fires"),
        ("China drought trends", ["china"], "country_profile", "stressors/climate_hazards"),
        ("Ghana land cover", ["ghana"], "country_profile", "current_state/land_status"),
        
        # Commitment queries
        ("Saudi Arabia restoration commitments", ["saudi arabia"], "commitment", None),
        ("MENA restoration pledge", ["mena-mena"], "commitment", None),
        ("Asia NDC targets", ["asia-asia"], "commitment", None),
        
        # Legislation queries
        ("Saudi logging law 2020", ["saudi arabia"], "legislation", None),
        ("China environmental regulations", ["china"], "legislation", None),
        ("沙特法规", ["saudi arabia"], "legislation", None),
        
        # No target queries
        ("global climate trends", [], "country_profile", "trends/climate"),
        ("restoration commitments", [], "commitment", None),
    ]
    
    print("=" * 80)
    print("Testing new rule-based router")
    print("=" * 80)
    
    for query, expected_targets, expected_domain, expected_hint in test_cases:
        result = route_query(query)
        
        status = "✅" if (
            result.targets == expected_targets and 
            result.domain == expected_domain and 
            result.section_hint == expected_hint
        ) else "❌"
        
        print(f"\n{status} Query: '{query}'")
        print(f"   Targets: {result.targets} (expected: {expected_targets})")
        print(f"   Domain: {result.domain} (expected: {expected_domain})")
        print(f"   Section: {result.section_hint} (expected: {expected_hint})")


if __name__ == "__main__":
    _test_router()


