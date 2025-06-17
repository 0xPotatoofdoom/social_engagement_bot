"""
Cron-Based Monitoring System
Continuous monitoring with intelligent email alerts for AI x blockchain opportunities
"""

import asyncio
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import structlog
import os

logger = structlog.get_logger()

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
            
            # Create test alert only if not already sent today
            logger.info("Checking if test alert needed")
            from bot.scheduling.cron_monitor import AlertOpportunity
            
            test_alert = AlertOpportunity(
                account_username="TestAccount",
                account_tier=1,
                content_text=f"Daily AI x blockchain test opportunity - {datetime.now().strftime('%Y-%m-%d')}",
                content_url=f"https://twitter.com/test/status/{datetime.now().strftime('%Y%m%d')}",
                timestamp=datetime.now().isoformat(),
                
                overall_score=0.85,
                ai_blockchain_relevance=0.90,
                technical_depth=0.80,
                opportunity_type="test_opportunity",
                suggested_response_type="test_response",
                time_sensitivity="immediate",
                
                strategic_context="Daily test opportunity to verify email system",
                suggested_response="Test the email alert system",
                
                generated_reply="This is a daily test reply to verify the email system is working correctly.",
                reply_reasoning="Testing email system functionality",
                alternative_responses=["Test alternative 1", "Test alternative 2"],
                engagement_prediction=0.75,
                voice_alignment_score=0.80
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
            # Get AI x blockchain keywords from enhanced monitoring
            ai_blockchain_keywords = [
                "ai agents blockchain",
                "autonomous trading",
                "machine learning defi",
                "v4 hooks ai",
                "uniswap automation",
                "predictive mev",
                "ai blockchain convergence",
                "intelligent protocols"
            ]
            
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
                    
                    # Generate content for this opportunity
                    await self._generate_opportunity_content(alert_opp)
                    processed.append(alert_opp)
                    
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
                    
                    # Generate content for this opportunity
                    await self._generate_opportunity_content(alert_opp)
                    processed.append(alert_opp)
                    
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
            
            Voice Guidelines:
            - AI x blockchain technical authority
            - Conversational yet authoritative
            - Forward-thinking innovation expert
            - Educational but confident
            
            Generate a reply that:
            1. Demonstrates technical expertise in AI x blockchain convergence
            2. Adds unique value to the conversation
            3. Positions as thought leader in the space
            4. Stays under 280 characters
            5. Includes relevant AI x blockchain insights
            
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
                - Conversational yet authoritative
                - Forward-thinking innovation expert
                - Educational but confident
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
        """Send email alerts based on priority levels"""
        if not opportunities:
            return
        
        # Immediate alerts (>= 0.8 score)
        immediate_alerts = [opp for opp in opportunities if opp.overall_score >= self.config.immediate_threshold]
        if immediate_alerts:
            await self._send_immediate_alert(immediate_alerts)
        
        # Priority alerts (>= 0.6 score)
        priority_alerts = [opp for opp in opportunities if self.config.priority_threshold <= opp.overall_score < self.config.immediate_threshold]
        if priority_alerts:
            await self._send_priority_alert(priority_alerts)
    
    async def _send_immediate_alert(self, opportunities: List[AlertOpportunity]):
        """Send immediate high-priority email alert"""
        try:
            subject = f"🔥 IMMEDIATE: {len(opportunities)} High-Priority AI x Blockchain Opportunities"
            
            html_content = self._generate_alert_html(
                "IMMEDIATE ACTION REQUIRED",
                opportunities,
                "These opportunities require immediate attention (within 30 minutes) for maximum impact."
            )
            
            await self._send_email(subject, html_content)
            
            # Record alert
            self._record_alert('immediate', len(opportunities), opportunities)
            
            logger.info(f"Sent immediate alert for {len(opportunities)} opportunities")
            
        except Exception as e:
            logger.error(f"Error sending immediate alert: {e}")
    
    async def _send_priority_alert(self, opportunities: List[AlertOpportunity]):
        """Send priority email alert"""
        try:
            subject = f"⚡ PRIORITY: {len(opportunities)} AI x Blockchain Engagement Opportunities"
            
            html_content = self._generate_alert_html(
                "PRIORITY OPPORTUNITIES",
                opportunities,
                "These opportunities are time-sensitive and should be addressed within 1-2 hours."
            )
            
            await self._send_email(subject, html_content)
            
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
    
    async def _send_email(self, subject: str, html_content: str):
        """Send email alert"""
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
                server.send_message(msg)
            
            logger.info(f"Email sent successfully: {subject}")
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
    
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
            
            await self._send_email(subject, html_content)
            
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