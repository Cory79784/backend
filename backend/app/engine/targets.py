"""
Target extraction (countries/regions) - No intent recognition
Pure rule-based extraction with alias support
"""
import re
from typing import List

# Country aliases (can be moved to YAML config later)
COUNTRY_ALIASES = {
    # MENA & 邻近
    "saudi arabia": {"saudi", "ksa", "kingdom of saudi arabia", "沙特", "saudi arabia"},
    "united arab emirates": {"uae", "emirates", "阿联酋"},
    "qatar": {"qat", "卡塔尔"},
    "kuwait": {"kwt", "科威特"},
    "bahrain": {"bhr", "巴林"},
    "oman": {"omn", "阿曼"},
    "yemen": {"yem", "也门"},
    "jordan": {"jor", "约旦"},
    "lebanon": {"lbn", "黎巴嫩"},
    "israel": {"isr", "以色列"},
    "iran": {"irn", "伊朗"},
    "iraq": {"irq", "伊拉克"},
    "turkey": {"turkiye", "türkiye", "土耳其"},
    "egypt": {"egy", "埃及"},
    "morocco": {"mar", "摩洛哥"},
    "algeria": {"dza", "阿尔及利亚"},
    "tunisia": {"tun", "突尼斯"},

    # SSA 选集
    "ghana": {"gha", "加纳", "ghana"},
    "nigeria": {"nga", "尼日利亚", "nigeria"},
    "ethiopia": {"eth", "埃塞俄比亚", "ethiopia"},
    "kenya": {"ken", "肯尼亚", "kenya"},
    "south africa": {"zaf", "南非", "south africa"},
    "tanzania": {"tza", "坦桑尼亚"},
    "uganda": {"uga", "乌干达"},
    "rwanda": {"rwa", "卢旺达"},
    "burundi": {"bdi", "布隆迪"},
    "democratic republic of the congo": {"drc", "congo-kinshasa", "cod", "刚果（金）"},
    "republic of the congo": {"congo-brazzaville", "cog", "刚果（布）"},
    "angola": {"ago", "安哥拉"},
    "zambia": {"zmb", "赞比亚"},
    "zimbabwe": {"zwe", "津巴布韦"},
    "mozambique": {"moz", "莫桑比克"},
    "namibia": {"nam", "纳米比亚"},
    "botswana": {"bwa", "博茨瓦纳"},
    "cameroon": {"cmr", "喀麦隆"},
    "senegal": {"sen", "塞内加尔"},
    "cote d'ivoire": {"côte d'ivoire", "ivory coast", "civ", "科特迪瓦"},

    # Asia
    "china": {"prc", "cn", "中国", "china"},
    "india": {"ind", "印度", "india"},
    "japan": {"jpn", "日本"},
    "south korea": {"republic of korea", "rok", "kr", "韩国"},
    "indonesia": {"idn", "印尼"},
    "pakistan": {"pak", "巴基斯坦"},
    "bangladesh": {"bgd", "孟加拉国"},
    "vietnam": {"vnm", "越南"},
    "philippines": {"phl", "菲律宾"},
    "thailand": {"tha", "泰国"},

    # Europe
    "united kingdom": {"uk", "great britain", "gb", "gbr", "英国"},
    "france": {"fra", "法国"},
    "germany": {"deu", "德国"},
    "italy": {"ita", "意大利"},
    "spain": {"esp", "西班牙"},
    "poland": {"pol", "波兰"},

    # Americas & Oceania
    "united states": {"usa", "us", "u.s.", "america", "美國", "美国"},
    "canada": {"can", "加拿大"},
    "mexico": {"mex", "墨西哥"},
    "brazil": {"bra", "巴西", "brazil"},
    "argentina": {"arg", "阿根廷"},
    "chile": {"chl", "智利"},
    "peru": {"per", "秘鲁"},
    "colombia": {"col", "哥伦比亚"},
    "australia": {"aus", "澳大利亚"},
    "new zealand": {"nzl", "新西兰"},
}

# Region aliases
REGION_ALIASES = {
    "mena": {"mena", "middle east and north africa", "middle east"},
    "ssa": {"ssa", "sub-saharan africa", "sub saharan africa"},
    "asia": {"asia", "asian"},
    "europe": {"europe", "eu", "european"},
    "africa": {"africa", "african"},
    "americas": {"americas", "latin america", "north america", "south america"},
    "oceania": {"oceania", "pacific"},
}

# ISO3 mapping (can be moved to YAML config later)
ISO3 = {
    # MENA & 邻近
    "saudi arabia": "SAU",
    "united arab emirates": "ARE",
    "qatar": "QAT",
    "kuwait": "KWT",
    "bahrain": "BHR",
    "oman": "OMN",
    "yemen": "YEM",
    "jordan": "JOR",
    "lebanon": "LBN",
    "israel": "ISR",
    "iran": "IRN",
    "iraq": "IRQ",
    "turkey": "TUR",
    "egypt": "EGY",
    "morocco": "MAR",
    "algeria": "DZA",
    "tunisia": "TUN",

    # SSA 选集
    "ghana": "GHA",
    "nigeria": "NGA",
    "ethiopia": "ETH",
    "kenya": "KEN",
    "south africa": "ZAF",
    "tanzania": "TZA",
    "uganda": "UGA",
    "rwanda": "RWA",
    "burundi": "BDI",
    "democratic republic of the congo": "COD",
    "republic of the congo": "COG",
    "angola": "AGO",
    "zambia": "ZMB",
    "zimbabwe": "ZWE",
    "mozambique": "MOZ",
    "namibia": "NAM",
    "botswana": "BWA",
    "cameroon": "CMR",
    "senegal": "SEN",
    "cote d'ivoire": "CIV",

    # Asia
    "china": "CHN",
    "india": "IND",
    "japan": "JPN",
    "south korea": "KOR",
    "indonesia": "IDN",
    "pakistan": "PAK",
    "bangladesh": "BGD",
    "vietnam": "VNM",
    "philippines": "PHL",
    "thailand": "THA",

    # Europe
    "united kingdom": "GBR",
    "france": "FRA",
    "germany": "DEU",
    "italy": "ITA",
    "spain": "ESP",
    "poland": "POL",

    # Americas & Oceania
    "united states": "USA",
    "canada": "CAN",
    "mexico": "MEX",
    "brazil": "BRA",
    "argentina": "ARG",
    "chile": "CHL",
    "peru": "PER",
    "colombia": "COL",
    "australia": "AUS",
    "new zealand": "NZL",
}


def _norm(s: str) -> str:
    """Normalize text for matching"""
    return re.sub(r"\s+", " ", s.strip().lower())


def _region_key(name: str) -> str:
    """Generate region self-key like 'asia-asia'"""
    return f"{name}-{name}"


def extract_targets(query: str) -> List[str]:
    """
    Extract target countries or regions from query
    Priority: countries > regions > world-world (fallback)
    
    Args:
        query: User query string
        
    Returns:
        List of target keys (country names or region self-keys)
    """
    q = _norm(query)
    
    # Check countries first
    found_countries = []
    for country, aliases in COUNTRY_ALIASES.items():
        if country in q or any(a in q for a in aliases):
            found_countries.append(country)
    
    if found_countries:
        return found_countries
    
    # Check regions
    found_regions = []
    for region, aliases in REGION_ALIASES.items():
        if region in q or any(a in q for a in aliases):
            found_regions.append(_region_key(region))
    
    if found_regions:
        return found_regions
    
    # Fallback: world-world
    return ["world-world"]


def to_iso3(country_name: str) -> str | None:
    """
    Convert country name to ISO3 code
    
    Args:
        country_name: Normalized country name
        
    Returns:
        ISO3 code or None if not found
    """
    return ISO3.get(country_name)


# --- Test function ---
def _test_targets():
    """Test target extraction"""
    test_cases = [
        ("Saudi Arabia wildfires", ["saudi arabia"]),
        ("China drought", ["china"]),
        ("KSA trends", ["saudi arabia"]),
        ("沙特法规", ["saudi arabia"]),
        ("MENA restoration", ["mena-mena"]),
        ("Asia commitments", ["asia-asia"]),
        ("global climate", ["world-world"]),
        ("climate trends", ["world-world"]),
    ]
    
    print("=" * 80)
    print("Testing Target Extraction (No Intent)")
    print("=" * 80)
    
    for query, expected in test_cases:
        result = extract_targets(query)
        status = "✅" if result == expected else "❌"
        print(f"\n{status} Query: '{query}'")
        print(f"   Result: {result}")
        print(f"   Expected: {expected}")
        
        # Test ISO3 conversion for countries
        if result and "-" not in result[0] and result[0] != "world-world":
            iso3 = to_iso3(result[0])
            print(f"   ISO3: {iso3}")


if __name__ == "__main__":
    _test_targets()
