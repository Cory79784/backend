"""
Path configuration for data files
Supports environment variables and fallback paths
"""
import os
from typing import List

# Default relative paths (repository)
DEFAULT_COMBINED = "backend/data/combined_tables.jsonl"
DEFAULT_HITS = "backend/data/combined_tables_hits.jsonl"

# Windows absolute paths (local development)
WIN_COMBINED = r"D:\10.09\GeoGLI-Chatbot\backend\data\combined_tables.jsonl"
WIN_HITS = r"D:\10.09\GeoGLI-Chatbot\backend\data\combined_tables_hits.jsonl"


def pick_first_existing(paths: List[str]) -> str | None:
    """
    Pick the first existing path from a list
    
    Args:
        paths: List of paths to check
        
    Returns:
        First existing path or None
    """
    for p in paths:
        if p and os.path.exists(p):
            return p
    return None


def get_combined_path() -> str | None:
    """
    Get path to combined tables file
    Priority: env var > default relative > Windows absolute
    
    Returns:
        Path to combined_tables.jsonl or None
    """
    env_path = os.getenv("GEOGLI_COMBINED_PATH")
    return pick_first_existing([env_path, DEFAULT_COMBINED, WIN_COMBINED])


def get_hits_path() -> str | None:
    """
    Get path to combined hits file (pre-formatted)
    Priority: env var > default relative > Windows absolute
    
    Returns:
        Path to combined_tables_hits.jsonl or None
    """
    env_path = os.getenv("GEOGLI_COMBINED_HITS_PATH")
    return pick_first_existing([env_path, DEFAULT_HITS, WIN_HITS])
