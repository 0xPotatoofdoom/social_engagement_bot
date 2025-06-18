"""
Trend Monitoring System

Ingests trending topics, mentions, and conversations to identify
opportunities for relevant banger posts.
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
import structlog
from collections import defaultdict
import tweepy

# Configure structured logging
logger = structlog.get_logger(__name__)


@dataclass
class TrendingTopic:
    """Represents a trending topic with relevance scoring."""
    topic: str
    volume: int
    trend_type: str  # 'hashtag', 'keyword', 'mention'
    relevance_score: float
    discovered_at: datetime
    last_seen: datetime
    sample_tweets: List[Dict] = field(default_factory=list)
    related_topics: Set[str] = field(default_factory=set)
    engagement_potential: float = 0.0


@dataclass
class ContentOpportunity:
    """Represents an opportunity for content creation."""
    trigger_type: str  # 'mention', 'trend', 'conversation'
    context: Dict
    relevance_score: float
    urgency_score: float  # How time-sensitive is this?
    suggested_approach: str  # 'reply', 'quote', 'original', 'thread'
    discovered_at: datetime
    expires_at: Optional[datetime] = None


class TrendMonitor:
    """
    Monitors trending topics and identifies content opportunities.
    
    This system will generate logs that help us understand:
    1. What topics are trending that we should respond to
    2. Which conversations we should join
    3. When to create original content vs reactive content
    4. Optimal timing for maximum engagement
    5. Sentiment analysis for better opportunity detection
    6. Proactive keyword search for engagement opportunities
    """
    
    def __init__(self, x_client, claude_client=None, target_topics: List[str] = None, search_keywords: List[str] = None):
        self.x_client = x_client
        self.claude_client = claude_client
        self.target_topics = target_topics or []
        self.search_keywords = search_keywords or []
        
        # AI x Blockchain Enhanced Keywords
        self.ai_blockchain_keywords = self._get_ai_blockchain_keywords()
        
        # Tracking data
        self.trending_topics: Dict[str, TrendingTopic] = {}
        self.content_opportunities: List[ContentOpportunity] = []
        self.monitored_keywords = set(self.target_topics + self.search_keywords + self.ai_blockchain_keywords)
        
        # Monitoring state
        self.last_mentions_check = None
        self.last_trends_check = None
        self.last_keyword_search = {}  # Track last search for each keyword
        self.monitoring_active = False
        
        logger.info(
            "trend_monitor_initialized",
            target_topics=len(self.target_topics),
            search_keywords=len(self.search_keywords),
            ai_blockchain_keywords=len(self.ai_blockchain_keywords),
            total_monitored_keywords=len(self.monitored_keywords),
            has_claude_client=bool(claude_client)
        )
    
    async def start_monitoring(self, check_interval: int = 300):  # 5 minutes
        """Start continuous monitoring of trends and mentions."""
        logger.info("trend_monitoring_started", check_interval=check_interval)
        self.monitoring_active = True
        
        while self.monitoring_active:
            try:
                # Monitor mentions for direct engagement opportunities
                await self.check_mentions()
                
                # PROACTIVE: Search for keyword-based opportunities
                await self.search_keyword_opportunities()
                
                # Monitor trending topics for content inspiration
                await self.check_trending_topics()
                
                # Analyze conversations for context
                await self.analyze_conversations()
                
                # Identify content opportunities
                opportunities = await self.identify_content_opportunities()
                
                logger.info(
                    "monitoring_cycle_completed",
                    new_opportunities=len(opportunities),
                    total_trends=len(self.trending_topics),
                    timestamp=datetime.now().isoformat()
                )
                
                # Wait before next cycle
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(
                    "monitoring_cycle_error",
                    error_type=type(e).__name__,
                    error_details=str(e)
                )
                # Continue monitoring even if one cycle fails
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def check_mentions(self) -> List[Dict]:
        """Check for new mentions and conversation opportunities."""
        logger.info("checking_mentions_for_opportunities")
        
        try:
            since_id = None
            if self.last_mentions_check:
                # Get mentions since last check
                since_id = self.last_mentions_check
            
            mentions = await self.x_client.get_mentions(since_id=since_id)
            
            if mentions:
                logger.info(
                    "mentions_retrieved",
                    mention_count=len(mentions),
                    has_since_id=bool(since_id)
                )
                
                # Update last check ID to most recent mention
                if mentions:
                    self.last_mentions_check = mentions[0]['id']
                
                # Analyze mentions for content opportunities
                opportunities = await self.analyze_mentions_for_opportunities(mentions)
                self.content_opportunities.extend(opportunities)
                
                return mentions
            else:
                logger.info("no_new_mentions_found")
                return []
                
        except Exception as e:
            logger.error(
                "mentions_check_failed",
                error_type=type(e).__name__,
                error_details=str(e)
            )
            return []
    
    async def analyze_mentions_for_opportunities(self, mentions: List[Dict]) -> List[ContentOpportunity]:
        """Analyze mentions to identify content opportunities."""
        opportunities = []
        
        for mention in mentions:
            try:
                text = mention.get('text', '')
                author_id = mention.get('author_id')
                mention_id = mention.get('id')
                
                logger.debug(
                    "analyzing_mention",
                    mention_id=mention_id,
                    author_id=author_id,
                    text_preview=text[:100]
                )
                
                # Calculate relevance score based on content and author
                relevance_score = await self.calculate_mention_relevance(mention)
                
                # Calculate urgency (how quickly we should respond)
                urgency_score = await self.calculate_urgency(mention)
                
                # Determine best response approach
                suggested_approach = await self.suggest_response_approach(mention)
                
                if relevance_score > 0.5:  # Only create opportunities for relevant mentions
                    opportunity = ContentOpportunity(
                        trigger_type='mention',
                        context={
                            'mention_id': mention_id,
                            'author_id': author_id,
                            'text': text,
                            'mention_data': mention
                        },
                        relevance_score=relevance_score,
                        urgency_score=urgency_score,
                        suggested_approach=suggested_approach,
                        discovered_at=datetime.now(),
                        expires_at=datetime.now() + timedelta(hours=2)  # Mentions are time-sensitive
                    )
                    
                    opportunities.append(opportunity)
                    
                    logger.info(
                        "content_opportunity_identified",
                        trigger_type='mention',
                        relevance_score=relevance_score,
                        urgency_score=urgency_score,
                        approach=suggested_approach,
                        mention_id=mention_id
                    )
                
            except Exception as e:
                logger.error(
                    "mention_analysis_error",
                    mention_id=mention.get('id', 'unknown'),
                    error_type=type(e).__name__,
                    error_details=str(e)
                )
        
        return opportunities
    
    async def calculate_mention_relevance(self, mention: Dict) -> float:
        """Calculate how relevant a mention is to our target topics."""
        text = mention.get('text', '').lower()
        
        # Check for target topic keywords
        topic_matches = 0
        for topic in self.target_topics:
            if topic.lower() in text:
                topic_matches += 1
        
        # Base relevance from topic matching
        topic_relevance = min(topic_matches / max(len(self.target_topics), 1), 1.0)
        
        # Check for engagement indicators (questions, requests)
        engagement_indicators = ['?', 'how', 'what', 'why', 'help', 'advice', 'thoughts']
        engagement_score = sum(1 for indicator in engagement_indicators if indicator in text)
        engagement_relevance = min(engagement_score / 3, 1.0)  # Max boost from engagement
        
        # Combine scores
        relevance = (topic_relevance * 0.7) + (engagement_relevance * 0.3)
        
        logger.debug(
            "mention_relevance_calculated",
            topic_relevance=topic_relevance,
            engagement_relevance=engagement_relevance,
            final_relevance=relevance,
            topic_matches=topic_matches
        )
        
        return relevance
    
    async def calculate_urgency(self, mention: Dict) -> float:
        """Calculate how urgently we should respond to this mention."""
        # For now, all mentions are moderately urgent
        # TODO: Add factors like:
        # - Author follower count
        # - Mention engagement (likes, retweets)
        # - Time since mention
        # - Question vs statement
        
        text = mention.get('text', '').lower()
        
        # Questions are more urgent
        if '?' in text:
            return 0.8
        
        # Requests for help are urgent
        urgent_keywords = ['help', 'urgent', 'asap', 'quick']
        if any(keyword in text for keyword in urgent_keywords):
            return 0.9
        
        # Regular mentions
        return 0.5
    
    async def suggest_response_approach(self, mention: Dict) -> str:
        """Suggest the best approach for responding to this mention."""
        text = mention.get('text', '').lower()
        
        # If it's a question, suggest a direct reply
        if '?' in text:
            return 'reply'
        
        # If it's sharing our content, consider quote tweet
        if 'rt ' in text or 'retweet' in text:
            return 'quote'
        
        # If it's a discussion, join the thread
        if any(word in text for word in ['discuss', 'thread', 'conversation']):
            return 'thread'
        
        # Default to reply
        return 'reply'
    
    async def search_keyword_opportunities(self) -> List[Dict]:
        """
        PROACTIVE: Search for conversations about specific keywords.
        
        This is perfect for accounts with fewer followers - instead of waiting
        for mentions, we actively find conversations to contribute to.
        """
        logger.info(
            "searching_keyword_opportunities",
            keywords=len(self.search_keywords),
            keyword_list=self.search_keywords
        )
        
        all_results = []
        
        for keyword in self.search_keywords:
            try:
                logger.debug("searching_keyword", keyword=keyword)
                
                # Search for recent tweets about this keyword
                search_results = await self.search_tweets_by_keyword(keyword)
                
                if search_results:
                    logger.info(
                        "keyword_search_results",
                        keyword=keyword,
                        results_count=len(search_results)
                    )
                    
                    # Analyze each result for engagement opportunities
                    opportunities = await self.analyze_keyword_results(keyword, search_results)
                    self.content_opportunities.extend(opportunities)
                    all_results.extend(search_results)
                
                # Rate limit between searches
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(
                    "keyword_search_failed",
                    keyword=keyword,
                    error_type=type(e).__name__,
                    error_details=str(e)
                )
        
        logger.info(
            "keyword_search_completed",
            total_results=len(all_results),
            keywords_searched=len(self.search_keywords)
        )
        
        return all_results
    
    async def search_tweets_by_keyword(self, keyword: str, max_results: int = 10) -> List[Dict]:
        """Search for recent tweets containing a specific keyword."""
        try:
            # Ensure max_results is within API limits
            max_results = max(10, min(max_results, 100))
            
            logger.debug("executing_tweet_search", keyword=keyword, max_results=max_results)
            
            # Build search query
            query = f'"{keyword}" -is:retweet lang:en'
            
            # Use the read client for searches (App-Only auth)
            search_results = self.x_client.read_client.search_recent_tweets(
                query=query,
                max_results=max_results,
                expansions=['author_id'],
                tweet_fields=['created_at', 'public_metrics', 'context_annotations'],
                user_fields=['username', 'public_metrics']
            )
            
            results = []
            if search_results and hasattr(search_results, 'data') and search_results.data:
                for tweet in search_results.data:
                    tweet_dict = {
                        'id': tweet.id,
                        'text': tweet.text,
                        'author_id': tweet.author_id,
                        'created_at': tweet.created_at,
                        'public_metrics': getattr(tweet, 'public_metrics', {}),
                        'context_annotations': getattr(tweet, 'context_annotations', []),
                        'keyword': keyword
                    }
                    results.append(tweet_dict)
                    
                    logger.debug(
                        "tweet_found",
                        keyword=keyword,
                        tweet_id=tweet.id,
                        author_id=tweet.author_id,
                        text_preview=tweet.text[:100]
                    )
            
            logger.info(
                "keyword_search_completed",
                keyword=keyword,
                results_found=len(results)
            )
            
            return results
            
        except Exception as e:
            logger.error(
                "keyword_search_api_error",
                keyword=keyword,
                error_type=type(e).__name__,
                error_details=str(e)
            )
            return []
    
    async def analyze_keyword_results(self, keyword: str, search_results: List[Dict]) -> List[ContentOpportunity]:
        """Analyze keyword search results for engagement opportunities."""
        opportunities = []
        
        for tweet in search_results:
            try:
                tweet_text = tweet.get('text', '')
                tweet_id = tweet.get('id')
                author_id = tweet.get('author_id')
                
                logger.debug(
                    "analyzing_keyword_result",
                    keyword=keyword,
                    tweet_id=tweet_id,
                    text_preview=tweet_text[:100]
                )
                
                # Calculate relevance based on keyword and content
                relevance_score = await self.calculate_keyword_relevance(keyword, tweet)
                
                # Use Claude for sentiment analysis if available
                sentiment_score = 0.5  # Default
                engagement_potential = 0.5  # Default
                
                if self.claude_client:
                    try:
                        sentiment = await self.claude_client.analyze_sentiment(
                            text=tweet_text,
                            context=f"Found via keyword search for '{keyword}'"
                        )
                        
                        # Convert sentiment to numerical score
                        sentiment_score = self.sentiment_to_score(sentiment.overall_sentiment)
                        engagement_potential = sentiment.engagement_potential
                        
                        logger.debug(
                            "sentiment_analyzed",
                            tweet_id=tweet_id,
                            sentiment=sentiment.overall_sentiment,
                            engagement_potential=engagement_potential,
                            themes=sentiment.key_themes
                        )
                        
                    except Exception as e:
                        logger.warning(
                            "sentiment_analysis_failed",
                            tweet_id=tweet_id,
                            error=str(e)
                        )
                
                # Calculate urgency (keyword-based opportunities are generally less urgent)
                urgency_score = await self.calculate_keyword_urgency(tweet)
                
                # Determine response approach
                suggested_approach = await self.suggest_keyword_response_approach(keyword, tweet)
                
                # Enhanced filtering: Higher thresholds + shill detection + bot detection + v4/Unichain focus
                is_shill = await self._detect_shill_content(tweet_text)
                is_bot = await self._detect_bot_content(tweet)  # NEW: Bot detection
                has_v4_unichain_relevance = await self._check_v4_unichain_relevance(tweet_text, keyword)
                is_quality_discussion = await self._is_quality_human_discussion(tweet)  # NEW: Quality check
                
                # Much stricter thresholds to avoid low-quality opportunities and bots
                # Prioritize quality human discussions or very high relevance scores
                if ((relevance_score > 0.7 and sentiment_score > 0.5 and engagement_potential > 0.6 
                    and not is_shill and not is_bot and has_v4_unichain_relevance)
                    and (is_quality_discussion or relevance_score > 0.85)):
                    opportunity = ContentOpportunity(
                        trigger_type='keyword_search',
                        context={
                            'keyword': keyword,
                            'tweet_id': tweet_id,
                            'author_id': author_id,
                            'text': tweet_text,
                            'search_text': tweet_text,
                            'tweet_data': tweet,
                            'sentiment_score': sentiment_score,
                            'engagement_potential': engagement_potential
                        },
                        relevance_score=relevance_score,
                        urgency_score=urgency_score,
                        suggested_approach=suggested_approach,
                        discovered_at=datetime.now(),
                        expires_at=datetime.now() + timedelta(hours=6)  # Keyword opportunities last longer
                    )
                    
                    opportunities.append(opportunity)
                    
                    logger.info(
                        "keyword_opportunity_identified",
                        keyword=keyword,
                        tweet_id=tweet_id,
                        relevance_score=relevance_score,
                        sentiment_score=sentiment_score,
                        engagement_potential=engagement_potential,
                        approach=suggested_approach
                    )
                
            except Exception as e:
                logger.error(
                    "keyword_result_analysis_error",
                    keyword=keyword,
                    tweet_id=tweet.get('id', 'unknown'),
                    error_type=type(e).__name__,
                    error_details=str(e)
                )
        
        return opportunities
    
    def sentiment_to_score(self, sentiment: str) -> float:
        """Convert sentiment string to numerical score."""
        sentiment_map = {
            'positive': 0.8,
            'neutral': 0.5,
            'negative': 0.2
        }
        return sentiment_map.get(sentiment.lower(), 0.5)
    
    async def calculate_keyword_relevance(self, keyword: str, tweet: Dict) -> float:
        """Calculate how relevant a keyword search result is with enhanced v4/Unichain focus."""
        text = tweet.get('text', '').lower()
        keyword_lower = keyword.lower()
        
        # Base relevance from keyword presence
        keyword_relevance = 1.0 if keyword_lower in text else 0.0
        
        # Enhanced boost for technical discussions and questions
        technical_indicators = ['how does', 'technical', 'implementation', 'architecture', 'protocol', 'smart contract']
        discussion_indicators = ['?', 'thoughts', 'opinion', 'what do you think', 'insights', 'analysis']
        
        technical_boost = sum(0.3 for indicator in technical_indicators if indicator in text)
        discussion_boost = sum(0.2 for indicator in discussion_indicators if indicator in text)
        
        # Specific v4/Unichain relevance boost
        v4_terms = ['v4', 'hooks', 'unichain', 'concentrated liquidity', 'tick spacing']
        v4_boost = sum(0.4 for term in v4_terms if term in text)
        
        # Check public metrics if available
        metrics = tweet.get('public_metrics', {})
        like_count = metrics.get('like_count', 0)
        retweet_count = metrics.get('retweet_count', 0)
        reply_count = metrics.get('reply_count', 0)
        
        # Higher threshold for engagement to ensure quality
        engagement_score = min((like_count + retweet_count + reply_count) / 20, 0.3)
        
        total_relevance = min(keyword_relevance + technical_boost + discussion_boost + v4_boost + engagement_score, 1.0)
        
        logger.debug(
            "enhanced_keyword_relevance_calculated",
            keyword=keyword,
            keyword_relevance=keyword_relevance,
            technical_boost=technical_boost,
            discussion_boost=discussion_boost,
            v4_boost=v4_boost,
            engagement_score=engagement_score,
            total_relevance=total_relevance
        )
        
        return total_relevance
    
    async def calculate_keyword_urgency(self, tweet: Dict) -> float:
        """Calculate urgency for keyword-based opportunities."""
        text = tweet.get('text', '').lower()
        
        # Questions are more urgent
        if '?' in text:
            return 0.7
        
        # New/breaking news is urgent
        urgent_keywords = ['breaking', 'just announced', 'new', 'launch', 'update']
        if any(keyword in text for keyword in urgent_keywords):
            return 0.8
        
        # Regular keyword matches are lower urgency
        return 0.4
    
    async def suggest_keyword_response_approach(self, keyword: str, tweet: Dict) -> str:
        """Suggest response approach for keyword-based opportunities."""
        text = tweet.get('text', '').lower()
        
        # If it's a question, reply with helpful answer
        if '?' in text:
            return 'reply'
        
        # If it's news/announcement, consider quote tweet with analysis
        if any(word in text for word in ['announced', 'launches', 'releases', 'update']):
            return 'quote'
        
        # If it's discussion, join the conversation
        if any(word in text for word in ['discuss', 'thoughts', 'opinion']):
            return 'reply'
        
        # Default to quote tweet for keyword matches
        return 'quote'
    
    async def _detect_shill_content(self, text: str) -> bool:
        """Detect promotional/shill content that should be filtered out."""
        text_lower = text.lower()
        
        # Common shill indicators
        shill_indicators = [
            'check out', 'alpha hunters', 'join our', 'exclusive access',
            'limited time', 'don\'t miss out', 'revolutionary platform',
            'game changer', 'next moonshot', 'hidden gem', 'secret alpha',
            'redefining the standards', 'cutting edge tech', 'the future is here',
            'exclusive', 'limited', 'join now', 'get in early', 'massive gains'
        ]
        
        # Promotional patterns
        promotional_patterns = [
            'introducing', 'presenting', 'announcing', 'proud to announce',
            'we are', 'our platform', 'our protocol', 'our solution'
        ]
        
        # Check for multiple promotional indicators (likely shill)
        shill_count = sum(1 for indicator in shill_indicators if indicator in text_lower)
        promo_count = sum(1 for pattern in promotional_patterns if pattern in text_lower)
        
        # Too many promotional terms = likely shill
        if shill_count >= 2 or promo_count >= 2:
            return True
            
        # Check for excessive emoji or caps (common in shills)
        emoji_count = sum(1 for char in text if ord(char) > 127)
        caps_ratio = sum(1 for char in text if char.isupper()) / max(len(text), 1)
        
        if emoji_count > 5 or caps_ratio > 0.3:
            return True
            
        return False
    
    async def _detect_bot_content(self, tweet: Dict) -> bool:
        """Detect bot-generated content patterns and automated accounts."""
        text = tweet.get('text', '').lower()
        
        # Bot content patterns
        bot_indicators = [
            # Repetitive announcement templates
            r'breaking:\s+\w+\s+just',
            r'alert:\s+\w+\s+(launched|announced|released)',
            r'new:\s+\w+\s+(protocol|platform|dapp)',
            r'🚨\s*breaking',
            r'📢\s*announcement',
            
            # Generic excitement patterns (common in bots)
            r'excited to (announce|share|introduce|launch)',
            r'thrilled to (announce|share|introduce|launch)',
            r'proud to (announce|share|introduce|launch)',
            r'delighted to (announce|share|introduce|launch)',
            
            # Automated call-to-action patterns
            'don\'t miss out',
            'limited time',
            'act now',
            'join us today',
            'sign up now',
            'register today',
            'claim your spot',
            
            # Bot-like ending phrases
            'stay tuned for more updates',
            'follow us for the latest',
            'like and retweet',
            'share with your network',
            'tag your friends',
            
            # Generic protocol descriptions
            r'revolutionary (protocol|platform|solution)',
            r'game-changing (protocol|platform|solution)',
            r'next-gen(eration)? (protocol|platform|solution)',
            r'cutting-edge (protocol|platform|solution)',
            
            # Automated metrics boasting
            r'\d+%\s*(apy|apr|yield|returns)',
            r'\$\d+[kmb]?\s*(tvl|volume|liquidity)',
            r'over\s+\d+\s+users',
            r'trusted by\s+\d+',
        ]
        
        # Count bot pattern matches
        import re
        pattern_matches = 0
        for pattern in bot_indicators:
            if isinstance(pattern, str):
                if pattern in text:
                    pattern_matches += 1
            else:
                if re.search(pattern, text):
                    pattern_matches += 1
        
        # Check for excessive formatting (bot characteristic)
        emoji_patterns = ['🚀', '🔥', '💎', '🌟', '⚡', '💰', '🏆', '✨']
        emoji_count = sum(text.count(emoji) for emoji in emoji_patterns)
        
        # Check text structure for bot-like consistency
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        if len(sentences) >= 3:
            # Bots often have very consistent sentence lengths
            lengths = [len(s) for s in sentences]
            avg_length = sum(lengths) / len(lengths)
            length_variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
            if length_variance < 100:  # Very low variance suggests templated content
                pattern_matches += 1
        
        # Check for multiple hashtags (bot characteristic)
        hashtag_count = text.count('#')
        if hashtag_count > 4:
            pattern_matches += 1
        
        # Check for multiple links (bot characteristic)
        link_count = text.count('http://') + text.count('https://') + text.count('t.co/')
        if link_count > 2:
            pattern_matches += 1
        
        # Account-level bot indicators (if we have the data)
        author_metrics = tweet.get('author', {}).get('public_metrics', {})
        if author_metrics:
            followers = author_metrics.get('followers_count', 0)
            following = author_metrics.get('following_count', 0)
            tweets = author_metrics.get('tweet_count', 0)
            
            # Bot account patterns
            if followers < 100 and tweets > 1000:  # High activity, low followers
                pattern_matches += 1
            if following > followers * 10 and followers < 1000:  # Following way more than followers
                pattern_matches += 1
            if followers > 0 and following > 0:
                ratio = following / followers
                if ratio > 50:  # Extreme following ratio
                    pattern_matches += 2
        
        # Check account creation date if available
        created_at = tweet.get('author', {}).get('created_at', '')
        if created_at:
            try:
                from datetime import datetime
                account_age_days = (datetime.now() - datetime.fromisoformat(created_at.replace('Z', '+00:00'))).days
                if account_age_days < 30 and tweet.get('author', {}).get('public_metrics', {}).get('tweet_count', 0) > 500:
                    # New account with high activity - likely bot
                    pattern_matches += 2
            except:
                pass
        
        # Determine if it's a bot
        is_bot = (
            pattern_matches >= 3 or  # Multiple bot patterns
            emoji_count >= 8 or      # Excessive emojis
            (pattern_matches >= 2 and emoji_count >= 5)  # Combination
        )
        
        if is_bot:
            logger.info(
                "bot_content_detected",
                tweet_id=tweet.get('id', 'unknown'),
                pattern_matches=pattern_matches,
                emoji_count=emoji_count,
                hashtag_count=hashtag_count,
                text_preview=text[:100]
            )
        
        return is_bot
    
    async def _check_v4_unichain_relevance(self, text: str, keyword: str) -> bool:
        """Check if content has genuine v4/Unichain technical relevance."""
        text_lower = text.lower()
        
        # High-value v4/Unichain terms
        core_terms = ['v4', 'unichain', 'hooks', 'concentrated liquidity', 'tick spacing']
        technical_terms = [
            'smart contract', 'protocol', 'implementation', 'architecture',
            'mev', 'arbitrage', 'liquidity provision', 'yield farming',
            'autonomous', 'algorithm', 'machine learning', 'neural network'
        ]
        
        # Quality discussion indicators
        discussion_quality = [
            'technical analysis', 'deep dive', 'breakdown', 'explanation',
            'how it works', 'implementation details', 'pros and cons',
            'comparison', 'evaluation', 'research', 'study'
        ]
        
        # Must have at least one core term
        has_core_terms = any(term in text_lower for term in core_terms)
        has_technical_depth = any(term in text_lower for term in technical_terms)
        has_quality_discussion = any(term in text_lower for term in discussion_quality)
        
        # For generic keywords like "ai-powered routing", require higher relevance
        if keyword in ['ai-powered routing', 'uniswap automation']:
            return has_core_terms and (has_technical_depth or has_quality_discussion)
        
        # For specific v4/Unichain keywords, just need core terms + some technical context
        return has_core_terms or has_technical_depth
    
    async def _is_quality_human_discussion(self, tweet: Dict) -> bool:
        """Identify high-quality human discussions worth engaging with."""
        text = tweet.get('text', '')
        
        # Positive indicators of human discussion
        human_indicators = [
            # Questions and curiosity
            r'\?(?!\?)(?!\s*$)',  # Real questions (not just "???" or trailing ?)
            r'(what|how|why|when|where|who)\s+\w+',  # Question words
            r'(anyone|someone|anybody|somebody)\s+(know|think|tried|using)',
            r'thoughts on',
            r'opinions on',
            r'curious about',
            r'wondering if',
            
            # Technical discussion markers
            r'(tried|tested|built|deployed|implemented)',
            r'(works|working|worked)\s+(with|on)',
            r'experience with',
            r'lessons learned',
            r'best practices',
            r'pros and cons',
            
            # Personal experiences
            r"(i've|we've|i have|we have)\s+(been|tried|built|used)",
            r'in my experience',
            r'found that',
            r'discovered that',
            r'learned that',
            
            # Thoughtful analysis
            r'interesting (point|aspect|approach)',
            r'worth noting',
            r'important to (note|mention|consider)',
            r'key (insight|takeaway|point)',
            
            # Community engagement
            r'thanks for',
            r'great point',
            r'good question',
            r'agree with',
            r'disagree with',
        ]
        
        # Count human discussion indicators
        import re
        human_score = 0
        for pattern in human_indicators:
            if re.search(pattern, text.lower()):
                human_score += 1
        
        # Check for conversation markers
        is_reply = tweet.get('referenced_tweets', [])
        if is_reply and any(ref.get('type') == 'replied_to' for ref in is_reply):
            human_score += 1  # Part of a conversation
        
        # Check for mentions (engaging with others)
        mentions = tweet.get('entities', {}).get('mentions', [])
        if 1 <= len(mentions) <= 3:  # Some mentions but not spam
            human_score += 1
        
        # Length check - very short or very long tweets are often low quality
        text_length = len(text)
        if 50 < text_length < 500:  # Reasonable discussion length
            human_score += 1
        
        # Check author engagement history
        author_metrics = tweet.get('author', {}).get('public_metrics', {})
        if author_metrics:
            followers = author_metrics.get('followers_count', 0)
            tweets = author_metrics.get('tweet_count', 0)
            
            # Established accounts with reasonable activity
            if 100 < followers < 50000 and 500 < tweets < 20000:
                human_score += 1
        
        # Higher score indicates more human-like quality discussion
        return human_score >= 3
    
    async def check_trending_topics(self) -> List[TrendingTopic]:
        """Monitor trending topics relevant to our interests."""
        logger.info("checking_trending_topics")
        
        # TODO: Implement trending topics retrieval
        # For now, we'll simulate this functionality
        # In a real implementation, this would:
        # 1. Use X API trends endpoint
        # 2. Search for trending hashtags in our topic areas
        # 3. Analyze trending keywords
        
        logger.info("trending_topics_check_completed", trends_found=0)
        return []
    
    async def analyze_conversations(self):
        """Analyze ongoing conversations for context and opportunities."""
        logger.info("analyzing_conversations_for_context")
        
        # TODO: Implement conversation analysis
        # This would:
        # 1. Follow reply chains from our mentions
        # 2. Understand conversation context
        # 3. Identify good entry points for engagement
        
        logger.info("conversation_analysis_completed")
    
    async def identify_content_opportunities(self) -> List[ContentOpportunity]:
        """Identify and prioritize content creation opportunities."""
        # Clean up expired opportunities
        current_time = datetime.now()
        active_opportunities = [
            opp for opp in self.content_opportunities
            if not opp.expires_at or opp.expires_at > current_time
        ]
        
        # Remove expired opportunities
        expired_count = len(self.content_opportunities) - len(active_opportunities)
        if expired_count > 0:
            logger.info("expired_opportunities_removed", count=expired_count)
        
        self.content_opportunities = active_opportunities
        
        # Sort by relevance and urgency
        prioritized = sorted(
            self.content_opportunities,
            key=lambda x: (x.relevance_score * x.urgency_score),
            reverse=True
        )
        
        # Return new opportunities from this cycle
        new_opportunities = [
            opp for opp in prioritized
            if (current_time - opp.discovered_at).seconds < 300  # Last 5 minutes
        ]
        
        if new_opportunities:
            logger.info(
                "new_content_opportunities_identified",
                count=len(new_opportunities),
                top_score=new_opportunities[0].relevance_score * new_opportunities[0].urgency_score
            )
        
        return new_opportunities
    
    def get_top_opportunities(self, limit: int = 5) -> List[ContentOpportunity]:
        """Get the top content opportunities for action."""
        current_time = datetime.now()
        
        # Filter active opportunities
        active = [
            opp for opp in self.content_opportunities
            if not opp.expires_at or opp.expires_at > current_time
        ]
        
        # Sort by combined score
        sorted_opportunities = sorted(
            active,
            key=lambda x: (x.relevance_score * x.urgency_score),
            reverse=True
        )
        
        return sorted_opportunities[:limit]
    
    def stop_monitoring(self):
        """Stop the monitoring loop."""
        logger.info("trend_monitoring_stopped")
        self.monitoring_active = False
    
    def add_target_topic(self, topic: str):
        """Add a new topic to monitor."""
        self.target_topics.append(topic)
        self.monitored_keywords.add(topic.lower())
        
        logger.info("target_topic_added", topic=topic, total_topics=len(self.target_topics))
    
    def get_monitoring_stats(self) -> Dict:
        """Get current monitoring statistics."""
        current_time = datetime.now()
        active_opportunities = [
            opp for opp in self.content_opportunities
            if not opp.expires_at or opp.expires_at > current_time
        ]
        
        stats = {
            'monitoring_active': self.monitoring_active,
            'target_topics': len(self.target_topics),
            'trending_topics': len(self.trending_topics),
            'active_opportunities': len(active_opportunities),
            'total_opportunities_discovered': len(self.content_opportunities),
            'last_mentions_check': self.last_mentions_check,
            'last_trends_check': self.last_trends_check
        }
        
        logger.info("monitoring_stats_generated", stats=stats)
        return stats
    
    def _get_ai_blockchain_keywords(self) -> List[str]:
        """Get enhanced AI x blockchain keyword sets for convergence topic monitoring"""
        return [
            # AI Agents & Autonomous Trading
            "ai agents blockchain",
            "autonomous trading",
            "intelligent contracts",
            "machine learning defi",
            "ai infrastructure crypto",
            "ml protocols",
            
            # HFT + AI Integration
            "hft ai",
            "algorithmic trading defi",
            "ml trading",
            "quantitative crypto",
            "ai trading strategies",
            "predictive trading",
            
            # Uniswap v4 + AI Specific
            "v4 hooks ai",
            "uniswap automation",
            "smart routing ai",
            "predictive mev",
            "intelligent hooks",
            "automated arbitrage",
            
            # Technical Convergence
            "ai blockchain convergence",
            "next generation defi",
            "intelligent infrastructure",
            "autonomous protocols",
            "machine learning trading",
            "predictive analytics crypto",
            
            # Innovation Indicators
            "ai powered defi",
            "intelligent amm",
            "autonomous market makers",
            "ai enhanced protocols",
            "smart contract ai",
            "blockchain machine learning"
        ]
    
    async def enhanced_keyword_analysis(self, keyword: str, tweet: Dict) -> Dict:
        """Enhanced analysis for AI x blockchain convergence opportunities"""
        text = tweet.get('text', '').lower()
        
        # AI x Blockchain convergence scoring
        ai_terms = ['ai', 'artificial intelligence', 'machine learning', 'ml', 'neural', 'algorithm', 'predictive', 'intelligent', 'autonomous']
        blockchain_terms = ['blockchain', 'crypto', 'defi', 'uniswap', 'ethereum', 'smart contract', 'protocol', 'amm', 'dex']
        convergence_terms = ['integration', 'convergence', 'automation', 'enhanced', 'powered', 'driven']
        
        ai_score = sum(1 for term in ai_terms if term in text) / len(ai_terms)
        blockchain_score = sum(1 for term in blockchain_terms if term in text) / len(blockchain_terms)
        convergence_score = sum(1 for term in convergence_terms if term in text) / len(convergence_terms)
        
        # Calculate AI x blockchain relevance
        ai_blockchain_relevance = min(1.0, (ai_score + blockchain_score + convergence_score) / 2)
        
        # Technical depth indicators
        technical_terms = ['implementation', 'architecture', 'performance', 'optimization', 'algorithm', 'model', 'framework', 'infrastructure']
        technical_depth = min(1.0, sum(1 for term in technical_terms if term in text) / 3)
        
        # Innovation indicators
        innovation_terms = ['breakthrough', 'revolutionary', 'next generation', 'cutting edge', 'advanced', 'novel', 'innovative']
        innovation_score = min(1.0, sum(1 for term in innovation_terms if term in text) / 2)
        
        # Engagement opportunity indicators
        engagement_terms = ['thoughts', 'opinion', 'what do you think', 'feedback', 'discussion', 'debate', 'question']
        engagement_opportunity = min(1.0, sum(1 for term in engagement_terms if term in text) / 2)
        
        # Time sensitivity indicators
        urgent_terms = ['breaking', 'just announced', 'new', 'launch', 'update', 'released', 'live']
        time_sensitivity = min(1.0, sum(1 for term in urgent_terms if term in text) / 2)
        
        return {
            'ai_blockchain_relevance': ai_blockchain_relevance,
            'technical_depth': technical_depth,
            'innovation_score': innovation_score,
            'engagement_opportunity': engagement_opportunity,
            'time_sensitivity': time_sensitivity,
            'overall_ai_blockchain_score': (ai_blockchain_relevance * 0.4 + technical_depth * 0.3 + innovation_score * 0.3)
        }


# Export main classes
__all__ = ['TrendMonitor', 'TrendingTopic', 'ContentOpportunity']