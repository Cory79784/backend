"""
Base class for data sources (plugin architecture)
No intent recognition - sources declare if they match a query
"""
from typing import List, Dict


class Source:
    """
    Base class for pluggable data sources
    Each source decides if it matches a query and how to fetch results
    """
    priority: int = 100  # Lower number = higher priority
    
    def matches(self, query: str) -> bool:
        """
        Check if this source should handle the query
        
        Args:
            query: User query string
            
        Returns:
            True if this source can handle the query
        """
        raise NotImplementedError
    
    def fetch(self, query: str, targets: List[str]) -> List[Dict]:
        """
        Fetch results for the given query and targets
        
        Args:
            query: User query string
            targets: List of target keys (countries or region self-keys)
            
        Returns:
            List of result dictionaries
        """
        raise NotImplementedError
