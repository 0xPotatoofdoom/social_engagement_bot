"""
Dynamic Keyword Rotation System for Chronically Online Behavior

Manages keyword pools, tracks trending narratives, and rotates search terms
to create organic, narrative-following search patterns.
"""

import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Set, Tuple
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)


class KeywordRotator:
    """Manages dynamic keyword rotation for organic search behavior"""
    
    def __init__(self):
        self.data_dir = Path("data/keywords")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Core keyword pools by category
        self.keyword_pools = {
            "core_tech": [
                "v4 hooks", "uniswap v4", "unichain", "ai agents", 
                "autonomous trading", "mev protection", "concentrated liquidity",
                "hook architecture", "protocol design", "smart contracts"
            ],
            "defi_general": [
                "defi", "yield farming", "liquidity mining", "impermanent loss",
                "amm", "dex", "liquidity pools", "staking rewards", "tvl",
                "protocol revenue", "real yield", "ve tokenomics"
            ],
            "trending_tech": [
                "restaking", "eigenlayer", "liquid staking", "modular blockchain",
                "rollups", "zk proofs", "account abstraction", "intents",
                "cross-chain", "interoperability", "bridging", "omnichain"
            ],
            "market_vibes": [
                "bull market", "bear market", "crypto winter", "altseason",
                "rotation", "narrative shift", "risk on", "capitulation",
                "accumulation", "distribution", "market structure"
            ],
            "memecoins": [
                "memecoins", "community tokens", "fair launch", "stealth launch",
                "rug pull", "honeypot", "sniping", "degen plays", "10x gems",
                "moonshot", "pump and dump", "whale watching"
            ],
            "stablecoins": [
                "stablecoins", "usdc", "usdt", "dai", "frax", "lusd",
                "algorithmic stable", "collateralized", "peg stability",
                "stable pools", "curve wars", "bribes"
            ],
            "ai_crypto": [
                "ai crypto", "machine learning trading", "predictive models",
                "sentiment analysis", "on-chain ai", "autonomous agents",
                "ai protocols", "decentralized ai", "ml strategies"
            ],
            "culture": [
                "gm", "wagmi", "ngmi", "probably nothing", "few understand",
                "wen token", "wen moon", "diamond hands", "paper hands",
                "hodl", "dca", "btfd", "fomo", "fud"
            ]
        }
        
        # Current narratives (these would be updated based on trends)
        self.current_narratives = {
            "primary": ["ai agents", "v4 hooks", "autonomous trading"],
            "secondary": ["restaking", "modular blockchain", "real yield"],
            "emerging": ["intents", "account abstraction", "omnichain"]
        }
        
        # Search history to avoid repetition
        self.recent_searches = []
        self.search_history_file = self.data_dir / "search_history.json"
        self._load_search_history()
        
        # Trending topics cache
        self.trending_cache_file = self.data_dir / "trending_cache.json"
        self.trending_topics = self._load_trending_cache()
        
    def get_search_keywords(self, count: int = 5, strategy: str = "mixed") -> List[str]:
        """Get a set of keywords for searching based on strategy
        
        Args:
            count: Number of keywords to return
            strategy: "focused" (core only), "broad" (all categories), "narrative" (trending), "mixed"
            
        Returns:
            List of keyword combinations that feel organic
        """
        keywords = []
        
        if strategy == "focused":
            # Focus on core AI x blockchain topics
            keywords = self._get_focused_keywords(count)
        elif strategy == "broad":
            # Mix from all categories for variety
            keywords = self._get_broad_keywords(count)
        elif strategy == "narrative":
            # Follow current narratives
            keywords = self._get_narrative_keywords(count)
        else:  # mixed
            # Organic mix - most realistic
            keywords = self._get_mixed_keywords(count)
            
        # Filter out recent searches to avoid repetition
        keywords = self._filter_recent_searches(keywords)
        
        # Add to search history
        self._update_search_history(keywords)
        
        logger.info(f"Generated {len(keywords)} keywords with {strategy} strategy", keywords=keywords)
        return keywords
        
    def _get_focused_keywords(self, count: int) -> List[str]:
        """Get keywords focused on core AI x blockchain topics"""
        core_terms = self.keyword_pools["core_tech"] + self.keyword_pools["ai_crypto"]
        
        # Create combinations that feel natural
        keywords = []
        for _ in range(count):
            if random.random() < 0.7:
                # Single focused term
                keywords.append(random.choice(core_terms))
            else:
                # Natural combination
                term1 = random.choice(self.keyword_pools["core_tech"])
                term2 = random.choice(["defi", "yield", "protocol", "design"])
                keywords.append(f"{term1} {term2}")
                
        return keywords
        
    def _get_broad_keywords(self, count: int) -> List[str]:
        """Get keywords from all categories"""
        all_keywords = []
        for pool in self.keyword_pools.values():
            all_keywords.extend(pool)
            
        # Mix single terms and combinations
        keywords = []
        for _ in range(count):
            if random.random() < 0.6:
                keywords.append(random.choice(all_keywords))
            else:
                # Create interesting combinations
                cat1 = random.choice(list(self.keyword_pools.keys()))
                cat2 = random.choice(list(self.keyword_pools.keys()))
                if cat1 != cat2:
                    term1 = random.choice(self.keyword_pools[cat1])
                    term2 = random.choice(self.keyword_pools[cat2])
                    keywords.append(f"{term1} {term2}")
                else:
                    keywords.append(random.choice(self.keyword_pools[cat1]))
                    
        return keywords
        
    def _get_narrative_keywords(self, count: int) -> List[str]:
        """Get keywords based on current narratives"""
        keywords = []
        
        # Weight by narrative importance
        narrative_weights = {
            "primary": 0.5,
            "secondary": 0.3,
            "emerging": 0.2
        }
        
        for _ in range(count):
            narrative_type = random.choices(
                list(narrative_weights.keys()),
                weights=list(narrative_weights.values())
            )[0]
            
            base_term = random.choice(self.current_narratives[narrative_type])
            
            # Sometimes combine with context
            if random.random() < 0.4:
                context = random.choice(["analysis", "opportunity", "alpha", "trend", "narrative"])
                keywords.append(f"{base_term} {context}")
            else:
                keywords.append(base_term)
                
        return keywords
        
    def _get_mixed_keywords(self, count: int) -> List[str]:
        """Get organic mix of keywords - most realistic behavior"""
        keywords = []
        
        # Simulate chronically online behavior patterns
        patterns = [
            ("narrative_check", 0.3),    # Checking current narratives
            ("memecoin_degen", 0.15),    # Quick memecoin checks
            ("technical_deep", 0.25),    # Deep technical searches
            ("yield_hunting", 0.15),     # Looking for yield opportunities
            ("general_scroll", 0.15)     # General crypto scrolling
        ]
        
        for _ in range(count):
            pattern = random.choices(
                [p[0] for p in patterns],
                weights=[p[1] for p in patterns]
            )[0]
            
            if pattern == "narrative_check":
                # Check trending narratives
                narrative = random.choice(self.current_narratives["primary"] + self.current_narratives["secondary"])
                if random.random() < 0.3:
                    narrative += " " + random.choice(["thread", "analysis", "alpha"])
                keywords.append(narrative)
                
            elif pattern == "memecoin_degen":
                # Quick memecoin searches
                term = random.choice(self.keyword_pools["memecoins"])
                if random.random() < 0.4:
                    term += " " + random.choice(["gains", "plays", "calls", "gems"])
                keywords.append(term)
                
            elif pattern == "technical_deep":
                # Technical searches
                term = random.choice(self.keyword_pools["core_tech"] + self.keyword_pools["trending_tech"])
                keywords.append(term)
                
            elif pattern == "yield_hunting":
                # Yield/DeFi searches
                term = random.choice(self.keyword_pools["defi_general"] + self.keyword_pools["stablecoins"])
                if random.random() < 0.3:
                    term += " " + random.choice(["apy", "yield", "strategy", "farm"])
                keywords.append(term)
                
            else:  # general_scroll
                # Random interesting combination
                all_terms = []
                for pool in self.keyword_pools.values():
                    all_terms.extend(pool)
                keywords.append(random.choice(all_terms))
                
        return keywords
        
    def _filter_recent_searches(self, keywords: List[str]) -> List[str]:
        """Filter out recently used keywords to avoid repetition"""
        # Keep last 50 searches
        recent_set = set(self.recent_searches[-50:])
        
        filtered = []
        for keyword in keywords:
            if keyword not in recent_set:
                filtered.append(keyword)
            else:
                # Try to find alternative
                for _ in range(3):
                    alternative = self._get_mixed_keywords(1)[0]
                    if alternative not in recent_set:
                        filtered.append(alternative)
                        break
                        
        return filtered
        
    def _update_search_history(self, keywords: List[str]):
        """Update search history"""
        self.recent_searches.extend(keywords)
        self.recent_searches = self.recent_searches[-100:]  # Keep last 100
        
        # Save to file
        try:
            with open(self.search_history_file, 'w') as f:
                json.dump({
                    "searches": self.recent_searches,
                    "last_updated": datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save search history: {e}")
            
    def _load_search_history(self):
        """Load search history from file"""
        try:
            if self.search_history_file.exists():
                with open(self.search_history_file, 'r') as f:
                    data = json.load(f)
                    self.recent_searches = data.get("searches", [])
        except Exception as e:
            logger.error(f"Failed to load search history: {e}")
            self.recent_searches = []
            
    def update_trending_narratives(self, trending_data: Dict[str, List[str]]):
        """Update current narratives based on trending data"""
        if "primary" in trending_data:
            self.current_narratives["primary"] = trending_data["primary"]
        if "secondary" in trending_data:
            self.current_narratives["secondary"] = trending_data["secondary"]
        if "emerging" in trending_data:
            self.current_narratives["emerging"] = trending_data["emerging"]
            
        # Save to cache
        self._save_trending_cache()
        
    def _save_trending_cache(self):
        """Save trending topics to cache"""
        try:
            with open(self.trending_cache_file, 'w') as f:
                json.dump({
                    "narratives": self.current_narratives,
                    "last_updated": datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save trending cache: {e}")
            
    def _load_trending_cache(self) -> Dict:
        """Load trending topics from cache"""
        try:
            if self.trending_cache_file.exists():
                with open(self.trending_cache_file, 'r') as f:
                    data = json.load(f)
                    # Check if cache is recent (within 6 hours)
                    last_updated = datetime.fromisoformat(data["last_updated"])
                    if datetime.now() - last_updated < timedelta(hours=6):
                        return data.get("narratives", self.current_narratives)
        except Exception as e:
            logger.error(f"Failed to load trending cache: {e}")
            
        return self.current_narratives
        
    def get_current_vibe(self) -> str:
        """Get current market vibe for content generation"""
        vibes = [
            "bullish on innovation",
            "hunting for alpha", 
            "deep in the research",
            "following the smart money",
            "tracking on-chain flows",
            "vibing with the community",
            "exploring new narratives",
            "building through the bear",
            "accumulating knowledge"
        ]
        return random.choice(vibes)


# Global instance
_keyword_rotator = None

def get_keyword_rotator() -> KeywordRotator:
    """Get or create global keyword rotator instance"""
    global _keyword_rotator
    if _keyword_rotator is None:
        _keyword_rotator = KeywordRotator()
    return _keyword_rotator