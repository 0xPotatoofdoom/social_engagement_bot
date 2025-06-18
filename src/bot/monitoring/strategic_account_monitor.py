"""
Strategic Account Monitoring System

Monitors high-value KOL accounts for AI x blockchain opportunities.
Implements tier-based prioritization and intelligent deduplication.
"""
import json
import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import structlog

logger = structlog.get_logger(__name__)


class StrategicAccountMonitor:
    """Monitor strategic KOL accounts for high-value engagement opportunities"""
    
    def __init__(self, accounts_config: Optional[Dict[str, List[str]]] = None):
        """Initialize with strategic accounts configuration
        
        Args:
            accounts_config: Optional dict with tier_1 and tier_2 account lists
        """
        self.accounts = accounts_config or self._load_default_accounts()
        self.processed_tweets_file = "data/strategic_accounts/processed_tweets.json"
        self.processed_tweets = self._load_processed_tweets()
        
    def _load_default_accounts(self) -> Dict[str, List[str]]:
        """Load default strategic accounts from CLAUDE.md configuration"""
        return {
            "tier_1": [
                "VitalikButerin",
                "dabit3", 
                "PatrickAlphaC",
                "saucepoint",
                "TheCryptoLark"
            ],
            "tier_2": [
                "VirtualBacon0x",
                "Morecryptoonl",
                "AzFlin"
            ]
        }
        
    def _load_processed_tweets(self) -> set:
        """Load set of already processed tweet IDs"""
        if os.path.exists(self.processed_tweets_file):
            try:
                with open(self.processed_tweets_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('processed_ids', []))
            except Exception as e:
                logger.error("Failed to load processed tweets", error=str(e))
        return set()
        
    def _save_processed_tweets(self):
        """Save processed tweet IDs to file"""
        os.makedirs(os.path.dirname(self.processed_tweets_file), exist_ok=True)
        try:
            with open(self.processed_tweets_file, 'w') as f:
                json.dump({'processed_ids': list(self.processed_tweets)}, f)
        except Exception as e:
            logger.error("Failed to save processed tweets", error=str(e))
            
    def get_strategic_accounts(self) -> Dict[str, List[str]]:
        """Get configured strategic accounts"""
        return self.accounts
        
    def check_strategic_accounts(self, x_api, rate_limiter=None) -> List[Dict[str, Any]]:
        """Check all strategic accounts for new opportunities
        
        Args:
            x_api: X API client instance
            rate_limiter: Optional rate limiter instance
            
        Returns:
            List of opportunity dictionaries
        """
        opportunities = []
        all_accounts = self.accounts['tier_1'] + self.accounts['tier_2']
        
        logger.info(f"Checking {len(all_accounts)} strategic accounts")
        
        for account in all_accounts:
            try:
                # Check rate limits if limiter provided
                if rate_limiter and not rate_limiter.can_make_call('user_timeline'):
                    logger.warning(f"Rate limit reached, skipping {account}")
                    continue
                    
                # Record the API call
                if rate_limiter:
                    rate_limiter.record_call('user_timeline')
                    
                # Get recent tweets from timeline
                # Handle both async (production) and sync (test) APIs
                timeline_result = x_api.get_user_timeline(account, max_results=10)
                
                if asyncio.iscoroutine(timeline_result):
                    # Production async API
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        tweets = loop.run_until_complete(timeline_result)
                    finally:
                        loop.close()
                else:
                    # Test mock API
                    tweets = timeline_result
                
                # Process tweets for opportunities
                logger.debug(f"Processing {len(tweets)} tweets for {account}")
                for tweet in tweets:
                    if self._is_relevant_opportunity(tweet):
                        opportunity = self._create_opportunity(tweet, account)
                        if opportunity:
                            opportunities.append(opportunity)
                        else:
                            logger.debug(f"Failed to create opportunity for tweet {tweet.get('id')}")
                    else:
                        logger.debug(f"Tweet not relevant: {tweet.get('id', 'unknown')}")
                            
            except Exception as e:
                logger.error(f"Failed to check account {account}", error=str(e))
                if "rate limit" in str(e).lower():
                    # Handle rate limit
                    if rate_limiter:
                        rate_limiter.handle_rate_limit('user_timeline')
                    # Return what we have so far on rate limit
                    return opportunities
                    
        logger.info(f"Found {len(opportunities)} strategic opportunities")
        return opportunities
        
    def _is_relevant_opportunity(self, tweet: Dict[str, Any]) -> bool:
        """Check if tweet is a relevant opportunity
        
        Criteria:
        - Recent (within 2 hours)
        - Not already processed
        - Contains relevant keywords
        """
        # Check if already processed
        tweet_id = tweet.get('id', '')
        if tweet_id in self.processed_tweets:
            return False
            
        # Check recency
        created_at = tweet.get('created_at', '')
        if created_at:
            try:
                # Handle different datetime formats
                if isinstance(created_at, str):
                    # Remove Z suffix and parse
                    tweet_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                else:
                    # Assume it's already a datetime object
                    tweet_time = created_at
                    
                # Make both times timezone-aware for comparison
                now = datetime.now()
                if tweet_time.tzinfo:
                    from datetime import timezone
                    now = datetime.now(timezone.utc)
                    
                if now - tweet_time > timedelta(hours=2):
                    return False
            except Exception as e:
                logger.warning(f"Failed to parse tweet time: {e}")
                # If we can't parse time, assume it's recent
                
        # Check for relevant keywords
        text = tweet.get('text', '').lower()
        relevant_keywords = [
            'v4', 'uniswap', 'hooks', 'unichain', 'ai agent', 
            'mev', 'liquidity', 'protocol', 'smart contract'
        ]
        
        has_keyword = any(keyword in text for keyword in relevant_keywords)
        logger.debug(f"Tweet {tweet_id}: text='{text[:50]}...', has_keyword={has_keyword}")
        
        if not has_keyword:
            return False
            
        return True
        
    def _create_opportunity(self, tweet: Dict[str, Any], account: str) -> Optional[Dict[str, Any]]:
        """Create opportunity dict from tweet data"""
        try:
            # Mark as processed
            tweet_id = tweet.get('id', '')
            self.processed_tweets.add(tweet_id)
            self._save_processed_tweets()
            
            # Calculate score with tier bonus
            base_score = self.calculate_opportunity_score(tweet)
            
            return {
                'tweet_id': tweet_id,
                'account': account,
                'text': tweet.get('text', ''),
                'created_at': tweet.get('created_at', ''),
                'metrics': {
                    'retweets': tweet.get('retweet_count', 0),
                    'likes': tweet.get('favorite_count', 0),
                    'replies': tweet.get('reply_count', 0)
                },
                'relevance_score': base_score,
                'is_strategic': True,
                'tier': 1 if account in self.accounts['tier_1'] else 2
            }
        except Exception as e:
            logger.error(f"Failed to create opportunity", error=str(e))
            return None
            
    def calculate_opportunity_score(self, tweet: Dict[str, Any]) -> float:
        """Calculate relevance score for opportunity
        
        Tier 1 accounts get 0.15 bonus to ensure they meet high priority threshold
        """
        base_score = 0.7  # Base score for strategic accounts
        
        # Add tier bonus
        username = tweet.get('user', {}).get('screen_name', '')
        if username in self.accounts['tier_1']:
            base_score += 0.15  # Ensures >= 0.85 for tier 1
            
        # Engagement bonus
        engagement = (tweet.get('retweet_count', 0) + 
                     tweet.get('favorite_count', 0)) / 100
        base_score += min(engagement * 0.1, 0.15)  # Max 0.15 bonus
        
        return min(base_score, 1.0)
        
    def mark_opportunities_processed(self, opportunities: List[Dict[str, Any]]):
        """Mark opportunities as processed to prevent duplicates"""
        for opp in opportunities:
            tweet_id = opp.get('tweet_id', '')
            if tweet_id:
                self.processed_tweets.add(tweet_id)
        self._save_processed_tweets()
        
    def get_processed_tweet_ids(self) -> set:
        """Get set of processed tweet IDs"""
        return self.processed_tweets
        
    def fetch_all_strategic_timelines(self, x_api, rate_limiter=None) -> List[Dict[str, Any]]:
        """Fetch timelines for all strategic accounts
        
        This is an alias for check_strategic_accounts for compatibility
        """
        return self.check_strategic_accounts(x_api, rate_limiter)
        
    def enrich_opportunity_with_ai(self, opportunity: Dict[str, Any], claude_client) -> Dict[str, Any]:
        """Enrich opportunity with AI-generated content
        
        Args:
            opportunity: Raw opportunity dict
            claude_client: Claude API client instance
            
        Returns:
            Enriched opportunity with AI content
        """
        try:
            # Generate AI replies
            ai_content = claude_client.generate_replies(
                tweet_text=opportunity['text'],
                author=opportunity['account'],
                context={
                    'is_strategic': True,
                    'tier': opportunity.get('tier', 2)
                }
            )
            
            opportunity['ai_content'] = ai_content
            
            # Ensure tier 1 gets high score
            if opportunity.get('tier') == 1:
                opportunity['relevance_score'] = max(opportunity.get('relevance_score', 0.7), 0.85)
                
            return opportunity
            
        except Exception as e:
            logger.error(f"Failed to enrich with AI", error=str(e))
            return opportunity