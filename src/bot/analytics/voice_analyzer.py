"""
Voice Analytics and Learning System

Analyzes user's posting history to learn voice patterns, engagement drivers,
and successful content characteristics for voice tuning.
"""

import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import structlog
import re

# Configure structured logging
logger = structlog.get_logger(__name__)


@dataclass
class PostAnalysis:
    """Analysis of a single post."""
    tweet_id: str
    text: str
    created_at: datetime
    engagement_metrics: Dict  # likes, retweets, replies, etc.
    engagement_score: float  # normalized 0-1 score
    content_themes: List[str]
    hashtags: List[str]
    mentions: List[str]
    voice_characteristics: Dict
    technical_depth: float
    enthusiasm_level: float
    helpfulness_score: float


@dataclass
class VoiceProfile:
    """Learned voice profile from historical posts."""
    successful_patterns: Dict
    engagement_drivers: List[str]
    preferred_hashtags: List[str]
    common_phrases: List[str]
    technical_vocabulary: List[str]
    tone_distribution: Dict  # technical, helpful, enthusiastic, etc.
    optimal_length_range: Tuple[int, int]
    best_posting_themes: List[str]
    engagement_correlations: Dict


@dataclass
class VoiceTuningRecommendations:
    """Recommendations for voice tuning based on analysis."""
    voice_adjustments: List[str]
    content_suggestions: List[str]
    engagement_optimizations: List[str]
    hashtag_recommendations: List[str]
    tone_recommendations: Dict
    length_recommendations: str


class VoiceAnalyzer:
    """
    Analyzes posting history to learn voice patterns and engagement drivers.
    
    Features:
    - Historical post analysis with engagement correlation
    - Voice pattern recognition and categorization
    - Successful content characteristic identification
    - Engagement driver analysis
    - Voice tuning recommendations
    - Performance-based learning
    """
    
    def __init__(self, x_client, claude_client):
        self.x_client = x_client
        self.claude_client = claude_client
        
        # Analysis data
        self.post_analyses: List[PostAnalysis] = []
        self.voice_profile: Optional[VoiceProfile] = None
        self.engagement_patterns = defaultdict(list)
        
        # Analysis stats
        self.analysis_stats = {
            'posts_analyzed': 0,
            'engagement_data_points': 0,
            'voice_patterns_identified': 0,
            'last_analysis': None
        }
        
        logger.info("voice_analyzer_initialized")
    
    async def analyze_posting_history(self, max_posts: int = 50) -> VoiceProfile:
        """Analyze user's posting history to learn voice patterns."""
        logger.info("analyzing_posting_history", max_posts=max_posts)
        
        try:
            # Get user's recent tweets
            user_tweets = await self._fetch_user_tweets(max_posts)
            
            if not user_tweets:
                logger.warning("no_tweets_found_for_analysis")
                return self._create_default_voice_profile()
            
            logger.info("tweets_fetched_for_analysis", count=len(user_tweets))
            
            # Analyze each tweet
            analyses = []
            for tweet in user_tweets:
                try:
                    analysis = await self._analyze_single_post(tweet)
                    analyses.append(analysis)
                    await asyncio.sleep(0.5)  # Rate limit
                except Exception as e:
                    logger.warning("post_analysis_failed", tweet_id=tweet.get('id'), error=str(e))
            
            self.post_analyses = analyses
            
            # Generate voice profile from analyses
            voice_profile = await self._generate_voice_profile(analyses)
            self.voice_profile = voice_profile
            
            # Update stats
            self.analysis_stats['posts_analyzed'] = len(analyses)
            self.analysis_stats['last_analysis'] = datetime.now()
            
            logger.info(
                "posting_history_analysis_completed",
                posts_analyzed=len(analyses),
                engagement_patterns=len(self.engagement_patterns),
                voice_characteristics=len(voice_profile.successful_patterns)
            )
            
            return voice_profile
            
        except Exception as e:
            logger.error("posting_history_analysis_failed", error=str(e))
            return self._create_default_voice_profile()
    
    async def _fetch_user_tweets(self, max_posts: int) -> List[Dict]:
        """Fetch user's recent tweets with engagement metrics."""
        try:
            # Get authenticated user info using the OAuth 1.0a client
            me = self.x_client.client.get_me()
            user_id = me.data.id
            
            logger.info("fetching_user_tweets", user_id=user_id, max_posts=max_posts)
            
            # Get user's tweets with engagement metrics using OAuth 1.0a client
            tweets = self.x_client.client.get_users_tweets(
                id=user_id,
                max_results=min(max_posts, 100),  # API limit
                tweet_fields=['created_at', 'public_metrics', 'context_annotations'],
                exclude=['retweets', 'replies']  # Focus on original content
            )
            
            tweet_data = []
            if tweets and tweets.data:
                logger.info("processing_tweets", tweet_count=len(tweets.data))
                for i, tweet in enumerate(tweets.data):
                    try:
                        logger.debug("processing_tweet", tweet_index=i, tweet_id=getattr(tweet, 'id', 'unknown'))
                        
                        # Handle public_metrics - it might be a dict already or a named tuple
                        public_metrics = {}
                        if tweet.public_metrics:
                            if hasattr(tweet.public_metrics, '_asdict'):
                                public_metrics = tweet.public_metrics._asdict()
                            elif isinstance(tweet.public_metrics, dict):
                                public_metrics = tweet.public_metrics
                            else:
                                # Convert object attributes to dict
                                public_metrics = {
                                    'like_count': getattr(tweet.public_metrics, 'like_count', 0),
                                    'retweet_count': getattr(tweet.public_metrics, 'retweet_count', 0),
                                    'reply_count': getattr(tweet.public_metrics, 'reply_count', 0),
                                    'quote_count': getattr(tweet.public_metrics, 'quote_count', 0)
                                }
                        
                        tweet_dict = {
                            'id': str(tweet.id),
                            'text': str(tweet.text),
                            'created_at': tweet.created_at,
                            'public_metrics': public_metrics,
                            'context_annotations': getattr(tweet, 'context_annotations', [])
                        }
                        tweet_data.append(tweet_dict)
                        logger.debug("tweet_processed_successfully", tweet_id=tweet_dict['id'], text_length=len(tweet_dict['text']))
                        
                    except Exception as e:
                        logger.warning("tweet_processing_failed", tweet_index=i, error=str(e), error_type=type(e).__name__)
                        continue
            
            if not tweet_data and tweets:
                # API call succeeded but no tweets found
                logger.warning("no_tweets_in_response", has_data=bool(tweets.data), response_type=type(tweets).__name__)
                if hasattr(tweets, 'data') and tweets.data is not None:
                    logger.info("empty_tweets_data", data_type=type(tweets.data).__name__, data_length=len(tweets.data) if hasattr(tweets.data, '__len__') else 'unknown')
            
            logger.info("user_tweets_fetched", count=len(tweet_data))
            return tweet_data
            
        except Exception as e:
            logger.error("user_tweets_fetch_failed", error=str(e))
            return []
    
    async def _analyze_single_post(self, tweet: Dict) -> PostAnalysis:
        """Analyze a single post for voice characteristics and engagement."""
        text = tweet.get('text', '')
        tweet_id = tweet.get('id', 'unknown')
        
        logger.debug("analyzing_single_post", tweet_id=tweet_id, text_length=len(text))
        
        # Extract basic features
        hashtags = re.findall(r'#\w+', text)
        mentions = re.findall(r'@\w+', text)
        
        # Get engagement metrics
        metrics = tweet.get('public_metrics', {})
        engagement_score = self._calculate_engagement_score(metrics)
        
        # Analyze voice characteristics with Claude
        voice_characteristics = await self._analyze_voice_characteristics(text)
        
        # Calculate content scores
        technical_depth = self._calculate_technical_depth(text)
        enthusiasm_level = self._calculate_enthusiasm_level(text)
        helpfulness_score = self._calculate_helpfulness_score(text)
        
        # Extract themes
        content_themes = await self._extract_content_themes(text)
        
        analysis = PostAnalysis(
            tweet_id=tweet_id,
            text=text,
            created_at=tweet.get('created_at', datetime.now()),
            engagement_metrics=metrics,
            engagement_score=engagement_score,
            content_themes=content_themes,
            hashtags=hashtags,
            mentions=mentions,
            voice_characteristics=voice_characteristics,
            technical_depth=technical_depth,
            enthusiasm_level=enthusiasm_level,
            helpfulness_score=helpfulness_score
        )
        
        logger.debug(
            "post_analysis_completed",
            tweet_id=tweet_id,
            engagement_score=engagement_score,
            technical_depth=technical_depth,
            themes_count=len(content_themes)
        )
        
        return analysis
    
    def _calculate_engagement_score(self, metrics: Dict) -> float:
        """Calculate normalized engagement score (0-1)."""
        likes = metrics.get('like_count', 0)
        retweets = metrics.get('retweet_count', 0)
        replies = metrics.get('reply_count', 0)
        
        # Weight different engagement types
        weighted_engagement = (likes * 1.0) + (retweets * 2.0) + (replies * 3.0)
        
        # Normalize to 0-1 scale (log scale for better distribution)
        if weighted_engagement == 0:
            return 0.0
        
        # Use log scale to handle wide range of engagement levels
        import math
        normalized = min(math.log10(weighted_engagement + 1) / 3.0, 1.0)  # Assume max ~1000 engagement
        
        return normalized
    
    async def _analyze_voice_characteristics(self, text: str) -> Dict:
        """Analyze voice characteristics using Claude."""
        try:
            prompt = f"""
            Analyze the voice characteristics of this tweet:
            
            "{text}"
            
            Rate each characteristic from 0.0 to 1.0:
            - technical_expertise: How much technical knowledge is shown
            - approachability: How accessible the language is
            - enthusiasm: Level of excitement/positivity
            - helpfulness: How much value it provides to readers
            - authority: How confident/authoritative the tone is
            - conversational: How casual/friendly vs formal
            
            Return only JSON:
            {{
                "technical_expertise": 0.8,
                "approachability": 0.7,
                "enthusiasm": 0.6,
                "helpfulness": 0.9,
                "authority": 0.8,
                "conversational": 0.5
            }}
            """
            
            # For now, use simplified analysis
            # TODO: Implement Claude-based voice analysis
            characteristics = {
                "technical_expertise": self._calculate_technical_depth(text),
                "approachability": self._calculate_approachability(text),
                "enthusiasm": self._calculate_enthusiasm_level(text),
                "helpfulness": self._calculate_helpfulness_score(text),
                "authority": self._calculate_authority_level(text),
                "conversational": self._calculate_conversational_level(text)
            }
            
            return characteristics
            
        except Exception as e:
            logger.warning("voice_characteristics_analysis_failed", error=str(e))
            return {
                "technical_expertise": 0.5,
                "approachability": 0.5,
                "enthusiasm": 0.5,
                "helpfulness": 0.5,
                "authority": 0.5,
                "conversational": 0.5
            }
    
    def _calculate_technical_depth(self, text: str) -> float:
        """Calculate technical depth score."""
        technical_terms = [
            'defi', 'protocol', 'smart contract', 'blockchain', 'dex', 'amm',
            'liquidity', 'yield', 'staking', 'governance', 'dao', 'token',
            'consensus', 'validator', 'node', 'gas', 'ethereum', 'layer',
            'composability', 'interoperability', 'permissionless', 'trustless',
            'decentralized', 'immutable', 'cryptographic', 'hash', 'merkle',
            'proof', 'stake', 'mining', 'fork', 'mainnet', 'testnet'
        ]
        
        text_lower = text.lower()
        matches = sum(1 for term in technical_terms if term in text_lower)
        
        # Normalize by text length and term frequency
        score = min(matches / 5.0, 1.0)  # Max score at 5+ technical terms
        return score
    
    def _calculate_approachability(self, text: str) -> float:
        """Calculate how approachable/accessible the language is."""
        approachable_indicators = [
            'simple', 'easy', 'understand', 'explain', 'learn', 'guide',
            'help', 'how', 'why', 'what', 'intro', 'basics', 'beginner',
            'everyone', 'anyone', 'folks', 'people', 'community'
        ]
        
        complex_indicators = [
            'sophisticated', 'advanced', 'complex', 'intricate', 'nuanced',
            'comprehensive', 'elaborate', 'detailed', 'technical', 'expert'
        ]
        
        text_lower = text.lower()
        approachable_count = sum(1 for term in approachable_indicators if term in text_lower)
        complex_count = sum(1 for term in complex_indicators if term in text_lower)
        
        # Base score from approachable language
        score = min(approachable_count / 3.0, 1.0)
        
        # Reduce score for overly complex language
        score = max(score - (complex_count * 0.2), 0.0)
        
        # Boost for questions (more approachable)
        if '?' in text:
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_enthusiasm_level(self, text: str) -> float:
        """Calculate enthusiasm level."""
        enthusiasm_indicators = [
            '!', 'amazing', 'awesome', 'great', 'love', 'excited', 'fantastic',
            'incredible', 'brilliant', 'outstanding', 'excellent', 'wonderful',
            'impressive', 'remarkable', 'extraordinary', 'phenomenal', 'superb',
            'thrilled', 'pumped', 'stoked', 'fired up', 'can\'t wait', 'huge',
            'massive', 'breakthrough', 'revolutionary', 'groundbreaking'
        ]
        
        text_lower = text.lower()
        
        # Count enthusiasm indicators
        matches = sum(1 for term in enthusiasm_indicators if term in text_lower)
        
        # Count exclamation marks
        exclamations = text.count('!')
        
        # Calculate score
        score = min((matches + exclamations) / 4.0, 1.0)
        
        return score
    
    def _calculate_helpfulness_score(self, text: str) -> float:
        """Calculate how helpful the content is."""
        helpful_indicators = [
            'help', 'guide', 'how to', 'tip', 'advice', 'recommend', 'suggest',
            'explain', 'breakdown', 'analysis', 'insight', 'understand',
            'learn', 'teach', 'show', 'demonstrate', 'example', 'tutorial',
            'solution', 'answer', 'clarify', 'overview', 'summary'
        ]
        
        educational_patterns = [
            r'here\'s how', r'here\'s why', r'let me explain', r'breakdown:',
            r'key points?', r'important to', r'remember that', r'keep in mind'
        ]
        
        text_lower = text.lower()
        
        # Count helpful indicators
        helpful_count = sum(1 for term in helpful_indicators if term in text_lower)
        
        # Check for educational patterns
        pattern_count = sum(1 for pattern in educational_patterns if re.search(pattern, text_lower))
        
        # Check for questions (can be helpful by prompting discussion)
        question_boost = 0.2 if '?' in text else 0.0
        
        score = min((helpful_count + pattern_count) / 3.0 + question_boost, 1.0)
        
        return score
    
    def _calculate_authority_level(self, text: str) -> float:
        """Calculate authority/confidence level."""
        authority_indicators = [
            'analysis', 'data shows', 'research', 'study', 'evidence',
            'proven', 'confirmed', 'established', 'fact', 'clearly',
            'definitely', 'certainly', 'obviously', 'undoubtedly',
            'experience', 'years', 'expert', 'professional', 'industry'
        ]
        
        uncertain_indicators = [
            'maybe', 'perhaps', 'possibly', 'might', 'could be', 'seems',
            'appears', 'i think', 'i believe', 'in my opinion', 'probably',
            'likely', 'unsure', 'not sure', 'unclear', 'confusing'
        ]
        
        text_lower = text.lower()
        
        authority_count = sum(1 for term in authority_indicators if term in text_lower)
        uncertain_count = sum(1 for term in uncertain_indicators if term in text_lower)
        
        # Base score from authority indicators
        score = min(authority_count / 3.0, 1.0)
        
        # Reduce for uncertainty
        score = max(score - (uncertain_count * 0.3), 0.0)
        
        return score
    
    def _calculate_conversational_level(self, text: str) -> float:
        """Calculate how conversational vs formal the tone is."""
        conversational_indicators = [
            'hey', 'hi', 'yo', 'folks', 'guys', 'everyone', 'what do you think',
            'thoughts?', 'agree?', 'right?', 'lol', 'haha', 'btw', 'fyi',
            'tbh', 'imo', 'just', 'really', 'pretty', 'super', 'kinda',
            'gonna', 'wanna', 'gotta', '...', 'omg', 'wow'
        ]
        
        formal_indicators = [
            'furthermore', 'however', 'nevertheless', 'therefore', 'moreover',
            'consequently', 'additionally', 'specifically', 'particularly',
            'significantly', 'subsequently', 'accordingly', 'thus', 'hence'
        ]
        
        text_lower = text.lower()
        
        conversational_count = sum(1 for term in conversational_indicators if term in text_lower)
        formal_count = sum(1 for term in formal_indicators if term in text_lower)
        
        # Calculate conversational score
        score = min(conversational_count / 3.0, 1.0)
        
        # Reduce for formal language
        score = max(score - (formal_count * 0.2), 0.0)
        
        return score
    
    async def _extract_content_themes(self, text: str) -> List[str]:
        """Extract main themes/topics from the text."""
        # DeFi/Crypto themes
        defi_keywords = {
            'uniswap': 'DEX/AMM',
            'defi': 'DeFi',
            'protocol': 'Protocol Development',
            'yield': 'Yield Farming',
            'liquidity': 'Liquidity Management',
            'staking': 'Staking',
            'governance': 'DAO Governance',
            'smart contract': 'Smart Contracts',
            'blockchain': 'Blockchain Technology',
            'ethereum': 'Ethereum',
            'layer 2': 'Layer 2 Scaling',
            'nft': 'NFTs',
            'dao': 'DAO',
            'token': 'Tokenomics'
        }
        
        themes = []
        text_lower = text.lower()
        
        for keyword, theme in defi_keywords.items():
            if keyword in text_lower:
                themes.append(theme)
        
        # Remove duplicates
        return list(set(themes))
    
    async def _generate_voice_profile(self, analyses: List[PostAnalysis]) -> VoiceProfile:
        """Generate voice profile from post analyses."""
        if not analyses:
            return self._create_default_voice_profile()
        
        logger.info("generating_voice_profile", analyses_count=len(analyses))
        
        # Analyze successful patterns (top 25% by engagement)
        analyses_by_engagement = sorted(analyses, key=lambda x: x.engagement_score, reverse=True)
        top_quarter = analyses_by_engagement[:max(1, len(analyses) // 4)]
        
        # Extract patterns from successful posts
        successful_patterns = self._extract_successful_patterns(top_quarter)
        
        # Find engagement drivers
        engagement_drivers = self._find_engagement_drivers(analyses)
        
        # Aggregate voice characteristics
        avg_characteristics = self._aggregate_voice_characteristics(analyses)
        
        # Find optimal content patterns
        hashtag_usage = self._analyze_hashtag_patterns(analyses)
        length_patterns = self._analyze_length_patterns(analyses)
        theme_performance = self._analyze_theme_performance(analyses)
        
        voice_profile = VoiceProfile(
            successful_patterns=successful_patterns,
            engagement_drivers=engagement_drivers,
            preferred_hashtags=hashtag_usage['most_successful'][:10],
            common_phrases=successful_patterns.get('phrases', []),
            technical_vocabulary=successful_patterns.get('technical_terms', []),
            tone_distribution=avg_characteristics,
            optimal_length_range=length_patterns['optimal_range'],
            best_posting_themes=theme_performance['top_themes'][:5],
            engagement_correlations=self._calculate_engagement_correlations(analyses)
        )
        
        logger.info(
            "voice_profile_generated",
            successful_patterns_count=len(successful_patterns),
            engagement_drivers_count=len(engagement_drivers),
            preferred_hashtags_count=len(voice_profile.preferred_hashtags)
        )
        
        return voice_profile
    
    def _extract_successful_patterns(self, top_posts: List[PostAnalysis]) -> Dict:
        """Extract patterns from most successful posts."""
        patterns = {
            'phrases': [],
            'technical_terms': [],
            'structures': [],
            'engagement_tactics': []
        }
        
        # Extract common phrases from successful posts
        all_text = ' '.join(post.text for post in top_posts)
        
        # Find technical terms used in successful posts
        technical_terms = []
        for post in top_posts:
            if post.technical_depth > 0.5:
                # Extract technical words
                words = re.findall(r'\b\w+\b', post.text.lower())
                tech_words = [w for w in words if self._is_technical_term(w)]
                technical_terms.extend(tech_words)
        
        patterns['technical_terms'] = list(set(technical_terms))[:10]
        
        # Find engagement tactics
        engagement_tactics = []
        for post in top_posts:
            if '?' in post.text:
                engagement_tactics.append('questions')
            if post.hashtags:
                engagement_tactics.append('hashtags')
            if post.mentions:
                engagement_tactics.append('mentions')
            if post.enthusiasm_level > 0.6:
                engagement_tactics.append('enthusiasm')
        
        patterns['engagement_tactics'] = list(set(engagement_tactics))
        
        return patterns
    
    def _is_technical_term(self, word: str) -> bool:
        """Check if a word is a technical term."""
        technical_terms = {
            'defi', 'protocol', 'blockchain', 'ethereum', 'smart', 'contract',
            'liquidity', 'yield', 'staking', 'governance', 'dao', 'token',
            'dex', 'amm', 'swap', 'pool', 'farming', 'mining', 'validator',
            'consensus', 'decentralized', 'permissionless', 'trustless',
            'composability', 'interoperability', 'layer', 'scaling', 'gas',
            'transaction', 'block', 'hash', 'merkle', 'proof', 'stake'
        }
        return word in technical_terms
    
    def _find_engagement_drivers(self, analyses: List[PostAnalysis]) -> List[str]:
        """Find what drives engagement in posts."""
        drivers = []
        
        # Correlate characteristics with engagement
        high_engagement = [a for a in analyses if a.engagement_score > 0.5]
        
        if high_engagement:
            avg_technical = sum(a.technical_depth for a in high_engagement) / len(high_engagement)
            avg_enthusiasm = sum(a.enthusiasm_level for a in high_engagement) / len(high_engagement)
            avg_helpfulness = sum(a.helpfulness_score for a in high_engagement) / len(high_engagement)
            
            if avg_technical > 0.6:
                drivers.append('technical_expertise')
            if avg_enthusiasm > 0.6:
                drivers.append('enthusiasm')
            if avg_helpfulness > 0.6:
                drivers.append('helpfulness')
            
            # Check for specific patterns
            question_posts = [a for a in high_engagement if '?' in a.text]
            if len(question_posts) / len(high_engagement) > 0.3:
                drivers.append('questions')
            
            hashtag_posts = [a for a in high_engagement if a.hashtags]
            if len(hashtag_posts) / len(high_engagement) > 0.5:
                drivers.append('strategic_hashtags')
        
        return drivers
    
    def _aggregate_voice_characteristics(self, analyses: List[PostAnalysis]) -> Dict:
        """Aggregate voice characteristics across all posts."""
        if not analyses:
            return {}
        
        characteristics = defaultdict(list)
        
        for analysis in analyses:
            for char, value in analysis.voice_characteristics.items():
                characteristics[char].append(value)
        
        # Calculate averages
        avg_characteristics = {}
        for char, values in characteristics.items():
            avg_characteristics[char] = sum(values) / len(values)
        
        return avg_characteristics
    
    def _analyze_hashtag_patterns(self, analyses: List[PostAnalysis]) -> Dict:
        """Analyze hashtag usage patterns and success."""
        hashtag_performance = defaultdict(list)
        
        for analysis in analyses:
            for hashtag in analysis.hashtags:
                hashtag_performance[hashtag].append(analysis.engagement_score)
        
        # Calculate average performance for each hashtag
        hashtag_scores = {}
        for hashtag, scores in hashtag_performance.items():
            hashtag_scores[hashtag] = sum(scores) / len(scores)
        
        # Sort by performance
        sorted_hashtags = sorted(hashtag_scores.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'most_successful': [h[0] for h in sorted_hashtags],
            'performance_scores': hashtag_scores
        }
    
    def _analyze_length_patterns(self, analyses: List[PostAnalysis]) -> Dict:
        """Analyze optimal post length patterns."""
        length_engagement = [(len(a.text), a.engagement_score) for a in analyses]
        
        if not length_engagement:
            return {'optimal_range': (150, 280)}
        
        # Sort by engagement and find patterns
        high_engagement = sorted(length_engagement, key=lambda x: x[1], reverse=True)
        top_quarter = high_engagement[:max(1, len(high_engagement) // 4)]
        
        lengths = [item[0] for item in top_quarter]
        
        optimal_range = (min(lengths), max(lengths))
        
        return {
            'optimal_range': optimal_range,
            'average_successful_length': sum(lengths) / len(lengths)
        }
    
    def _analyze_theme_performance(self, analyses: List[PostAnalysis]) -> Dict:
        """Analyze which themes perform best."""
        theme_performance = defaultdict(list)
        
        for analysis in analyses:
            for theme in analysis.content_themes:
                theme_performance[theme].append(analysis.engagement_score)
        
        # Calculate average performance
        theme_scores = {}
        for theme, scores in theme_performance.items():
            if scores:  # Only include themes with data
                theme_scores[theme] = sum(scores) / len(scores)
        
        # Sort by performance
        sorted_themes = sorted(theme_scores.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'top_themes': [t[0] for t in sorted_themes],
            'theme_scores': theme_scores
        }
    
    def _calculate_engagement_correlations(self, analyses: List[PostAnalysis]) -> Dict:
        """Calculate correlations between characteristics and engagement."""
        correlations = {}
        
        if len(analyses) < 3:
            return correlations
        
        characteristics = ['technical_depth', 'enthusiasm_level', 'helpfulness_score']
        
        for char in characteristics:
            char_values = [getattr(a, char) for a in analyses]
            engagement_values = [a.engagement_score for a in analyses]
            
            # Simple correlation calculation
            correlation = self._calculate_correlation(char_values, engagement_values)
            correlations[char] = correlation
        
        return correlations
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate simple correlation coefficient."""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        mean_x = sum(x) / len(x)
        mean_y = sum(y) / len(y)
        
        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(len(x)))
        
        sum_sq_x = sum((x[i] - mean_x) ** 2 for i in range(len(x)))
        sum_sq_y = sum((y[i] - mean_y) ** 2 for i in range(len(y)))
        
        denominator = (sum_sq_x * sum_sq_y) ** 0.5
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _create_default_voice_profile(self) -> VoiceProfile:
        """Create default voice profile when no data is available."""
        return VoiceProfile(
            successful_patterns={
                'technical_terms': ['defi', 'protocol', 'blockchain', 'smart contract'],
                'engagement_tactics': ['questions', 'hashtags', 'helpfulness']
            },
            engagement_drivers=['technical_expertise', 'helpfulness'],
            preferred_hashtags=['#DeFi', '#Web3', '#Blockchain', '#Ethereum'],
            common_phrases=[],
            technical_vocabulary=['protocol', 'liquidity', 'governance', 'composability'],
            tone_distribution={
                'technical_expertise': 0.7,
                'approachability': 0.6,
                'enthusiasm': 0.5,
                'helpfulness': 0.8,
                'authority': 0.6,
                'conversational': 0.4
            },
            optimal_length_range=(150, 280),
            best_posting_themes=['DeFi', 'Protocol Development', 'Blockchain Technology'],
            engagement_correlations={'helpfulness_score': 0.6, 'technical_depth': 0.4}
        )
    
    async def generate_voice_tuning_recommendations(self) -> VoiceTuningRecommendations:
        """Generate recommendations for voice tuning based on analysis."""
        if not self.voice_profile:
            logger.warning("no_voice_profile_available_for_recommendations")
            return self._create_default_recommendations()
        
        profile = self.voice_profile
        
        # Voice adjustments based on successful patterns
        voice_adjustments = []
        
        tone_dist = profile.tone_distribution
        if tone_dist.get('technical_expertise', 0) > 0.7:
            voice_adjustments.append("Maintain high technical expertise - it drives engagement")
        
        if tone_dist.get('helpfulness', 0) > 0.6:
            voice_adjustments.append("Continue focusing on helpful content - strong correlation with engagement")
        
        if tone_dist.get('enthusiasm', 0) < 0.4:
            voice_adjustments.append("Consider adding more enthusiasm to increase engagement")
        
        # Content suggestions based on successful themes
        content_suggestions = []
        for theme in profile.best_posting_themes[:3]:
            content_suggestions.append(f"Create more content about {theme} - high engagement theme")
        
        # Engagement optimizations
        engagement_optimizations = []
        for driver in profile.engagement_drivers:
            if driver == 'questions':
                engagement_optimizations.append("Include questions to drive discussion")
            elif driver == 'technical_expertise':
                engagement_optimizations.append("Showcase technical knowledge - strong engagement driver")
            elif driver == 'helpfulness':
                engagement_optimizations.append("Focus on providing value and helping others")
        
        # Hashtag recommendations
        hashtag_recommendations = profile.preferred_hashtags[:5]
        
        # Tone recommendations
        tone_recommendations = {
            'technical_expertise': 'Maintain current level' if tone_dist.get('technical_expertise', 0) > 0.6 else 'Increase',
            'enthusiasm': 'Increase' if tone_dist.get('enthusiasm', 0) < 0.5 else 'Maintain',
            'helpfulness': 'Maintain high level' if tone_dist.get('helpfulness', 0) > 0.6 else 'Increase'
        }
        
        # Length recommendations
        optimal_min, optimal_max = profile.optimal_length_range
        length_recommendations = f"Optimal length: {optimal_min}-{optimal_max} characters"
        
        recommendations = VoiceTuningRecommendations(
            voice_adjustments=voice_adjustments,
            content_suggestions=content_suggestions,
            engagement_optimizations=engagement_optimizations,
            hashtag_recommendations=hashtag_recommendations,
            tone_recommendations=tone_recommendations,
            length_recommendations=length_recommendations
        )
        
        logger.info(
            "voice_tuning_recommendations_generated",
            adjustments_count=len(voice_adjustments),
            content_suggestions_count=len(content_suggestions),
            optimizations_count=len(engagement_optimizations)
        )
        
        return recommendations
    
    def _create_default_recommendations(self) -> VoiceTuningRecommendations:
        """Create default recommendations when no analysis is available."""
        return VoiceTuningRecommendations(
            voice_adjustments=[
                "Maintain technical expertise while staying approachable",
                "Focus on providing value in every post"
            ],
            content_suggestions=[
                "Create educational content about DeFi protocols",
                "Share insights about blockchain technology",
                "Explain complex concepts in simple terms"
            ],
            engagement_optimizations=[
                "Ask questions to encourage discussion",
                "Use relevant hashtags strategically",
                "Share actionable insights"
            ],
            hashtag_recommendations=['#DeFi', '#Web3', '#Blockchain', '#Ethereum'],
            tone_recommendations={
                'technical_expertise': 'Maintain high level',
                'helpfulness': 'Focus on value creation',
                'enthusiasm': 'Show passion for innovation'
            },
            length_recommendations="Aim for 150-280 characters for optimal engagement"
        )
    
    def get_analysis_stats(self) -> Dict:
        """Get voice analysis statistics."""
        return {
            **self.analysis_stats,
            'voice_profile_available': bool(self.voice_profile),
            'engagement_patterns_count': len(self.engagement_patterns)
        }


# Export main classes
__all__ = ['VoiceAnalyzer', 'PostAnalysis', 'VoiceProfile', 'VoiceTuningRecommendations']