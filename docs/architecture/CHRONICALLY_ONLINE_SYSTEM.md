# Chronically Online Keyword System Documentation

## Overview

The Chronically Online System makes the X Engagement Bot feel like a real crypto enthusiast who's constantly scrolling Twitter, jumping between topics based on current narratives and market vibes.

## Architecture

### KeywordRotator Component

Located at: `src/bot/monitoring/keyword_rotator.py`

**Core Features:**
- Dynamic keyword pools organized by category
- Search history tracking to avoid repetition
- Narrative tracking that updates every 4-6 hours
- Market mood incorporation
- Organic search pattern generation

### Keyword Categories

```python
keyword_pools = {
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
```

## Search Strategies

### 1. Mixed Strategy (35% - Most Common)
Simulates organic scrolling behavior with patterns like:
- **Narrative checking** (30%): "v4 hooks analysis"
- **Memecoin degen** (15%): "stealth launch gems"
- **Technical deep dive** (25%): "unichain architecture"
- **Yield hunting** (15%): "real yield strategy"
- **General scroll** (15%): Random combinations

### 2. Focused Strategy (30%)
Concentrates on core AI x blockchain topics:
- Single focused terms (70%): "v4 hooks implementation"
- Natural combinations (30%): "autonomous trading defi"

### 3. Narrative Strategy (25%)
Follows current trending topics:
- Primary narratives (50%): Current hot topics
- Secondary narratives (30%): Emerging trends
- Emerging narratives (20%): Future possibilities

### 4. Broad Strategy (10%)
Explores across all categories for variety

## Implementation Details

### Search Pattern Generation

```python
# Example: Mixed strategy implementation
if pattern == "narrative_check":
    narrative = random.choice(current_narratives["primary"])
    if random.random() < 0.3:
        narrative += " " + random.choice(["thread", "analysis", "alpha"])
    keywords.append(narrative)
    
elif pattern == "memecoin_degen":
    term = random.choice(keyword_pools["memecoins"])
    if random.random() < 0.4:
        term += " " + random.choice(["gains", "plays", "calls", "gems"])
    keywords.append(term)
```

### Narrative Updates

Every 4-6 hours, the system updates trending narratives based on:
- Predefined narrative sets that rotate
- Market mood (bullish/crabbing/accumulating/rotating)
- Dynamic additions based on current sentiment

### Search History Management

- Tracks last 50-100 searches
- Filters out recently used keywords
- Attempts alternative generation if repetition detected
- Persists history to `data/keywords/search_history.json`

## Integration with Monitoring

The keyword rotation system integrates with `CronMonitor`:

```python
# In _monitor_ai_blockchain_keywords()
ai_blockchain_keywords = self._get_focused_keywords()

# Which calls:
keywords = self.keyword_rotator.get_search_keywords(
    count=keyword_count,  # 3-6 keywords
    strategy=strategy     # chosen by weighted random
)
```

## Current Vibes

The system includes "vibes" that influence content generation:
- "bullish on innovation"
- "hunting for alpha"
- "deep in the research"
- "following the smart money"
- "tracking on-chain flows"
- "vibing with the community"
- "exploring new narratives"
- "building through the bear"
- "accumulating knowledge"

## Data Persistence

### Search History
- Location: `data/keywords/search_history.json`
- Contains: Recent searches and timestamp

### Trending Cache
- Location: `data/keywords/trending_cache.json`
- Contains: Current narratives and last update time
- TTL: 6 hours

## Performance Characteristics

- **Keyword Generation**: <10ms per batch
- **History Lookup**: O(1) with set-based deduplication
- **Memory Usage**: ~10KB for history and cache
- **Update Frequency**: 
  - Keywords: Every 30-minute monitoring cycle
  - Narratives: Every 4-6 hours

## Example Output

```
Selected 5 keywords with mixed strategy:
- "rug pull calls"
- "ve tokenomics farm"
- "autonomous trading"
- "defi"
- "degen plays"
```

This creates a natural search pattern that feels like someone who's:
1. Checking for memecoin opportunities
2. Looking into yield farming strategies
3. Researching technical topics
4. Generally browsing DeFi
5. Back to checking degen plays

## Future Enhancements

1. **Real-time Trend Detection**: Analyze actual Twitter trends
2. **Engagement-based Learning**: Adjust keyword weights based on success
3. **Time-of-day Patterns**: Different search behaviors for different times
4. **Event-driven Keywords**: React to major crypto events dynamically
5. **Community Input**: Let followers suggest trending topics