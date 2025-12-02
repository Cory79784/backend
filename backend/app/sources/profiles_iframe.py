"""
Country profiles iframe source
Keyword → dashboard id routing (no intent)
"""
from typing import List, Dict, Tuple
from .base import Source
from app.engine.targets import to_iso3

HOST = "dash-staging.g20gsp.unepgrid.ch"
DEFAULT_DASHBOARD_ID = 38     # fallback: Socio-Econ "Trends"
HEIGHT = 420

# 关键词 → 仪表盘ID（只换 ID，其他 URL 结构不变；匹配任意一个关键词即可）
# 38: Trends - Socio-Economics（人口/GDP/贸易等）
# 37: ODA flows（援助）
# 39: Climate trends（温度/降水）
# 40: Global Restoration Commitments（承诺总览）- 注释掉避免与 commitment 重复
# 41: Dashboard meta（图表/地图数量等）
DASHBOARD_KEYWORD_RULES: List[Tuple[int, Tuple[str, ...]]] = [
    # ODA flows
    (37, ("oda", "official development assistance", "biodiversity sector", "water supply", "sanitation", "oda flows")),
    # Climate trends
    (39, ("climate", "temperature", "precipitation", "rainfall", "anomaly", "temperature change", "precip change")),
    # Global restoration commitments - 注释掉避免与 commitment 关键词冲突
    # (40, ("global restoration commitments", "restoration commitments", "bonn challenge", "rio conventions", "pledge", "commitments")),
    # Dashboard meta
    (41, ("dashboard family", "number of charts", "number of maps", "table all charts", "dashboard meta")),
    # Socio-economics (38) —— 兜底前的弱引导
    (38, ("population", "gdp", "agriculture", "agricultural", "exports", "urban", "rural", "socio-economics", "socioeconomics", "socio")),
]


def _pick_dashboard_id(query: str) -> int:
    """
    Pick dashboard ID based on query keywords
    
    Args:
        query: User query string
        
    Returns:
        Dashboard ID (37, 38, 39, 40, or 41)
    """
    q = query.lower()
    for dash_id, kws in DASHBOARD_KEYWORD_RULES:
        if any(k in q for k in kws):
            return dash_id
    return DEFAULT_DASHBOARD_ID


class ProfilesIframeSource(Source):
    """
    Source for country profile iframes (Superset dashboards)
    Fallback source when no commit/legislation keywords
    """
    priority = 50  # Lower priority than tabular
    
    def matches(self, query: str) -> bool:
        """
        Match as fallback when no commit/legislation keywords
        
        Args:
            query: User query string
            
        Returns:
            True if query doesn't contain commit/legislation keywords
        """
        q = query.lower()
        # Fallback: match when NOT commit/legislation
        return not ("commit" in q or "legislat" in q or "pledge" in q or "law" in q)
    
    def _build_url(self, iso3: str, dashboard_id: int) -> str:
        """
        Build Superset dashboard URL
        Only replaces dashboard/{id} and iso3, keeps other URL structure
        
        Args:
            iso3: ISO3 country code
            dashboard_id: Dashboard ID
            
        Returns:
            Full dashboard URL
        """
        return f"https://{HOST}/superset/dashboard/{dashboard_id}/?standalone=3&iso3={iso3}"
    
    def fetch(self, query: str, targets: List[str]) -> List[Dict]:
        """
        Fetch iframe embeds for targets
        
        Args:
            query: User query string
            targets: List of target keys
            
        Returns:
            List of iframe results
        """
        hits: List[Dict] = []
        dash_id = _pick_dashboard_id(query)
        
        for target in targets:
            # Skip regions (no ISO3 code)
            if "-" in target:
                continue
            
            # Skip world-world fallback
            if target == "world-world":
                continue
            
            # Get ISO3 code
            iso3 = to_iso3(target)
            if not iso3:
                continue
            
            # Build URL with selected dashboard ID
            url = self._build_url(iso3, dash_id)
            
            # Create iframe result
            hits.append({
                "type": "iframe",
                "title": f"Country Profile — {iso3} (#{dash_id})",
                "embed": {
                    "url": url,
                    "height": HEIGHT,
                },
                "country": target,
                "iso3": iso3,
                "dashboard_id": dash_id,
            })
        
        return hits
