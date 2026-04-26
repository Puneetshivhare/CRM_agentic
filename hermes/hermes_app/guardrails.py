"""
hermes_app/guardrails.py — Guardrails enforcement.
"""

import logging
import re
from typing import List, Set

import yaml

logger = logging.getLogger("hermes")


class GuardrailsManager:
    """Enforces guardrails and restrictions."""
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.allowed_actions: Set[str] = set(self.config.get("allowed_actions", []))
        self.blocked_actions: Set[str] = set(self.config.get("blocked_actions", []))
        self.allowed_mcp_servers: Set[str] = set(
            self.config.get("allowed_mcp_servers", [])
        )
        self.blocked_mcp_servers: Set[str] = set(
            self.config.get("blocked_mcp_servers", [])
        )
        self.blocked_query_patterns: List[str] = self.config.get(
            "web_search", {}
        ).get("blocked_query_patterns", [])
        self.blocked_domains: List[str] = self.config.get(
            "web_crawl", {}
        ).get("blocked_domains", [])
        
    def _load_config(self, path: str) -> dict:
        """Load guardrails configuration."""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load guardrails: {e}")
            # Return restrictive defaults
            return {
                "allowed_actions": ["web_search", "web_crawl"],
                "blocked_actions": ["*"],
            }
    
    def is_action_allowed(self, action: str) -> bool:
        """Check if action is permitted."""
        # Explicitly blocked?
        if action in self.blocked_actions:
            logger.warning(f"Action '{action}' is in blocked list")
            return False
        
        # Explicitly allowed?
        if action not in self.allowed_actions:
            logger.warning(f"Action '{action}' not in allowed list")
            return False
        
        return True
    
    def is_mcp_server_allowed(self, server: str) -> bool:
        """Check if MCP server is permitted."""
        if server in self.blocked_mcp_servers:
            return False
        if server not in self.allowed_mcp_servers:
            return False
        return True
    
    def validate_search_query(self, query: str) -> tuple[bool, str]:
        """Validate search query against blocked patterns."""
        query_lower = query.lower()
        
        for pattern in self.blocked_query_patterns:
            # Convert glob-style to regex
            regex_pattern = pattern.replace("*", ".*").lower()
            if re.search(regex_pattern, query_lower):
                return False, f"Query matches blocked pattern: {pattern}"
        
        return True, ""
    
    def is_domain_allowed(self, domain: str) -> bool:
        """Check if domain is allowed for crawling."""
        for blocked in self.blocked_domains:
            pattern = blocked.replace("*", ".*")
            if re.match(pattern, domain, re.IGNORECASE):
                return False
        return True
    
    def get_crawl_limits(self) -> dict:
        """Get crawl restrictions."""
        return self.config.get("web_crawl", {})
    
    def get_rate_limits(self) -> dict:
        """Get rate limit configuration."""
        return self.config.get("rate_limits", {})
