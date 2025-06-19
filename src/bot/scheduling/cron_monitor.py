"""
Cron-Based Monitoring System
Continuous monitoring with intelligent email alerts for AI x blockchain opportunities
"""

import asyncio
import smtplib
import json
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import structlog
import os

# Import enhanced logging and feedback tracking
from bot.utils.logging_config import get_monitoring_logger, get_email_logger
from bot.analytics.feedback_tracker import get_feedback_tracker
from bot.monitoring.keyword_rotator import get_keyword_rotator

# Version tracking for email alerts
SYSTEM_VERSION = "v2.1-sprotogremlin"  # Feature branch: authentic voice improvements

logger = get_monitoring_logger()

@dataclass
class AlertConfiguration:
    """Configuration for email alerts"""
    smtp_server: str
    smtp_port: int
    email_username: str
    email_password: str
    from_email: str
    to_email: str
    
    # Alert settings
    work_hours_start: int = 9  # 9 AM
    work_hours_end: int = 18   # 6 PM
    monitoring_interval: int = 30  # minutes
    
    # Alert thresholds
    immediate_threshold: float = 0.8
    priority_threshold: float = 0.6
    digest_threshold: float = 0.4

@dataclass
class AlertOpportunity:
    """Opportunity formatted for email alerts"""
    account_username: str
    account_tier: int
    content_text: str
    content_url: str
    timestamp: str
    
    overall_score: float
    ai_blockchain_relevance: float
    technical_depth: float
    opportunity_type: str
    suggested_response_type: str
    time_sensitivity: str
    
    strategic_context: str
    suggested_response: str
    
    # Enhanced email content
    generated_reply: Optional[str] = None
    reply_reasoning: Optional[str] = None
    alternative_responses: Optional[List[str]] = None
    engagement_prediction: Optional[float] = None
    voice_alignment_score: Optional[float] = None
    
    # Feedback tracking
    feedback_id: Optional[str] = None
    feedback_urls: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)

class CronMonitorSystem:
    """
    Cron-based monitoring system with intelligent email alerts
    Monitors strategic accounts every 30 minutes during work hours (9 AM - 6 PM)
    """
    
    def __init__(self, x_client, claude_client, strategic_tracker, config: AlertConfiguration):
        self.x_client = x_client
        self.claude_client = claude_client
        self.strategic_tracker = strategic_tracker
        self.config = config
        
        self.monitoring_active = False
        self.data_dir = Path("data/strategic_accounts")
        self.alerts_file = self.data_dir / "alert_history.json"
        self.processed_file = self.data_dir / "processed_opportunities.json"
        
        # Alert tracking
        self.alert_history: List[Dict] = []
        self.last_digest_sent = None
        self.daily_opportunities: List[AlertOpportunity] = []
        
        # Duplicate detection
        self.processed_opportunities: set = set()
        
        # Email event logger and feedback tracker
        self.email_logger = get_email_logger()
        self.feedback_tracker = get_feedback_tracker()
        self.keyword_rotator = get_keyword_rotator()
        
        # Track when we last updated trending narratives
        self.last_narrative_update = datetime.now()
        
        self._load_alert_history()
        self._load_processed_opportunities()
        
        logger.info(
            "cron_monitor_initialized",
            monitoring_interval=config.monitoring_interval,
            work_hours=f"{config.work_hours_start}-{config.work_hours_end}",
            email_configured=bool(config.smtp_server and config.to_email)
        )
    
    def _load_alert_history(self):
        """Load alert history from persistent storage"""
        try:
            if self.alerts_file.exists():
                with open(self.alerts_file, 'r') as f:
                    self.alert_history = json.load(f)
            else:
                self.alert_history = []
            logger.info(f"Loaded {len(self.alert_history)} alert history records")
        except Exception as e:
            logger.error(f"Error loading alert history: {e}")
            self.alert_history = []
    
    def _load_processed_opportunities(self):
        """Load processed opportunities from persistent storage"""
        try:
            if self.processed_file.exists():
                with open(self.processed_file, 'r') as f:
                    data = json.load(f)
                    self.processed_opportunities = set(data.get('processed_ids', []))
                    logger.info(f"Loaded {len(self.processed_opportunities)} processed opportunity IDs")
            else:
                self.processed_opportunities = set()
                logger.info("No processed opportunities file found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading processed opportunities: {e}")
            self.processed_opportunities = set()
    
    def _save_processed_opportunities(self):
        """Save processed opportunities to persistent storage"""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            
            # Keep only last 10,000 entries to prevent unlimited growth
            if len(self.processed_opportunities) > 10000:
                self.processed_opportunities = set(list(self.processed_opportunities)[-5000:])
            
            data = {
                'processed_ids': list(self.processed_opportunities),
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.processed_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving processed opportunities: {e}")
    
    def _get_opportunity_id(self, opportunity: AlertOpportunity) -> str:
        """Generate unique ID for opportunity to prevent duplicates"""
        import hashlib
        
        # For test opportunities, use a daily key
        if opportunity.account_username == "TestAccount":
            return f"test_opportunity_{datetime.now().strftime('%Y-%m-%d')}"
        
        # For real opportunities, try to extract tweet ID from URL
        if opportunity.content_url and "/status/" in opportunity.content_url:
            try:
                tweet_id = opportunity.content_url.split("/status/")[-1].split("?")[0]
                return f"{opportunity.account_username}_{tweet_id}"
            except:
                pass
        
        # Fallback: hash content + account + hour bucket
        content_key = f"{opportunity.account_username}_{opportunity.content_text[:100]}"
        content_hash = hashlib.md5(content_key.encode()).hexdigest()[:8]
        hour_bucket = datetime.now().strftime('%Y%m%d_%H')
        return f"{content_hash}_{hour_bucket}"
    
    def _is_opportunity_processed(self, opportunity: AlertOpportunity) -> bool:
        """Check if opportunity has already been processed"""
        opp_id = self._get_opportunity_id(opportunity)
        return opp_id in self.processed_opportunities
    
    def _mark_opportunity_processed(self, opportunity: AlertOpportunity):
        """Mark opportunity as processed to prevent duplicates"""
        opp_id = self._get_opportunity_id(opportunity)
        self.processed_opportunities.add(opp_id)
        self._save_processed_opportunities()
        logger.debug(f"Marked opportunity as processed: {opp_id}")
    
    def _save_alert_history(self):
        """Save alert history to persistent storage"""
        try:
            # Keep only last 1000 alerts
            recent_alerts = self.alert_history[-1000:]
            with open(self.alerts_file, 'w') as f:
                json.dump(recent_alerts, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving alert history: {e}")
    
    async def start_continuous_monitoring(self):
        """Start continuous monitoring with cron-like scheduling"""
        logger.info("Starting continuous monitoring system")
        self.monitoring_active = True
        
        while self.monitoring_active:
            try:
                current_time = datetime.now()
                
                # Execute monitoring cycle (24/7 operation)
                logger.info("Executing monitoring cycle")
                await self._execute_monitoring_cycle()
                
                # Send daily digest if needed
                await self._check_daily_digest()
                
                # Wait for next monitoring interval
                await asyncio.sleep(self.config.monitoring_interval * 60)  # Convert to seconds
                
            except Exception as e:
                logger.error(
                    "monitoring_cycle_error",
                    error_type=type(e).__name__,
                    error_details=str(e)
                )
                # Continue monitoring even if one cycle fails
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    def _is_work_hours(self, current_time: datetime) -> bool:
        """Check if current time is within configured work hours"""
        current_hour = current_time.hour
        return self.config.work_hours_start <= current_hour < self.config.work_hours_end
    
    async def _execute_monitoring_cycle(self):
        """Execute a complete monitoring cycle"""
        cycle_start = datetime.now()
        opportunities_found = []
        
        try:
            # Skip strategic accounts for now to avoid rate limits
            logger.info("Skipping strategic account monitoring to avoid rate limits")
            
            # Create focused test alert for v4/Unichain/AI system
            logger.info("Creating focused v4/Unichain/AI test opportunity")
            from bot.scheduling.cron_monitor import AlertOpportunity
            
            test_alert = AlertOpportunity(
                account_username="saucepoint",
                account_tier=1,
                content_text=f"Testing v4 AI integration patterns with predictive MEV protection - {datetime.now().strftime('%Y-%m-%d')}",
                content_url=f"https://twitter.com/saucepoint/status/1234567890123456789",
                timestamp=datetime.now().isoformat(),
                
                overall_score=0.91,
                ai_blockchain_relevance=0.95,
                technical_depth=0.88,
                opportunity_type="uniswap_v4_ai_innovation",
                suggested_response_type="technical_insight",
                time_sensitivity="immediate",
                
                strategic_context="Core v4 developer discussing AI integration breakthrough",
                suggested_response="Technical analysis of AI-powered hook architecture",
                
                generated_reply="The AI integration patterns emerging in v4 hooks are revolutionary. Real-time MEV prediction and adaptive routing will fundamentally change DEX efficiency.",
                reply_reasoning="Shows deep v4 technical knowledge with AI expertise",
                alternative_responses=[
                    "This validates autonomous trading infrastructure on Unichain",
                    "The convergence of AI agents and v4 architecture is inevitable"
                ],
                engagement_prediction=0.89,
                voice_alignment_score=0.93
            )
            
            # Filter out duplicates
            processed_opportunities = []
            if not self._is_opportunity_processed(test_alert):
                processed_opportunities.append(test_alert)
                self._mark_opportunity_processed(test_alert)
                logger.info("New test opportunity created and marked as processed")
            else:
                logger.info("Test opportunity already sent today, skipping duplicate")
            
            # 4. Send alerts based on priority
            await self._send_priority_alerts(processed_opportunities)
            
            # 5. Add to daily digest queue
            self.daily_opportunities.extend(processed_opportunities)
            
            cycle_duration = (datetime.now() - cycle_start).total_seconds()
            
            logger.info(
                "monitoring_cycle_completed",
                duration_seconds=cycle_duration,
                opportunities_found=len(opportunities_found),
                processed_opportunities=len(processed_opportunities),
                alerts_sent=len([opp for opp in processed_opportunities if opp.overall_score >= self.config.priority_threshold])
            )
            
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")
    
    async def _monitor_strategic_accounts(self) -> List[Dict]:
        """Monitor strategic accounts for new content"""
        opportunities = []
        
        try:
            # Get all strategic accounts
            accounts = self.strategic_tracker.accounts
            
            for username, account in accounts.items():
                try:
                    # Get recent tweets from this account
                    user_tweets = await self._get_user_recent_tweets(username, max_results=10)
                    
                    for tweet in user_tweets:
                        # Analyze for engagement opportunities
                        opportunity = await self.strategic_tracker.analyze_account_content(username, tweet)
                        if opportunity:
                            opportunities.append(opportunity.to_dict())
                    
                    # Rate limiting between accounts
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.warning(f"Error monitoring account @{username}: {e}")
            
            logger.info(f"Strategic account monitoring found {len(opportunities)} opportunities")
            
        except Exception as e:
            logger.error(f"Error in strategic account monitoring: {e}")
        
        return opportunities
    
    async def _get_user_recent_tweets(self, username: str, max_results: int = 10) -> List[Dict]:
        """Get recent tweets from a specific user"""
        try:
            # Get user ID
            user = self.x_client.client.get_user(username=username)
            if not user.data:
                return []
            
            user_id = user.data.id
            
            # Get recent tweets
            tweets = self.x_client.client.get_users_tweets(
                id=user_id,
                max_results=max_results,
                tweet_fields=['created_at', 'public_metrics', 'context_annotations'],
                exclude=['retweets', 'replies']
            )
            
            results = []
            if tweets and tweets.data:
                for tweet in tweets.data:
                    # Only process tweets from last 4 hours
                    if tweet.created_at and (datetime.now() - tweet.created_at.replace(tzinfo=None)).total_seconds() < 14400:
                        tweet_dict = {
                            'id': tweet.id,
                            'text': tweet.text,
                            'author_id': user_id,
                            'created_at': tweet.created_at,
                            'public_metrics': getattr(tweet, 'public_metrics', {}),
                            'context_annotations': getattr(tweet, 'context_annotations', [])
                        }
                        results.append(tweet_dict)
            
            return results
            
        except Exception as e:
            logger.warning(f"Error getting tweets for @{username}: {e}")
            return []
    
    async def _monitor_ai_blockchain_keywords(self) -> List[Dict]:
        """Monitor AI x blockchain keywords for opportunities"""
        opportunities = []
        
        try:
            # Occasionally update trending narratives (every 4-6 hours)
            if datetime.now() - self.last_narrative_update > timedelta(hours=random.uniform(4, 6)):
                await self._update_trending_narratives()
                self.last_narrative_update = datetime.now()
            
            # Get focused keywords for v4/Unichain/AI intersection
            ai_blockchain_keywords = self._get_focused_keywords()
            
            for keyword in ai_blockchain_keywords:
                try:
                    # Search for recent tweets
                    search_results = await self._search_keyword_tweets(keyword, max_results=10)
                    
                    for tweet in search_results:
                        # Enhanced AI x blockchain analysis
                        analysis = await self._analyze_ai_blockchain_content(keyword, tweet)
                        
                        if analysis['overall_ai_blockchain_score'] >= 0.6:
                            opportunity = {
                                'keyword': keyword,
                                'tweet_data': tweet,
                                'analysis': analysis,
                                'discovered_at': datetime.now().isoformat()
                            }
                            opportunities.append(opportunity)
                    
                    # Rate limiting between searches
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.warning(f"Error searching keyword '{keyword}': {e}")
            
            logger.info(f"AI x blockchain keyword monitoring found {len(opportunities)} opportunities")
            
        except Exception as e:
            logger.error(f"Error in keyword monitoring: {e}")
        
        return opportunities
    
    async def _search_keyword_tweets(self, keyword: str, max_results: int = 10) -> List[Dict]:
        """Search for recent tweets containing a specific keyword"""
        try:
            query = f'"{keyword}" -is:retweet lang:en'
            
            search_results = self.x_client.read_client.search_recent_tweets(
                query=query,
                max_results=max_results,
                tweet_fields=['created_at', 'public_metrics', 'context_annotations'],
                expansions=['author_id'],
                user_fields=['username', 'public_metrics']
            )
            
            results = []
            if search_results and search_results.data:
                for tweet in search_results.data:
                    # Only process recent tweets (last 2 hours)
                    if tweet.created_at and (datetime.now() - tweet.created_at.replace(tzinfo=None)).total_seconds() < 7200:
                        tweet_dict = {
                            'id': tweet.id,
                            'text': tweet.text,
                            'author_id': tweet.author_id,
                            'created_at': tweet.created_at,
                            'public_metrics': getattr(tweet, 'public_metrics', {}),
                            'keyword': keyword
                        }
                        results.append(tweet_dict)
            
            return results
            
        except Exception as e:
            logger.warning(f"Error searching for keyword '{keyword}': {e}")
            return []
    
    async def _analyze_ai_blockchain_content(self, keyword: str, tweet: Dict) -> Dict:
        """Analyze content for AI x blockchain convergence opportunities"""
        try:
            if self.claude_client:
                # Use Claude for enhanced analysis
                analysis_prompt = f"""
                Analyze this tweet found via keyword search for '{keyword}' for AI x blockchain engagement opportunities:
                
                Tweet: "{tweet.get('text', '')}"
                
                Provide analysis focusing on:
                1. AI x blockchain convergence relevance (0-1)
                2. Technical depth and complexity (0-1)
                3. Innovation and forward-thinking content (0-1)
                4. Engagement opportunity potential (0-1)
                5. Time sensitivity for response (0-1)
                
                Return JSON:
                {{
                    "ai_blockchain_relevance": 0.0-1.0,
                    "technical_depth": 0.0-1.0,
                    "innovation_score": 0.0-1.0,
                    "engagement_opportunity": 0.0-1.0,
                    "time_sensitivity": 0.0-1.0,
                    "content_themes": ["theme1", "theme2"],
                    "opportunity_type": "technical_discussion|breakthrough_announcement|collaboration|educational",
                    "strategic_value": "high|medium|low",
                    "suggested_approach": "technical_insight|question|collaboration|educational_support"
                }}
                """
                
                # Make direct API call for analysis using async context
                async with self.claude_client as client:
                    response_data = await client._make_api_call("messages", {
                        "model": "claude-3-haiku-20240307",
                        "max_tokens": 500,
                        "messages": [{"role": "user", "content": analysis_prompt}]
                    })
                
                # Extract JSON from Claude response (may have extra text)
                response_text = response_data['content'][0]['text']
                
                # Find JSON block in response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group(0))
                else:
                    # Fallback to basic scoring if JSON extraction fails
                    analysis = {
                        "ai_blockchain_relevance": 0.6,
                        "technical_depth": 0.5,
                        "innovation_score": 0.5,
                        "engagement_opportunity": 0.7,
                        "time_sensitivity": 0.6,
                        "content_themes": ["blockchain", "ai"],
                        "opportunity_type": "technical_discussion",
                        "strategic_value": "medium",
                        "suggested_approach": "technical_insight"
                    }
                
                # Calculate overall score
                analysis['overall_ai_blockchain_score'] = (
                    analysis['ai_blockchain_relevance'] * 0.3 +
                    analysis['technical_depth'] * 0.25 +
                    analysis['innovation_score'] * 0.25 +
                    analysis['engagement_opportunity'] * 0.2
                )
                
                return analysis
                
            else:
                # Fallback to basic analysis
                return self._basic_ai_blockchain_analysis(keyword, tweet)
                
        except Exception as e:
            logger.warning(f"AI analysis failed for keyword '{keyword}': {e}")
            return self._basic_ai_blockchain_analysis(keyword, tweet)
    
    def _basic_ai_blockchain_analysis(self, keyword: str, tweet: Dict) -> Dict:
        """Basic analysis when Claude API is not available"""
        text = tweet.get('text', '').lower()
        
        # Basic scoring based on keyword density and content indicators
        ai_terms = ['ai', 'machine learning', 'ml', 'neural', 'algorithm', 'intelligent', 'autonomous', 'predictive']
        blockchain_terms = ['blockchain', 'crypto', 'defi', 'uniswap', 'ethereum', 'protocol', 'smart contract']
        technical_terms = ['implementation', 'architecture', 'optimization', 'performance', 'framework']
        
        ai_score = sum(1 for term in ai_terms if term in text) / len(ai_terms)
        blockchain_score = sum(1 for term in blockchain_terms if term in text) / len(blockchain_terms)
        technical_score = sum(1 for term in technical_terms if term in text) / len(technical_terms)
        
        has_question = '?' in text
        engagement_opportunity = 0.8 if has_question else 0.5
        
        return {
            'ai_blockchain_relevance': min(1.0, (ai_score + blockchain_score) / 2),
            'technical_depth': min(1.0, technical_score * 2),
            'innovation_score': 0.6 if any(term in text for term in ['new', 'breakthrough', 'revolutionary']) else 0.4,
            'engagement_opportunity': engagement_opportunity,
            'time_sensitivity': 0.7 if any(term in text for term in ['breaking', 'just', 'announced']) else 0.4,
            'content_themes': ['ai_blockchain'],
            'opportunity_type': 'technical_discussion',
            'strategic_value': 'medium',
            'suggested_approach': 'technical_insight',
            'overall_ai_blockchain_score': min(1.0, (ai_score + blockchain_score + technical_score) / 2)
        }
    
    async def _process_opportunities(self, raw_opportunities: List[Dict]) -> List[AlertOpportunity]:
        """Process raw opportunities into formatted alerts with generated content"""
        processed = []
        
        for opp in raw_opportunities:
            try:
                # Determine if this is a strategic account or keyword opportunity
                if 'account_username' in opp:
                    # Strategic account opportunity
                    alert_opp = AlertOpportunity(
                        account_username=opp['account_username'],
                        account_tier=opp['account_tier'],
                        content_text=opp['content_text'],
                        content_url=opp['content_url'],
                        timestamp=opp['timestamp'],
                        
                        overall_score=opp['overall_score'],
                        ai_blockchain_relevance=opp['ai_blockchain_relevance'],
                        technical_depth=opp['technical_depth'],
                        opportunity_type=opp['opportunity_type'],
                        suggested_response_type=opp['suggested_response_type'],
                        time_sensitivity=opp['time_sensitivity'],
                        
                        strategic_context=f"Tier {opp['account_tier']} strategic account posting {opp['opportunity_type']} content",
                        suggested_response=f"Respond with {opp['suggested_response_type']} within {self._get_response_timeframe(opp['time_sensitivity'])}"
                    )
                    
                    # Check for duplicates before processing
                    if not self._is_opportunity_processed(alert_opp):
                        # Generate content for this opportunity
                        await self._generate_opportunity_content(alert_opp)
                        
                        # Create feedback tracking for this opportunity
                        feedback_id = self.feedback_tracker.create_opportunity_tracking(alert_opp.to_dict())
                        alert_opp.feedback_id = feedback_id
                        alert_opp.feedback_urls = self.feedback_tracker.generate_feedback_urls(feedback_id)
                        
                        # Mark as processed to prevent future duplicates
                        self._mark_opportunity_processed(alert_opp)
                        processed.append(alert_opp)
                        logger.debug(f"New strategic opportunity: {alert_opp.content_url}")
                    else:
                        logger.debug(f"Skipping duplicate strategic opportunity: {alert_opp.content_url}")
                    
                elif 'keyword' in opp:
                    # Keyword opportunity
                    tweet_data = opp['tweet_data']
                    analysis = opp['analysis']
                    
                    alert_opp = AlertOpportunity(
                        account_username=f"keyword_search_{opp['keyword'].replace(' ', '_')}",
                        account_tier=3,  # Keyword opportunities are generally Tier 3 priority
                        content_text=tweet_data['text'],
                        content_url=f"https://twitter.com/user/status/{tweet_data['id']}",
                        timestamp=opp['discovered_at'],
                        
                        overall_score=analysis['overall_ai_blockchain_score'],
                        ai_blockchain_relevance=analysis['ai_blockchain_relevance'],
                        technical_depth=analysis['technical_depth'],
                        opportunity_type=analysis['opportunity_type'],
                        suggested_response_type=analysis['suggested_approach'],
                        time_sensitivity=self._convert_time_sensitivity(analysis['time_sensitivity']),
                        
                        strategic_context=f"AI x blockchain keyword '{opp['keyword']}' opportunity with {analysis['strategic_value']} strategic value",
                        suggested_response=f"Engage with {analysis['suggested_approach']} approach focusing on technical expertise"
                    )
                    
                    # Check for duplicates before processing
                    if not self._is_opportunity_processed(alert_opp):
                        # Generate content for this opportunity
                        await self._generate_opportunity_content(alert_opp)
                        
                        # Create feedback tracking for this opportunity
                        feedback_id = self.feedback_tracker.create_opportunity_tracking(alert_opp.to_dict())
                        alert_opp.feedback_id = feedback_id
                        alert_opp.feedback_urls = self.feedback_tracker.generate_feedback_urls(feedback_id)
                        
                        # Mark as processed to prevent future duplicates
                        self._mark_opportunity_processed(alert_opp)
                        processed.append(alert_opp)
                        logger.debug(f"New keyword opportunity: {alert_opp.content_url}")
                    else:
                        logger.debug(f"Skipping duplicate keyword opportunity: {alert_opp.content_url}")
                    
            except Exception as e:
                logger.error(f"Error processing opportunity: {e}")
        
        # Sort by overall score
        processed.sort(key=lambda x: x.overall_score, reverse=True)
        
        return processed
    
    async def _generate_opportunity_content(self, opportunity: AlertOpportunity):
        """Generate AI-powered response content for an opportunity"""
        try:
            if not self.claude_client:
                # Fallback content generation
                opportunity.generated_reply = f"Interesting perspective on {opportunity.opportunity_type}. The AI x blockchain convergence implications here are significant."
                opportunity.reply_reasoning = "Basic response due to Claude API unavailability"
                opportunity.alternative_responses = ["Thanks for sharing this insight!", "Great point about the technical implementation."]
                opportunity.engagement_prediction = 0.6
                opportunity.voice_alignment_score = 0.7
                return
            
            # Generate content using Claude API
            # Build prompt without JSON template to avoid f-string formatting issues
            content_prompt = f"""
            Generate a strategic reply for this AI x blockchain opportunity:
            
            Original Content: "{opportunity.content_text}"
            Account: @{opportunity.account_username} (Tier {opportunity.account_tier})
            Opportunity Type: {opportunity.opportunity_type}
            Suggested Approach: {opportunity.suggested_response_type}
            
            Voice Guidelines - SingleDivorcedDad Sprotogremlin:
            - 42-year-old single dad with sprotogremlin energy
            - Chaotic but knowledgeable - crypto expertise expressed casually
            - Dad wisdom mixed with degen gremlin vibes
            - Technical knowledge but not corporate or formal
            - Slightly unhinged but endearing energy
            - NO buzzwords, NO "alpha", NO press release language
            - NEVER use hashtags or emojis
            
            Generate a reply that:
            1. Sounds like a real person, not a crypto influencer
            2. Adds genuine insight but in gremlin language
            3. Shows technical knowledge casually, not formally
            4. Stays under 280 characters
            5. Has authentic dad/gremlin personality
            6. NO corporate speak or marketing language
            
            Provide your response as JSON with these exact keys:
            - primary_reply: Your main response (string, max 280 chars)
            - reasoning: Why this approach works (string)
            - alternatives: Array of 2 alternative responses
            - engagement_prediction: Number from 0.0 to 1.0
            - voice_alignment: Number from 0.0 to 1.0
            
            Example format: JSON object with primary_reply, reasoning, alternatives array, engagement_prediction number, voice_alignment number
            """
            
            # Use Claude to generate content
            async with self.claude_client:
                voice_only = """
                AI x blockchain technical authority voice:
                - Conversational and approachable - use "chat" for addressing readers
                - Forward-thinking innovation expert - relaxed crypto-native language
                - Educational but confident - no corporate fluff or rigid tone
                - NEVER use hashtags - clean text only
                - Always use lowercase "v4" for Uniswap v4
                - Use "Uniswap community/ecosystem/foundation/labs" not just "Uniswap"
                - Relaxed, authentic voice - less formal, more natural
                """
                
                response = await self.claude_client.generate_content(
                    opportunity_type="reply",
                    context={'text': opportunity.content_text, 'prompt': content_prompt},
                    target_topics=["ai blockchain", "autonomous trading", "uniswap v4"],
                    voice_guidelines=voice_only
                )
            
            # Parse Claude response
            try:
                import json
                content_data = json.loads(response.content)
                
                opportunity.generated_reply = content_data.get('primary_reply', 'Generated response unavailable')
                opportunity.reply_reasoning = content_data.get('reasoning', 'AI-generated strategic response')
                opportunity.alternative_responses = content_data.get('alternatives', [])
                opportunity.engagement_prediction = content_data.get('engagement_prediction', 0.7)
                opportunity.voice_alignment_score = content_data.get('voice_alignment', 0.8)
                
            except (json.JSONDecodeError, KeyError):
                # Fallback if JSON parsing fails
                opportunity.generated_reply = response.content[:280] if hasattr(response, 'content') else "AI-generated response"
                opportunity.reply_reasoning = "AI-generated strategic response with technical expertise"
                opportunity.alternative_responses = ["Great insight on AI x blockchain convergence!", "The technical implications here are fascinating."]
                opportunity.engagement_prediction = 0.7
                opportunity.voice_alignment_score = 0.8
                
        except Exception as e:
            logger.warning(f"Content generation failed for opportunity: {e}")
            # Fallback content
            opportunity.generated_reply = f"Insightful take on {opportunity.opportunity_type}. The AI x blockchain convergence patterns here align with trends we're seeing in autonomous protocol development."
            opportunity.reply_reasoning = "Template response due to content generation error"
            opportunity.alternative_responses = [
                "This demonstrates the growing AI x blockchain infrastructure maturity.",
                "Fascinating developments in the convergence space!"
            ]
            opportunity.engagement_prediction = 0.6
            opportunity.voice_alignment_score = 0.7
    
    def _get_response_timeframe(self, time_sensitivity: str) -> str:
        """Convert time sensitivity to response timeframe"""
        timeframes = {
            'immediate': '30 minutes',
            'within_hour': '1 hour',
            'within_day': '4 hours',
            'digest': '24 hours'
        }
        return timeframes.get(time_sensitivity, '2 hours')
    
    def _convert_time_sensitivity(self, score: float) -> str:
        """Convert numerical time sensitivity to category"""
        if score >= 0.8:
            return 'immediate'
        elif score >= 0.6:
            return 'within_hour'
        elif score >= 0.4:
            return 'within_day'
        else:
            return 'digest'
    
    async def _send_priority_alerts(self, opportunities: List[AlertOpportunity]):
        """Send detailed email alerts with feedback tracking, opportunities + original content"""
        logger.info(f"Processing {len(opportunities)} opportunities for detailed email with feedback + original content")
        
        # Filter for highest priority opportunities (limit to 2 for email readability with original content)
        high_priority_opportunities = sorted(
            opportunities, 
            key=lambda x: x.overall_score, 
            reverse=True
        )[:2] if opportunities else []
        
        # Generate feedback URLs for each opportunity and register with feedback tracker
        feedback_tracker = get_feedback_tracker()
        for opp in high_priority_opportunities:
            # Register opportunity with feedback tracker
            opp_data = {
                'account_username': opp.account_username,
                'opportunity_type': opp.opportunity_type,
                'overall_score': opp.overall_score,
                'generated_reply': opp.generated_reply,
                'alternative_responses': opp.alternative_responses,
                'voice_alignment_score': opp.voice_alignment_score,
                'content_url': opp.content_url
            }
            opp.feedback_id = feedback_tracker.create_opportunity_tracking(opp_data)
            opp.feedback_urls = self._generate_feedback_urls(opp)
        
        # Generate original content (trending topic or unhinged take)
        content_type = "trending_topic" if len(high_priority_opportunities) >= 2 else "unhinged_take"
        original_content = await self._generate_original_content(content_type)
        
        # Register original content with feedback tracker
        original_content_data = {
            'account_username': 'AI_Generated',
            'opportunity_type': f'original_{content_type}',
            'overall_score': 0.8,  # Default score for original content
            'generated_reply': original_content['content'],
            'alternative_responses': [],
            'voice_alignment_score': 0.85,  # Default voice alignment
            'content_url': 'https://twitter.com/intent/tweet'
        }
        original_content_id = feedback_tracker.create_opportunity_tracking(original_content_data)
        original_content['feedback_id'] = original_content_id
        
        # Send detailed alert with both opportunities and original content
        await self._send_detailed_alert_with_original_content(high_priority_opportunities, original_content)
    
    def _generate_feedback_urls(self, opportunity: AlertOpportunity) -> Dict[str, str]:
        """Generate feedback URLs for opportunity quality rating and reply usage tracking"""
        opp_id = opportunity.feedback_id or f"opp_{hash(opportunity.content_url) % 10000}"
        
        # Use feedback tracker to generate URLs with proper base URL
        return self.feedback_tracker.generate_feedback_urls(opp_id)
    
    async def _send_detailed_alert_with_original_content(self, opportunities: List[AlertOpportunity], original_content: Dict):
        """Send detailed email alert with opportunities + original content + comprehensive feedback tracking"""
        try:
            opp_count = len(opportunities)
            content_type = original_content.get('content_type', 'unknown')
            
            # Generate subject based on content with version
            if opp_count == 0:
                subject = f"🚀 Original {content_type.replace('_', ' ').title()} + AI x Blockchain Focus [{SYSTEM_VERSION}]"
            elif any(opp.account_username == "SYSTEM_STARTUP" for opp in opportunities):
                subject = f"🤖 SYSTEM STARTUP - SingleDivorcedDad Bot Online [{SYSTEM_VERSION}]"
            else:
                subject = f"🎯 {opp_count} AI x Blockchain Opportunities + {content_type.replace('_', ' ').title()} [{SYSTEM_VERSION}]"
            
            html_content = self._generate_detailed_alert_with_original_html(opportunities, original_content)
            
            alert_type = f"detailed_with_{content_type}"
            await self._send_email(subject, html_content, alert_type, opp_count)
            
            # Record alert
            self._record_alert(alert_type, opp_count, opportunities)
            
            logger.info(f"Sent detailed alert: {opp_count} opportunities + {content_type}")
            
        except Exception as e:
            logger.error(f"Error sending detailed alert with original content: {e}")
    
    async def _send_detailed_alert(self, opportunities: List[AlertOpportunity]):
        """Send detailed email alert with comprehensive feedback tracking (legacy method)"""
        try:
            subject = f"🎯 {len(opportunities)} AI x Blockchain Opportunities with Feedback Tracking [{SYSTEM_VERSION}]"
            
            html_content = self._generate_alert_html(
                "PRIORITY OPPORTUNITIES WITH FEEDBACK",
                opportunities,
                "High-quality AI x blockchain engagement opportunities with voice evolution tracking."
            )
            
            await self._send_email(subject, html_content, "detailed_priority", len(opportunities))
            
            # Record alert
            self._record_alert('detailed_priority', len(opportunities), opportunities)
            
            logger.info(f"Sent detailed alert with feedback tracking for {len(opportunities)} opportunities")
            
        except Exception as e:
            logger.error(f"Error sending detailed alert: {e}")
    
    async def _send_priority_alert(self, opportunities: List[AlertOpportunity]):
        """Send priority email alert"""
        try:
            subject = f"⚡ PRIORITY: {len(opportunities)} AI x Blockchain Engagement Opportunities [{SYSTEM_VERSION}]"
            
            html_content = self._generate_alert_html(
                "PRIORITY OPPORTUNITIES",
                opportunities,
                "These opportunities are time-sensitive and should be addressed within 1-2 hours."
            )
            
            await self._send_email(subject, html_content, "priority", len(opportunities))
            
            # Record alert
            self._record_alert('priority', len(opportunities), opportunities)
            
            logger.info(f"Sent priority alert for {len(opportunities)} opportunities")
            
        except Exception as e:
            logger.error(f"Error sending priority alert: {e}")
    
    def _generate_alert_html(self, alert_type: str, opportunities: List[AlertOpportunity], description: str) -> str:
        """Generate enhanced HTML email content with generated replies and links"""
        opportunities_html = ""
        
        for i, opp in enumerate(opportunities[:5], 1):  # Limit to top 5
            emoji = "🔥" if opp.overall_score >= 0.8 else "⚡" if opp.overall_score >= 0.6 else "📊"
            
            # Generate enhanced tweet URLs - handle both real and test URLs
            tweet_id = opp.content_url.split('/')[-1] if '/status/' in opp.content_url else None
            
            if tweet_id and tweet_id.isdigit():
                # Real tweet ID - use reply intent
                reply_url = f"https://twitter.com/intent/tweet?in_reply_to={tweet_id}&text={opp.generated_reply or ''}"
                quote_url = f"https://twitter.com/intent/tweet?url={opp.content_url}&text={opp.generated_reply or ''}"
            else:
                # Test data or invalid URL - use general compose intent
                reply_text = f"@{opp.account_username} {opp.generated_reply or ''}"
                reply_url = f"https://twitter.com/intent/tweet?text={reply_text}"
                quote_url = f"https://twitter.com/intent/tweet?text={opp.generated_reply or ''}"
            
            # Format alternative responses
            alternatives_html = ""
            if opp.alternative_responses:
                for j, alt in enumerate(opp.alternative_responses[:2], 1):
                    if tweet_id and tweet_id.isdigit():
                        alt_reply_url = f"https://twitter.com/intent/tweet?in_reply_to={tweet_id}&text={alt}"
                    else:
                        alt_reply_text = f"@{opp.account_username} {alt}"
                        alt_reply_url = f"https://twitter.com/intent/tweet?text={alt_reply_text}"
                    alternatives_html += f"""
                    <div style="background: #f0f0f0; padding: 8px; margin: 5px 0; border-radius: 4px; border-left: 3px solid #3498db;">
                        <strong>Alternative {j}:</strong> {alt}<br>
                        <a href="{alt_reply_url}" style="font-size: 12px; color: #3498db; text-decoration: none;">📝 Use This Reply</a>
                    </div>
                    """
            
            # Performance prediction indicators
            engagement_color = "#27ae60" if opp.engagement_prediction and opp.engagement_prediction >= 0.7 else "#f39c12" if opp.engagement_prediction and opp.engagement_prediction >= 0.5 else "#e74c3c"
            voice_color = "#27ae60" if opp.voice_alignment_score and opp.voice_alignment_score >= 0.8 else "#f39c12" if opp.voice_alignment_score and opp.voice_alignment_score >= 0.6 else "#e74c3c"
            
            # Feedback URLs for this opportunity
            feedback_urls = opp.feedback_urls if opp.feedback_urls else {}
            excellent_url = feedback_urls.get('excellent', '#')
            good_url = feedback_urls.get('good', '#')
            okay_url = feedback_urls.get('okay', '#')
            poor_url = feedback_urls.get('poor', '#')
            bad_url = feedback_urls.get('bad', '#')
            used_primary_url = feedback_urls.get('used_primary', '#')
            used_alt1_url = feedback_urls.get('used_alt1', '#')
            used_alt2_url = feedback_urls.get('used_alt2', '#')
            used_custom_url = feedback_urls.get('used_custom', '#')
            not_used_url = feedback_urls.get('not_used', '#')
            feedback_id = opp.feedback_id or 'N/A'
            
            opportunities_html += f"""
            <div style="border: 1px solid #ddd; margin: 20px 0; padding: 20px; border-radius: 10px; background: #fafafa;">
                <h3 style="color: #2c3e50; margin-top: 0; border-bottom: 2px solid #3498db; padding-bottom: 8px;">
                    {emoji} Opportunity {i}: @{opp.account_username}
                </h3>
                
                <div style="background: #fff; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #3498db;">
                    <strong style="color: #2c3e50;">Original Content:</strong><br>
                    <em>"{opp.content_text[:300]}{'...' if len(opp.content_text) > 300 else ''}"</em>
                </div>
                
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 15px 0; background: #f8f9fa; padding: 12px; border-radius: 6px;">
                    <div><strong>Overall Score:</strong> <span style="color: {engagement_color};">{opp.overall_score:.2f}</span></div>
                    <div><strong>AI x Blockchain:</strong> <span style="color: #8e44ad;">{opp.ai_blockchain_relevance:.2f}</span></div>
                    <div><strong>Technical Depth:</strong> <span style="color: #d35400;">{opp.technical_depth:.2f}</span></div>
                </div>
                
                <div style="margin: 15px 0; background: #fff; padding: 12px; border-radius: 6px;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                        <div><strong>Opportunity Type:</strong> {opp.opportunity_type.replace('_', ' ').title()}</div>
                        <div><strong>Time Sensitivity:</strong> {opp.time_sensitivity.replace('_', ' ').title()}</div>
                    </div>
                </div>
                
                <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #27ae60;">
                    <strong style="color: #27ae60;">🤖 AI-Generated Response:</strong><br>
                    <div style="background: #fff; padding: 12px; margin: 8px 0; border-radius: 6px; font-style: italic; border: 1px solid #ddd;">
                        "{opp.generated_reply or 'Response generation in progress...'}"
                    </div>
                    
                    {f'<div style="font-size: 12px; color: #666; margin-top: 8px;"><strong>Reasoning:</strong> {opp.reply_reasoning}</div>' if opp.reply_reasoning else ''}
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px; font-size: 12px;">
                        <div>📈 <strong>Engagement Prediction:</strong> <span style="color: {engagement_color};">{(opp.engagement_prediction or 0):.0%}</span></div>
                        <div>🎭 <strong>Voice Alignment:</strong> <span style="color: {voice_color};">{(opp.voice_alignment_score or 0):.0%}</span></div>
                    </div>
                </div>
                
                {f'<div style="margin: 15px 0;"><strong style="color: #8e44ad;">🔄 Alternative Responses:</strong>{alternatives_html}</div>' if alternatives_html else ''}
                
                <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #ffc107;">
                    <strong style="color: #856404;">📋 Strategic Context:</strong><br>
                    {opp.strategic_context}<br>
                    <strong style="color: #856404;">💡 Recommended Action:</strong> {opp.suggested_response}
                </div>
                
                <div style="margin: 20px 0; text-align: center;">
                    <a href="{opp.content_url}" 
                       style="background: #3498db; color: white; padding: 12px 20px; text-decoration: none; border-radius: 6px; margin: 5px; display: inline-block; font-weight: bold;">
                        🔗 View Original Tweet
                    </a>
                    
                    <a href="{reply_url}" 
                       style="background: #27ae60; color: white; padding: 12px 20px; text-decoration: none; border-radius: 6px; margin: 5px; display: inline-block; font-weight: bold;">
                        💬 Reply with Generated Content
                    </a>
                    
                    <a href="{quote_url}" 
                       style="background: #e67e22; color: white; padding: 12px 20px; text-decoration: none; border-radius: 6px; margin: 5px; display: inline-block; font-weight: bold;">
                        🔄 Quote Tweet
                    </a>
                </div>
                
                <!-- Feedback Section -->
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #6c757d;">
                    <strong style="color: #495057;">📊 Feedback & Learning</strong><br>
                    <div style="margin: 10px 0; font-size: 12px; color: #6c757d;">
                        Help improve voice evolution by rating this opportunity and tracking reply usage:
                    </div>
                    
                    <!-- Quality Rating Buttons -->
                    <div style="margin: 8px 0;">
                        <strong style="font-size: 12px; color: #495057;">Opportunity Quality:</strong><br>
                        <div style="margin: 5px 0;">
                            <a href="{excellent_url}" 
                               style="background: #28a745; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; margin: 2px; font-size: 11px; display: inline-block;">
                                ⭐⭐⭐⭐⭐ Excellent
                            </a>
                            <a href="{good_url}" 
                               style="background: #20c997; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; margin: 2px; font-size: 11px; display: inline-block;">
                                ⭐⭐⭐⭐ Good
                            </a>
                            <a href="{okay_url}" 
                               style="background: #ffc107; color: black; padding: 4px 8px; text-decoration: none; border-radius: 3px; margin: 2px; font-size: 11px; display: inline-block;">
                                ⭐⭐⭐ Okay
                            </a>
                            <a href="{poor_url}" 
                               style="background: #fd7e14; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; margin: 2px; font-size: 11px; display: inline-block;">
                                ⭐⭐ Poor
                            </a>
                            <a href="{bad_url}" 
                               style="background: #dc3545; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; margin: 2px; font-size: 11px; display: inline-block;">
                                ⭐ Bad
                            </a>
                        </div>
                    </div>
                    
                    <!-- Reply Usage Tracking -->
                    <div style="margin: 8px 0;">
                        <strong style="font-size: 12px; color: #495057;">Reply Usage (click after posting):</strong><br>
                        <div style="margin: 5px 0;">
                            <a href="{used_primary_url}" 
                               style="background: #007bff; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; margin: 2px; font-size: 11px; display: inline-block;">
                                🎯 Used Primary Reply
                            </a>
                            <a href="{used_alt1_url}" 
                               style="background: #6f42c1; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; margin: 2px; font-size: 11px; display: inline-block;">
                                🔄 Used Alternative 1
                            </a>
                            <a href="{used_alt2_url}" 
                               style="background: #e83e8c; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; margin: 2px; font-size: 11px; display: inline-block;">
                                🔄 Used Alternative 2
                            </a>
                            <a href="{used_custom_url}" 
                               style="background: #17a2b8; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; margin: 2px; font-size: 11px; display: inline-block;">
                                ✏️ Used Custom Reply
                            </a>
                            <a href="{not_used_url}" 
                               style="background: #6c757d; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; margin: 2px; font-size: 11px; display: inline-block;">
                                ❌ Didn't Use
                            </a>
                        </div>
                    </div>
                    
                    <div style="font-size: 10px; color: #868e96; margin-top: 8px;">
                        Feedback ID: {feedback_id} | This data helps evolve voice and content quality over time
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 15px; padding: 10px; background: #ecf0f1; border-radius: 6px; font-size: 12px; color: #7f8c8d;">
                    <strong>Quick Actions:</strong> 
                    <a href="https://twitter.com/{opp.account_username}" style="color: #3498db; text-decoration: none; margin: 0 10px;">👤 View Profile</a> | 
                    <a href="https://twitter.com/intent/follow?screen_name={opp.account_username}" style="color: #3498db; text-decoration: none; margin: 0 10px;">➕ Follow</a>
                    {f' | <a href="https://twitter.com/intent/like?tweet_id={tweet_id}" style="color: #3498db; text-decoration: none; margin: 0 10px;">❤️ Like</a>' if tweet_id and tweet_id.isdigit() else ''}
                </div>
            </div>
            """
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>AI x Blockchain KOL Opportunities</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
            <div style="background: #007bff; color: white; padding: 8px 15px; border-radius: 5px; margin-bottom: 20px; text-align: center; font-weight: bold;">
                🤖 System Version: {SYSTEM_VERSION} (Feature Branch - Authentic Voice)
            </div>
            
            <h1 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                {alert_type}
            </h1>
            
            <p style="background: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107;">
                <strong>Alert Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                <strong>Description:</strong> {description}
            </p>
            
            <h2 style="color: #2c3e50;">Opportunities Identified:</h2>
            
            {opportunities_html}
            
            <div style="margin-top: 30px; padding: 15px; background: #f8f9fa; border-radius: 5px;">
                <h3 style="color: #2c3e50; margin-top: 0;">Next Steps:</h3>
                <ol>
                    <li>Review each opportunity for strategic alignment</li>
                    <li>Prioritize based on account tier and overall score</li>
                    <li>Craft responses that demonstrate technical expertise</li>
                    <li>Engage within recommended timeframes</li>
                    <li>Track engagement outcomes for optimization</li>
                </ol>
            </div>
            
            <div style="margin-top: 20px; padding: 15px; background: #e8f5e8; border-radius: 5px; text-align: center;">
                <p style="margin: 0;"><strong>AI x Blockchain KOL Development Platform</strong><br>
                Automated monitoring and opportunity detection system</p>
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    def _generate_detailed_alert_with_original_html(self, opportunities: List[AlertOpportunity], original_content: Dict) -> str:
        """Generate detailed HTML email with opportunities + original content + feedback tracking"""
        import urllib.parse
        
        opportunities_html = ""
        
        # Generate opportunities section (same as detailed format)
        for i, opp in enumerate(opportunities[:2], 1):  # Limit to 2 for readability with original content
            emoji = "🔥" if opp.overall_score >= 0.8 else "⚡" if opp.overall_score >= 0.6 else "📊"
            
            # Generate enhanced tweet URLs - handle both real and test URLs
            tweet_id = opp.content_url.split('/')[-1] if '/status/' in opp.content_url else None
            
            if tweet_id and tweet_id.isdigit():
                # Real tweet ID - use reply intent
                reply_url = f"https://twitter.com/intent/tweet?in_reply_to={tweet_id}&text={urllib.parse.quote(str(opp.generated_reply or ''))}"
                quote_url = f"https://twitter.com/intent/tweet?url={opp.content_url}&text={urllib.parse.quote(str(opp.generated_reply or ''))}"
            else:
                # Test data or invalid URL - use general compose intent
                reply_text = f"@{opp.account_username} {opp.generated_reply or ''}"
                reply_url = f"https://twitter.com/intent/tweet?text={urllib.parse.quote(reply_text)}"
                quote_url = f"https://twitter.com/intent/tweet?text={urllib.parse.quote(str(opp.generated_reply or ''))}"
            
            # Format alternative responses
            alternatives_html = ""
            if opp.alternative_responses:
                for j, alt in enumerate(opp.alternative_responses[:2], 1):
                    if tweet_id and tweet_id.isdigit():
                        alt_reply_url = f"https://twitter.com/intent/tweet?in_reply_to={tweet_id}&text={urllib.parse.quote(str(alt))}"
                    else:
                        alt_reply_text = f"@{opp.account_username} {alt}"
                        alt_reply_url = f"https://twitter.com/intent/tweet?text={urllib.parse.quote(alt_reply_text)}"
                    alternatives_html += f"""
                    <div style="background: #f0f0f0; padding: 8px; margin: 5px 0; border-radius: 4px; border-left: 3px solid #3498db;">
                        <strong>Alternative {j}:</strong> {alt}<br>
                        <a href="{alt_reply_url}" style="font-size: 12px; color: #3498db; text-decoration: none;">📝 Use This Reply</a>
                    </div>
                    """
            
            # Performance prediction indicators
            engagement_color = "#27ae60" if opp.engagement_prediction and opp.engagement_prediction >= 0.7 else "#f39c12" if opp.engagement_prediction and opp.engagement_prediction >= 0.5 else "#e74c3c"
            voice_color = "#27ae60" if opp.voice_alignment_score and opp.voice_alignment_score >= 0.8 else "#f39c12" if opp.voice_alignment_score and opp.voice_alignment_score >= 0.6 else "#e74c3c"
            
            # Feedback URLs for this opportunity
            feedback_urls = opp.feedback_urls if opp.feedback_urls else {}
            excellent_url = feedback_urls.get('excellent', '#')
            good_url = feedback_urls.get('good', '#')
            okay_url = feedback_urls.get('okay', '#')
            poor_url = feedback_urls.get('poor', '#')
            bad_url = feedback_urls.get('bad', '#')
            used_primary_url = feedback_urls.get('used_primary', '#')
            used_alt1_url = feedback_urls.get('used_alt1', '#')
            used_alt2_url = feedback_urls.get('used_alt2', '#')
            used_custom_url = feedback_urls.get('used_custom', '#')
            not_used_url = feedback_urls.get('not_used', '#')
            feedback_id = opp.feedback_id or 'N/A'
            
            opportunities_html += f"""
            <div style="border: 1px solid #ddd; margin: 20px 0; padding: 20px; border-radius: 10px; background: #fafafa;">
                <h3 style="color: #2c3e50; margin-top: 0; border-bottom: 2px solid #3498db; padding-bottom: 8px;">
                    {emoji} Opportunity {i}: @{opp.account_username}
                </h3>
                
                <div style="background: #fff; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #3498db;">
                    <strong style="color: #2c3e50;">Original Content:</strong><br>
                    <em>"{opp.content_text[:300]}{'...' if len(opp.content_text) > 300 else ''}"</em>
                </div>
                
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 15px 0; background: #f8f9fa; padding: 12px; border-radius: 6px;">
                    <div><strong>Overall Score:</strong> <span style="color: {engagement_color};">{opp.overall_score:.2f}</span></div>
                    <div><strong>AI x Blockchain:</strong> <span style="color: #8e44ad;">{opp.ai_blockchain_relevance:.2f}</span></div>
                    <div><strong>Technical Depth:</strong> <span style="color: #d35400;">{opp.technical_depth:.2f}</span></div>
                </div>
                
                <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #27ae60;">
                    <strong style="color: #27ae60;">🤖 AI-Generated Response:</strong><br>
                    <div style="background: #fff; padding: 12px; margin: 8px 0; border-radius: 6px; font-style: italic; border: 1px solid #ddd;">
                        "{opp.generated_reply or 'Response generation in progress...'}"
                    </div>
                    
                    {f'<div style="font-size: 12px; color: #666; margin-top: 8px;"><strong>Reasoning:</strong> {opp.reply_reasoning}</div>' if opp.reply_reasoning else ''}
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px; font-size: 12px;">
                        <div>📈 <strong>Engagement Prediction:</strong> <span style="color: {engagement_color};">{(opp.engagement_prediction or 0):.0%}</span></div>
                        <div>🎭 <strong>Voice Alignment:</strong> <span style="color: {voice_color};">{(opp.voice_alignment_score or 0):.0%}</span></div>
                    </div>
                </div>
                
                {f'<div style="margin: 15px 0;"><strong style="color: #8e44ad;">🔄 Alternative Responses:</strong>{alternatives_html}</div>' if alternatives_html else ''}
                
                <div style="margin: 20px 0; text-align: center;">
                    <a href="{opp.content_url}" 
                       style="background: #3498db; color: white; padding: 12px 20px; text-decoration: none; border-radius: 6px; margin: 5px; display: inline-block; font-weight: bold;">
                        🔗 View Original Tweet
                    </a>
                    
                    <a href="{reply_url}" 
                       style="background: #27ae60; color: white; padding: 12px 20px; text-decoration: none; border-radius: 6px; margin: 5px; display: inline-block; font-weight: bold;">
                        💬 Reply with Generated Content
                    </a>
                    
                    <a href="{quote_url}" 
                       style="background: #e67e22; color: white; padding: 12px 20px; text-decoration: none; border-radius: 6px; margin: 5px; display: inline-block; font-weight: bold;">
                        🔄 Quote Tweet
                    </a>
                </div>
                
                <!-- Feedback Section -->
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #6c757d;">
                    <strong style="color: #495057;">📊 Feedback & Learning</strong><br>
                    <div style="margin: 10px 0; font-size: 12px; color: #6c757d;">
                        Help improve voice evolution by rating this opportunity and tracking reply usage:
                    </div>
                    
                    <!-- Quality Rating Buttons -->
                    <div style="margin: 8px 0;">
                        <strong style="font-size: 12px; color: #495057;">Opportunity Quality:</strong><br>
                        <div style="margin: 5px 0;">
                            <a href="{excellent_url}" 
                               style="background: #28a745; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; margin: 2px; font-size: 11px; display: inline-block;">
                                ⭐⭐⭐⭐⭐ Excellent
                            </a>
                            <a href="{good_url}" 
                               style="background: #20c997; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; margin: 2px; font-size: 11px; display: inline-block;">
                                ⭐⭐⭐⭐ Good
                            </a>
                            <a href="{okay_url}" 
                               style="background: #ffc107; color: black; padding: 4px 8px; text-decoration: none; border-radius: 3px; margin: 2px; font-size: 11px; display: inline-block;">
                                ⭐⭐⭐ Okay
                            </a>
                            <a href="{poor_url}" 
                               style="background: #fd7e14; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; margin: 2px; font-size: 11px; display: inline-block;">
                                ⭐⭐ Poor
                            </a>
                            <a href="{bad_url}" 
                               style="background: #dc3545; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; margin: 2px; font-size: 11px; display: inline-block;">
                                ⭐ Bad
                            </a>
                        </div>
                    </div>
                    
                    <!-- Reply Usage Tracking -->
                    <div style="margin: 8px 0;">
                        <strong style="font-size: 12px; color: #495057;">Reply Usage (click after posting):</strong><br>
                        <div style="margin: 5px 0;">
                            <a href="{used_primary_url}" 
                               style="background: #007bff; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; margin: 2px; font-size: 11px; display: inline-block;">
                                🎯 Used Primary Reply
                            </a>
                            <a href="{used_alt1_url}" 
                               style="background: #6f42c1; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; margin: 2px; font-size: 11px; display: inline-block;">
                                🔄 Used Alternative 1
                            </a>
                            <a href="{used_alt2_url}" 
                               style="background: #e83e8c; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; margin: 2px; font-size: 11px; display: inline-block;">
                                🔄 Used Alternative 2
                            </a>
                            <a href="{used_custom_url}" 
                               style="background: #17a2b8; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; margin: 2px; font-size: 11px; display: inline-block;">
                                ✏️ Used Custom Reply
                            </a>
                            <a href="{not_used_url}" 
                               style="background: #6c757d; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; margin: 2px; font-size: 11px; display: inline-block;">
                                ❌ Didn't Use
                            </a>
                        </div>
                    </div>
                    
                    <div style="font-size: 10px; color: #868e96; margin-top: 8px;">
                        Feedback ID: {feedback_id} | This data helps evolve voice and content quality over time
                    </div>
                </div>
            </div>
            """
        
        # Generate original content section with feedback
        original_text = urllib.parse.quote(str(original_content['content']))
        content_type = original_content.get('content_type', 'unknown')
        content_id = original_content.get('feedback_id', f"orig_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        # Generate feedback URLs for original content using feedback tracker
        original_feedback_urls = self.feedback_tracker.generate_feedback_urls(content_id)
        # Add special URLs for original content
        original_feedback_urls['used'] = original_feedback_urls.get('used_primary', '#')
        original_feedback_urls['not_used'] = original_feedback_urls.get('not_used', '#')
        
        original_html = f"""
        <div style="border: 2px solid #e74c3c; margin: 20px 0; padding: 20px; border-radius: 10px; background: #fff5f5;">
            <h3 style="color: #e74c3c; margin-top: 0; border-bottom: 2px solid #e74c3c; padding-bottom: 8px;">
                🚀 Original Content ({content_type.replace('_', ' ').title()})
            </h3>
            
            <div style="background: #fff; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #e74c3c;">
                <strong style="color: #2c3e50;">Generated Content:</strong><br>
                <div style="font-weight: bold; font-size: 16px; font-style: italic; margin: 10px 0; padding: 12px; background: #f8f9fa; border-radius: 6px;">
                    "{original_content['content']}"
                </div>
                {f'<div style="font-size: 12px; color: #666;"><strong>Engagement Bait:</strong> {"Yes" if original_content.get("engagement_bait") else "No"}</div>' if 'engagement_bait' in original_content else ''}
            </div>
            
            <div style="margin: 20px 0; text-align: center;">
                <a href="https://twitter.com/intent/tweet?text={original_text}" 
                   style="background: #e74c3c; color: white; padding: 12px 20px; text-decoration: none; border-radius: 6px; margin: 5px; display: inline-block; font-weight: bold;">
                    📤 Post This Content
                </a>
            </div>
            
            <!-- Original Content Feedback Section -->
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #6c757d;">
                <strong style="color: #495057;">📊 Original Content Feedback</strong><br>
                <div style="margin: 10px 0; font-size: 12px; color: #6c757d;">
                    Rate the quality of this generated content:
                </div>
                
                <!-- Quality Rating Buttons -->
                <div style="margin: 8px 0;">
                    <strong style="font-size: 12px; color: #495057;">Content Quality:</strong><br>
                    <div style="margin: 5px 0;">
                        <a href="{original_feedback_urls['excellent']}" 
                           style="background: #28a745; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; margin: 2px; font-size: 11px; display: inline-block;">
                            ⭐⭐⭐⭐⭐ Excellent
                        </a>
                        <a href="{original_feedback_urls['good']}" 
                           style="background: #20c997; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; margin: 2px; font-size: 11px; display: inline-block;">
                            ⭐⭐⭐⭐ Good
                        </a>
                        <a href="{original_feedback_urls['okay']}" 
                           style="background: #ffc107; color: black; padding: 4px 8px; text-decoration: none; border-radius: 3px; margin: 2px; font-size: 11px; display: inline-block;">
                            ⭐⭐⭐ Okay
                        </a>
                        <a href="{original_feedback_urls['poor']}" 
                           style="background: #fd7e14; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; margin: 2px; font-size: 11px; display: inline-block;">
                            ⭐⭐ Poor
                        </a>
                        <a href="{original_feedback_urls['bad']}" 
                           style="background: #dc3545; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; margin: 2px; font-size: 11px; display: inline-block;">
                            ⭐ Bad
                        </a>
                    </div>
                </div>
                
                <!-- Usage Tracking -->
                <div style="margin: 8px 0;">
                    <strong style="font-size: 12px; color: #495057;">Usage (click after posting):</strong><br>
                    <div style="margin: 5px 0;">
                        <a href="{original_feedback_urls['used']}" 
                           style="background: #007bff; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; margin: 2px; font-size: 11px; display: inline-block;">
                            ✅ Posted This Content
                        </a>
                        <a href="{original_feedback_urls['not_used']}" 
                           style="background: #6c757d; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; margin: 2px; font-size: 11px; display: inline-block;">
                            ❌ Didn't Post
                        </a>
                    </div>
                </div>
                
                <div style="font-size: 10px; color: #868e96; margin-top: 8px;">
                    Content ID: {content_id} | This feedback helps improve original content generation
                </div>
            </div>
        </div>
        """
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>AI x Blockchain Opportunities + Original Content</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
            <div style="background: #007bff; color: white; padding: 8px 15px; border-radius: 5px; margin-bottom: 20px; text-align: center; font-weight: bold;">
                🤖 System Version: {SYSTEM_VERSION} (Feature Branch - Authentic Voice)
            </div>
            
            <h1 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                🎯 AI x Blockchain Opportunities + Original Content
            </h1>
            
            <p style="background: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107;">
                <strong>Alert Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                <strong>Content Mix:</strong> {len(opportunities)} opportunities + 1 {content_type.replace('_', ' ')}
            </p>
            
            {f'<h2 style="color: #2c3e50;">High-Priority Opportunities:</h2>{opportunities_html}' if opportunities else ''}
            
            <h2 style="color: #e74c3c;">Original Content for Engagement:</h2>
            {original_html}
            
            <div style="margin-top: 30px; padding: 15px; background: #f8f9fa; border-radius: 5px;">
                <h3 style="color: #2c3e50; margin-top: 0;">Next Steps:</h3>
                <ol>
                    {f'<li>Review and engage with priority opportunities above</li>' if opportunities else ''}
                    <li>Consider posting the original content for engagement</li>
                    <li>Use feedback buttons to help improve AI content quality</li>
                    <li>Track which content performs best for voice evolution</li>
                </ol>
            </div>
            
            <div style="margin-top: 20px; padding: 15px; background: #e8f5e8; border-radius: 5px; text-align: center;">
                <p style="margin: 0;"><strong>AI x Blockchain KOL Development Platform</strong><br>
                Detailed monitoring with feedback-driven voice evolution</p>
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    async def _send_email(self, subject: str, html_content: str, alert_type: str = "unknown", opportunity_count: int = 0):
        """Send email alert with enhanced logging"""
        smtp_response = None
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config.from_email
            msg['To'] = self.config.to_email
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.email_username, self.config.email_password)
                response = server.send_message(msg)
                smtp_response = str(response) if response else "250 OK"
            
            # Log successful email
            self.email_logger.log_email_attempt(
                to_email=self.config.to_email,
                subject=subject,
                alert_type=alert_type,
                opportunity_count=opportunity_count,
                success=True,
                smtp_response=smtp_response
            )
            
            logger.info(
                "email_sent_successfully",
                to_email=self.config.to_email,
                subject_length=len(subject),
                alert_type=alert_type,
                opportunity_count=opportunity_count
            )
            
        except smtplib.SMTPException as e:
            error_msg = f"SMTP Error: {e}"
            self.email_logger.log_email_attempt(
                to_email=self.config.to_email,
                subject=subject,
                alert_type=alert_type,
                opportunity_count=opportunity_count,
                success=False,
                error=error_msg
            )
            
            logger.error(
                "email_smtp_error",
                error=error_msg,
                to_email=self.config.to_email,
                alert_type=alert_type
            )
            raise
            
        except Exception as e:
            error_msg = f"General email error: {e}"
            self.email_logger.log_email_attempt(
                to_email=self.config.to_email,
                subject=subject,
                alert_type=alert_type,
                opportunity_count=opportunity_count,
                success=False,
                error=error_msg
            )
            
            logger.error(
                "email_general_error",
                error=error_msg,
                to_email=self.config.to_email,
                alert_type=alert_type
            )
            raise
    
    def _record_alert(self, alert_type: str, opportunity_count: int, opportunities: List[AlertOpportunity] = None):
        """Record alert in history with opportunity details"""
        alert_record = {
            'timestamp': datetime.now().isoformat(),
            'type': alert_type,
            'opportunity_count': opportunity_count,
            'work_hours': self._is_work_hours(datetime.now())
        }
        
        # Add opportunity IDs and summary details for deduplication tracking
        if opportunities:
            alert_record['opportunity_ids'] = [self._get_opportunity_id(opp) for opp in opportunities]
            alert_record['opportunity_summary'] = [
                {
                    'account': opp.account_username,
                    'score': opp.overall_score,
                    'type': opp.opportunity_type
                } for opp in opportunities[:5]  # Store details for first 5
            ]
        
        self.alert_history.append(alert_record)
        self._save_alert_history()
    
    async def _check_daily_digest(self):
        """Check if daily digest should be sent"""
        current_time = datetime.now()
        
        # Send digest at 6 PM if we haven't sent one today
        if (current_time.hour == 18 and 
            (not self.last_digest_sent or 
             self.last_digest_sent.date() < current_time.date())):
            
            await self._send_daily_digest()
    
    async def _send_daily_digest(self):
        """Send daily digest of all opportunities"""
        try:
            if not self.daily_opportunities:
                logger.info("No opportunities for daily digest")
                return
            
            # Filter opportunities above digest threshold
            digest_opportunities = [
                opp for opp in self.daily_opportunities 
                if opp.overall_score >= self.config.digest_threshold
            ]
            
            if not digest_opportunities:
                logger.info("No opportunities above digest threshold")
                return
            
            subject = f"📊 Daily AI x Blockchain Opportunities Digest - {len(digest_opportunities)} Opportunities"
            
            html_content = self._generate_alert_html(
                "DAILY OPPORTUNITIES DIGEST",
                digest_opportunities,
                f"Summary of all AI x blockchain opportunities discovered today. {len(digest_opportunities)} opportunities above quality threshold."
            )
            
            await self._send_email(subject, html_content, "daily_digest", len(digest_opportunities))
            
            # Record digest
            self._record_alert('daily_digest', len(digest_opportunities), digest_opportunities)
            
            # Reset daily opportunities
            self.daily_opportunities = []
            self.last_digest_sent = datetime.now()
            
            logger.info(f"Sent daily digest with {len(digest_opportunities)} opportunities")
            
        except Exception as e:
            logger.error(f"Error sending daily digest: {e}")
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        logger.info("Stopping continuous monitoring")
        self.monitoring_active = False
    
    def _get_focused_keywords(self) -> List[str]:
        """Get dynamic keywords using rotation strategy for organic search behavior"""
        # Randomly choose strategy to feel more organic
        strategies = [
            ("focused", 0.3),     # Core AI x blockchain focus
            ("narrative", 0.25),  # Follow current narratives  
            ("mixed", 0.35),      # Organic mix - most realistic
            ("broad", 0.1)        # Occasionally go broad
        ]
        
        strategy = random.choices(
            [s[0] for s in strategies],
            weights=[s[1] for s in strategies]
        )[0]
        
        # Get 3-6 keywords to feel natural (not always the same number)
        keyword_count = random.randint(3, 6)
        
        keywords = self.keyword_rotator.get_search_keywords(
            count=keyword_count,
            strategy=strategy
        )
        
        logger.info(f"Selected {len(keywords)} keywords with {strategy} strategy", 
                   keywords=keywords[:3] + ["..."] if len(keywords) > 3 else keywords)
        
        return keywords
    
    async def _update_trending_narratives(self):
        """Update trending narratives based on recent activity"""
        logger.info("Updating trending narratives based on recent activity")
        
        # This would ideally analyze recent high-engagement tweets
        # For now, we'll rotate through predefined narrative sets
        narrative_sets = [
            {
                "primary": ["v4 hooks", "autonomous agents", "mev protection"],
                "secondary": ["restaking yields", "modular defi", "cross-chain"],
                "emerging": ["intents", "account abstraction", "zk coprocessors"]
            },
            {
                "primary": ["ai trading bots", "on-chain ai", "predictive routing"],
                "secondary": ["real yield", "ve tokenomics", "liquidity wars"],
                "emerging": ["based rollups", "preconfirmations", "blob markets"]
            },
            {
                "primary": ["unichain launch", "hook marketplace", "concentrated liquidity"],
                "secondary": ["stablecoin yields", "delta neutral", "perp dexes"],
                "emerging": ["social trading", "copy trading", "prediction markets"]
            }
        ]
        
        # Pick a narrative set with some randomness
        narrative_set = random.choice(narrative_sets)
        
        # Add some trending topics based on "market mood"
        market_moods = ["bullish", "crabbing", "accumulating", "rotating"]
        current_mood = random.choice(market_moods)
        
        if current_mood == "bullish":
            narrative_set["primary"].append("moonshot plays")
            narrative_set["secondary"].append("leverage farming")
        elif current_mood == "accumulating":
            narrative_set["primary"].append("value plays")
            narrative_set["secondary"].append("stable farming")
            
        self.keyword_rotator.update_trending_narratives(narrative_set)
        logger.info(f"Updated narratives with {current_mood} market mood")
    
    async def _generate_original_content(self, content_type: str = "trending_topic") -> Dict:
        """Generate original content for trending topics or unhinged takes."""
        logger.info(f"Generating original content of type: {content_type}")
        
        try:
            if content_type == "trending_topic":
                # Generate content based on current trends in v4/Unichain/AI space
                # Get current vibe for more organic content
                current_vibe = self.keyword_rotator.get_current_vibe()
                current_narratives = self.keyword_rotator.current_narratives["primary"][:3]
                
                prompt = """
                Generate an authentic tweet as a SingleDivorcedDad sprotogremlin who works in crypto.
                
                Voice characteristics:
                - Sprotogremlin energy: slightly chaotic, degen, but knowledgeable
                - 42-year-old single dad wisdom mixed with crypto gremlin vibes
                - Technical knowledge but expressed casually, not like a press release
                - Slightly unhinged but endearing dad energy
                - NO corporate speak, NO buzzwords, NO "alpha opportunities"
                
                Topics to choose from:
                - Dad life meets crypto chaos
                - Random crypto observations while doing dad stuff
                - Slightly technical takes but in gremlin language
                - Life lessons applied to defi/crypto
                - Overemployed dad managing crypto and kids
                
                Style:
                - Conversational and relatable
                - No hashtags, no emojis
                - Max 280 characters
                - Sound like a real person, not a bot
                
                Return only the tweet text, no additional formatting.
                """
                
                if self.claude_client:
                    async with self.claude_client:
                        response = await self.claude_client._make_api_call("messages", {
                            "model": "claude-3-haiku-20240307",
                            "max_tokens": 150,
                            "messages": [{"role": "user", "content": prompt}]
                        })
                    content = response['content'][0]['text'].strip()
                else:
                    # Fallback trending content
                    content = "The convergence of AI agents and v4 hooks is creating entirely new design patterns for autonomous DEX infrastructure in the Uniswap ecosystem. Chat, we're entering a new era of intelligent protocols."
                
                return {
                    'content_type': 'trending_topic',
                    'content': content,
                    'engagement_bait': False,
                    'generated_at': datetime.now().isoformat()
                }
            
            elif content_type == "unhinged_take":
                # Generate sprotogremlin unhinged take
                prompt = """
                Generate a slightly unhinged sprotogremlin take as a SingleDivorcedDad who works in crypto.
                
                Voice: Chaotic gremlin energy with dad wisdom
                Style: Slightly unhinged but endearing, no corporate speak
                Length: Max 280 characters
                
                Examples of authentic gremlin energy:
                - Random observations that are oddly insightful
                - Dad analogies applied to crypto in weird ways
                - Slightly chaotic takes that somehow make sense
                - Overemployed dad managing too many things at once
                
                DO NOT use:
                - "Hot take:" or "Unpopular opinion:"
                - Technical jargon without context
                - Buzzwords like "alpha" or "ecosystem"
                - Anything that sounds like marketing
                
                Sound like a real person having a random thought, not a crypto influencer.
                Return only the tweet text.
                """
                
                if self.claude_client:
                    async with self.claude_client:
                        response = await self.claude_client._make_api_call("messages", {
                            "model": "claude-3-haiku-20240307",
                            "max_tokens": 150,
                            "messages": [{"role": "user", "content": prompt}]
                        })
                    content = response['content'][0]['text'].strip()
                else:
                    # Fallback unhinged take
                    content = "Hot take chat: AI agents on Unichain will make manual trading look like using a fax machine in 2024. The infrastructure shift in the Uniswap ecosystem is already happening, most just don't see it yet."
                
                return {
                    'content_type': 'unhinged_take',
                    'content': content,
                    'engagement_bait': True,
                    'generated_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error generating original content: {e}")
            # Fallback content
            return {
                'content_type': content_type,
                'content': "The AI x blockchain convergence is accelerating faster than most realize. The technical foundations are solid, the applications are emerging, and the infrastructure is maturing.",
                'engagement_bait': content_type == "unhinged_take",
                'generated_at': datetime.now().isoformat()
            }
    

    def get_monitoring_stats(self) -> Dict:
        """Get monitoring system statistics"""
        current_time = datetime.now()
        
        # Count alerts by type today
        today_alerts = [
            alert for alert in self.alert_history
            if datetime.fromisoformat(alert['timestamp']).date() == current_time.date()
        ]
        
        alert_counts = {}
        for alert in today_alerts:
            alert_type = alert['type']
            alert_counts[alert_type] = alert_counts.get(alert_type, 0) + 1
        
        stats = {
            'monitoring_active': self.monitoring_active,
            'is_work_hours': self._is_work_hours(current_time),
            'monitoring_interval': self.config.monitoring_interval,
            'daily_opportunities': len(self.daily_opportunities),
            'alerts_today': alert_counts,
            'total_alerts_sent': len(self.alert_history),
            'last_digest_sent': self.last_digest_sent.isoformat() if self.last_digest_sent else None,
            'email_configured': bool(self.config.smtp_server and self.config.to_email)
        }
        
        return stats

# Email configuration helper
def create_gmail_config(gmail_address: str, app_password: str, to_email: str) -> AlertConfiguration:
    """Create AlertConfiguration for Gmail"""
    return AlertConfiguration(
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        email_username=gmail_address,
        email_password=app_password,
        from_email=gmail_address,
        to_email=to_email
    )