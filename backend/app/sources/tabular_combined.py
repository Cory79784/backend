"""
Tabular combined source (commitment + legislation)
Reads from combined JSONL file with domain field
Supports both hits (pre-formatted) and combined (raw) formats
"""
import json
import os
from typing import List, Dict, Set
from .base import Source
from app.config.paths import get_combined_path, get_hits_path
from app.engine.targets import to_iso3  # Map country names to ISO3

# Keywords that trigger this source
KW_COMMIT_OR_LEGIS = ("commit", "legislat", "pledge", "ndc", "target", "law", "regulation", "act", "decree")


class TabularCombinedSource(Source):
    """
    Source for tabular data (commitments + legislation combined)
    Returns table format for frontend rendering
    Priority: hits file (pre-formatted) > combined file (raw)
    """
    priority = 10  # Higher priority than iframe
    
    def matches(self, query: str) -> bool:
        """
        Match if query contains commitment or legislation keywords
        
        Args:
            query: User query string
            
        Returns:
            True if query contains relevant keywords
        """
        q = query.lower()
        return any(k in q for k in KW_COMMIT_OR_LEGIS)
    
    def _accept_keys(self, targets: List[str]) -> Set[str]:
        """
        Build set of acceptable keys for matching
        Expands country names to include both normalized name and ISO3 code
        
        Args:
            targets: List of target keys (e.g., ["china", "mena-mena"])
            
        Returns:
            Set of acceptable keys in lowercase (e.g., {"china", "chn"})
        """
        accept: Set[str] = set()
        for t in targets:
            t_norm = (t or "").strip().lower()
            if not t_norm:
                continue
            
            # Add normalized target
            accept.add(t_norm)
            
            # For countries (not regions or world-world), also add ISO3 code
            if "-" not in t_norm and t_norm != "world-world":
                iso = to_iso3(t_norm)
                if iso:
                    accept.add(iso.strip().lower())  # e.g., "CHN" -> "chn"
        
        return accept
    
    def _iter_jsonl(self, path: str):
        """
        Iterator for JSONL file
        
        Args:
            path: Path to JSONL file
            
        Yields:
            Parsed JSON objects
        """
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
    
    def fetch(self, query: str, targets: List[str]) -> List[Dict]:
        """
        Fetch tabular data for targets
        
        Args:
            query: User query string
            targets: List of target keys
            
        Returns:
            List of table results
        """
        hits: List[Dict] = []
        q = query.lower()
        
        # Build set of acceptable keys (includes both country names and ISO3 codes)
        accept = self._accept_keys(targets)
        print(f"📊 [Tabular] Accept keys = {accept}")
        
        # Priority 1: Use hits file (pre-formatted, ready to render)
        hits_path = get_hits_path()
        if hits_path and os.path.exists(hits_path):
            print(f"📊 Reading hits file: {hits_path}")
            try:
                for doc in self._iter_jsonl(hits_path):
                    # Pre-formatted hit structure: {"type":"table","domain":...,"country":...,"table":{...}}
                    target_key = (doc.get("country") or doc.get("target_key") or "").strip().lower()
                    if not target_key or target_key not in accept:
                        continue
                    
                    # Further filter by keywords: commit / legislat
                    domain = (doc.get("domain") or "").strip().lower()
                    if "commit" in q and domain != "commitment":
                        continue
                    if "legislat" in q and domain != "legislation":
                        continue
                    
                    # Pre-formatted record, use directly
                    if doc.get("type") == "table" and "table" in doc:
                        hits.append(doc)
                
                if hits:
                    print(f"✓ Found {len(hits)} hits from hits file")
                    return hits  # Return immediately if hits found
            except Exception as e:
                print(f"⚠️  Error reading hits file: {e}")
        
        # Priority 2: Use combined file (raw records, need to transform to table format)
        combined_path = get_combined_path()
        if not combined_path or not os.path.exists(combined_path):
            print("⚠️  Tabular data file not found (combined/hits).")
            return hits
        
        print(f"📊 Reading combined file: {combined_path}")
        try:
            for rec in self._iter_jsonl(combined_path):
                target_key = (rec.get("target_key") or "").strip().lower()
                if not target_key or target_key not in accept:
                    continue
                
                # Filter by keywords
                domain = (rec.get("domain") or "").strip().lower()
                if "commit" in q and domain != "commitment":
                    continue
                if "legislat" in q and domain != "legislation":
                    continue
                
                # Transform to table format
                hits.append({
                    "type": "table",
                    "title": rec.get("title") or (domain.title() if domain else "Data"),
                    "table": {
                        "columns": rec.get("columns", []),
                        "rows": rec.get("rows", []),
                    },
                    "source_url": rec.get("source_url"),
                    "domain": domain,
                    "country": rec.get("target_key"),  # Keep original key (e.g., "SAU" / "asia-asia")
                    "updated": rec.get("updated"),
                })
            
            print(f"✓ Found {len(hits)} hits from combined file")
        except Exception as e:
            print(f"⚠️  Error reading combined file: {e}")
        
        return hits
