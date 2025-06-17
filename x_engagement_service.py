"""
24/7 X Engagement Bot Service - Fixed Rate Limiting Issue
Intelligent X engagement monitoring with AI-powered responses and ROI tracking
"""

import asyncio
import json
import os
import time
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import sys

# Add src to path for imports
import os
if os.path.exists('/app/src'):
    sys.path.append('/app/src')
else:
    sys.path.append('./src')  # Local development

from bot.api.x_client import XAPIClient
from bot.api.claude_client import ClaudeAPIClient
from bot.accounts.tracker import StrategicAccountTracker
from bot.scheduling.cron_monitor import CronMonitorSystem, AlertConfiguration, AlertOpportunity

# Import enhanced logging system
from bot.utils.logging_config import setup_logging, get_component_logger

# Setup advanced logging with rotation
log_dir = '/app/logs' if os.path.exists('/app') else './logs'
logging_manager = setup_logging(log_dir)
logger = get_component_logger("main_service")

@dataclass
class MetricsSnapshot:
    """Performance metrics snapshot for ROI analysis"""
    timestamp: str
    
    # API Usage Metrics
    api_calls_made: int
    rate_limit_hits: int
    api_efficiency: float
    
    # Opportunity Metrics
    opportunities_found: int
    high_priority_opportunities: int
    email_alerts_sent: int
    
    # Engagement Metrics
    strategic_accounts_engaged: int
    tier_1_interactions: int
    avg_opportunity_score: float
    
    # Voice Development Metrics
    avg_voice_alignment: float
    technical_content_percentage: float
    ai_blockchain_focus_score: float
    
    # ROI Metrics
    cost_per_opportunity: float
    engagement_efficiency: float
    strategic_value_generated: float

class RateLimitManager:
    """Intelligent rate limiting with exponential backoff"""
    
    def __init__(self):
        self.api_calls = {}
        self.rate_limits = {
            'search_tweets': {'limit': 300, 'window': 900, 'calls': []},  # 300 per 15 min
            'user_timeline': {'limit': 1500, 'window': 900, 'calls': []}, # 1500 per 15 min  
            'user_lookup': {'limit': 300, 'window': 900, 'calls': []},    # 300 per 15 min
        }
        self.backoff_until = {}
    
    def can_make_call(self, endpoint: str) -> bool:
        """Check if we can make a call to the endpoint"""
        if endpoint in self.backoff_until:
            if time.time() < self.backoff_until[endpoint]:
                return False
            else:
                del self.backoff_until[endpoint]
        
        now = time.time()
        limit_info = self.rate_limits.get(endpoint, {'limit': 300, 'window': 900, 'calls': []})
        
        # Remove old calls outside the window
        limit_info['calls'] = [call_time for call_time in limit_info['calls'] 
                              if now - call_time < limit_info['window']]
        
        return len(limit_info['calls']) < limit_info['limit']
    
    def record_call(self, endpoint: str):
        """Record an API call"""
        now = time.time()
        if endpoint not in self.rate_limits:
            self.rate_limits[endpoint] = {'limit': 300, 'window': 900, 'calls': []}
        
        self.rate_limits[endpoint]['calls'].append(now)
    
    def handle_rate_limit(self, endpoint: str, retry_after: int = None):
        """Handle rate limit hit with exponential backoff"""
        backoff_time = retry_after or 900  # Default 15 minutes
        self.backoff_until[endpoint] = time.time() + backoff_time
        logger.warning(f"Rate limit hit for {endpoint}, backing off for {backoff_time}s")
    
    def get_status(self) -> Dict:
        """Get current rate limit status"""
        now = time.time()
        status = {}
        
        for endpoint, info in self.rate_limits.items():
            # Clean old calls
            info['calls'] = [call_time for call_time in info['calls'] 
                           if now - call_time < info['window']]
            
            remaining = info['limit'] - len(info['calls'])
            backoff = self.backoff_until.get(endpoint, 0) - now
            
            status[endpoint] = {
                'calls_made': len(info['calls']),
                'remaining': remaining,
                'backoff_seconds': max(0, backoff)
            }
        
        return status

class MetricsTracker:
    """Track performance metrics for ROI analysis"""
    
    def __init__(self):
        data_dir = '/app/data' if os.path.exists('/app/data') else './data'
        self.metrics_file = Path(data_dir) / 'metrics' / 'performance_metrics.json'
        self.metrics_file.parent.mkdir(exist_ok=True, parents=True)
        self.session_metrics = {
            'api_calls_made': 0,
            'rate_limit_hits': 0,
            'opportunities_found': 0,
            'high_priority_opportunities': 0,
            'email_alerts_sent': 0,
            'strategic_accounts_engaged': 0,
            'tier_1_interactions': 0,
            'opportunity_scores': [],
            'voice_alignments': [],
            'session_start': datetime.now().isoformat()
        }
    
    def record_api_call(self):
        """Record an API call"""
        self.session_metrics['api_calls_made'] += 1
    
    def record_rate_limit_hit(self):
        """Record a rate limit hit"""
        self.session_metrics['rate_limit_hits'] += 1
    
    def record_opportunity(self, opportunity: AlertOpportunity):
        """Record an opportunity found"""
        self.session_metrics['opportunities_found'] += 1
        
        if opportunity.overall_score >= 0.8:
            self.session_metrics['high_priority_opportunities'] += 1
        
        if opportunity.account_tier == 1:
            self.session_metrics['tier_1_interactions'] += 1
        
        self.session_metrics['opportunity_scores'].append(opportunity.overall_score)
        
        if opportunity.voice_alignment_score:
            self.session_metrics['voice_alignments'].append(opportunity.voice_alignment_score)
    
    def record_email_sent(self):
        """Record an email alert sent"""
        self.session_metrics['email_alerts_sent'] += 1
    
    def get_current_snapshot(self) -> MetricsSnapshot:
        """Get current metrics snapshot"""
        opportunity_scores = self.session_metrics['opportunity_scores']
        voice_alignments = self.session_metrics['voice_alignments']
        
        api_efficiency = (
            self.session_metrics['opportunities_found'] / 
            max(1, self.session_metrics['api_calls_made'])
        ) * 100
        
        cost_per_opportunity = (
            0.0 if self.session_metrics['opportunities_found'] == 0 
            else self.session_metrics['api_calls_made'] / self.session_metrics['opportunities_found']
        )
        
        return MetricsSnapshot(
            timestamp=datetime.now().isoformat(),
            api_calls_made=self.session_metrics['api_calls_made'],
            rate_limit_hits=self.session_metrics['rate_limit_hits'],
            api_efficiency=api_efficiency,
            opportunities_found=self.session_metrics['opportunities_found'],
            high_priority_opportunities=self.session_metrics['high_priority_opportunities'],
            email_alerts_sent=self.session_metrics['email_alerts_sent'],
            strategic_accounts_engaged=len(set(self.session_metrics.get('accounts_engaged', []))),
            tier_1_interactions=self.session_metrics['tier_1_interactions'],
            avg_opportunity_score=sum(opportunity_scores) / len(opportunity_scores) if opportunity_scores else 0.0,
            avg_voice_alignment=sum(voice_alignments) / len(voice_alignments) if voice_alignments else 0.0,
            technical_content_percentage=75.0,  # Placeholder - could be calculated from content analysis
            ai_blockchain_focus_score=85.0,    # Placeholder - from strategic focus
            cost_per_opportunity=cost_per_opportunity,
            engagement_efficiency=api_efficiency,
            strategic_value_generated=self.session_metrics['high_priority_opportunities'] * 10.0  # Weighting
        )
    
    def save_snapshot(self, snapshot: MetricsSnapshot):
        """Save metrics snapshot to file"""
        try:
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r') as f:
                    history = json.load(f)
            else:
                history = []
            
            history.append(asdict(snapshot))
            
            # Keep last 1000 snapshots
            if len(history) > 1000:
                history = history[-1000:]
            
            with open(self.metrics_file, 'w') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving metrics snapshot: {e}")

class HealthServer:
    """Simple health check server"""
    
    def __init__(self, port=8080):
        self.port = port
        self.server = None
        self.thread = None
    
    def start(self):
        """Start the health server"""
        handler = lambda *args: HealthHandler(*args)
        self.server = HTTPServer(('0.0.0.0', self.port), handler)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"Health server started on port {self.port}")
    
    def stop(self):
        """Stop the health server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()

class HealthHandler(BaseHTTPRequestHandler):
    """Health check request handler"""
    
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "healthy", "service": "x_engagement_bot"}')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress HTTP logs

class XEngagementService:
    """Main 24/7 monitoring service - Fixed Rate Limiting Issue"""
    
    def __init__(self):
        self.running = True
        self.rate_manager = RateLimitManager()
        self.metrics = MetricsTracker()
        self.health_server = HealthServer()
        
        # Initialize clients
        self.x_client = None
        self.claude_client = None
        self.strategic_tracker = None
        self.monitor = None
        
        # Monitoring configuration
        self.monitoring_interval = 30 * 60  # 30 minutes
        self.metrics_interval = 60 * 60     # 1 hour
        self.report_interval = 24 * 60 * 60 # 24 hours
        
        self.last_metrics_save = time.time()
        self.last_report_sent = time.time()
    
    async def initialize_clients(self):
        """Initialize API clients with error handling - SKIP HEALTH CHECK TO AVOID RATE LIMITS"""
        try:
            logger.info("Initializing API clients (skipping health check to avoid rate limits)...")
            
            # X API Client
            self.x_client = XAPIClient(
                api_key=os.getenv('X_API_KEY'),
                api_secret=os.getenv('X_API_SECRET'),
                access_token=os.getenv('X_ACCESS_TOKEN'),
                access_token_secret=os.getenv('X_ACCESS_TOKEN_SECRET'),
                bearer_token=os.getenv('X_BEARER_TOKEN')
            )
            
            # Claude API Client
            self.claude_client = ClaudeAPIClient(api_key=os.getenv('CLAUDE_API_KEY'))
            
            # Strategic Account Tracker
            self.strategic_tracker = StrategicAccountTracker(
                x_client=self.x_client, 
                claude_client=self.claude_client
            )
            
            # Email configuration
            email_config = AlertConfiguration(
                smtp_server=os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
                smtp_port=int(os.getenv('SMTP_PORT', '587')),
                email_username=os.getenv('SENDER_EMAIL'),
                email_password=os.getenv('SENDER_PASSWORD'),
                from_email=os.getenv('SENDER_EMAIL'),
                to_email=os.getenv('RECIPIENT_EMAIL', os.getenv('SENDER_EMAIL'))
            )
            
            # Monitoring System
            self.monitor = CronMonitorSystem(
                x_client=self.x_client,
                claude_client=self.claude_client,
                strategic_tracker=self.strategic_tracker,
                config=email_config
            )
            
            # SKIP API health check to avoid rate limits - just check object creation
            if self.x_client and self.claude_client and self.monitor:
                logger.info("✅ All clients initialized successfully (health check skipped)")
                return True
            else:
                logger.error("❌ Client initialization failed - missing objects")
                return False
                
        except Exception as e:
            logger.error(f"❌ Client initialization failed: {e}")
            return False
    
    async def send_test_alert(self):
        """Send a test alert to verify email system without making any API calls"""
        try:
            logger.info("Creating test alert to verify email system...")
            
            # Create a test opportunity without any API calls
            test_alert = AlertOpportunity(
                account_username="TestAccount",
                account_tier=1,
                content_text="🚀 X Engagement Bot is now running! This is a test alert to verify the email system is working correctly.",
                content_url="https://twitter.com/intent/tweet?text=X%20Engagement%20Bot%20Test",
                timestamp=datetime.now().isoformat(),
                overall_score=0.85,
                ai_blockchain_relevance=0.80,
                technical_depth=0.75,
                opportunity_type="system_test",
                suggested_response_type="engagement_test",
                time_sensitivity="immediate",
                strategic_context="System verification test",
                suggested_response="Verify that the X Engagement Bot email alert system is functioning properly",
                generated_reply="✅ X Engagement Bot email system is operational and ready for monitoring!",
                reply_reasoning="Initial system verification to confirm email delivery and formatting",
                alternative_responses=["System test successful", "Email alerts working correctly"],
                engagement_prediction=0.90,
                voice_alignment_score=0.88
            )
            
            # Send the test alert
            await self.monitor._send_immediate_alert([test_alert])
            self.metrics.record_email_sent()
            logger.info("✅ Test alert sent successfully - email system verified")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Test alert failed: {e}")
            return False
    
    async def monitoring_cycle(self):
        """Single monitoring cycle with rate limiting - SIMPLIFIED TO AVOID IMMEDIATE API CALLS"""
        try:
            logger.info("Starting monitoring cycle...")
            all_opportunities = []
            
            # Check if we have room for any API calls
            can_search = self.rate_manager.can_make_call('search_tweets')
            can_timeline = self.rate_manager.can_make_call('user_timeline')
            
            if not can_search and not can_timeline:
                logger.warning("All endpoints rate limited - sleeping until reset")
                return
            
            # Simple keyword search only if rate limits allow
            if can_search:
                try:
                    logger.info("Attempting simple keyword search...")
                    self.rate_manager.record_call('search_tweets')
                    self.metrics.record_api_call()
                    
                    # Use a simple search that's less likely to hit limits
                    raw_keyword_opportunities = await self.monitor._monitor_ai_blockchain_keywords()
                    if raw_keyword_opportunities:
                        # Process raw opportunities into AlertOpportunity objects
                        processed_opportunities = await self.monitor._process_opportunities(raw_keyword_opportunities)
                        all_opportunities.extend(processed_opportunities)
                        logger.info(f"Found {len(processed_opportunities)} keyword opportunities")
                        
                        for opp in processed_opportunities:
                            self.metrics.record_opportunity(opp)
                            
                except Exception as e:
                    if "rate limit" in str(e).lower():
                        self.rate_manager.handle_rate_limit('search_tweets')
                        self.metrics.record_rate_limit_hit()
                        logger.warning(f"Keyword search hit rate limit: {e}")
                    else:
                        logger.warning(f"Keyword search error: {e}")
            else:
                logger.info("Skipping keyword search - rate limited")
            
            # Send alerts for any opportunities found
            if all_opportunities:
                high_priority = [opp for opp in all_opportunities if opp.overall_score >= 0.8]
                if high_priority:
                    try:
                        await self.monitor._send_immediate_alert(high_priority)
                        self.metrics.record_email_sent()
                        logger.info(f"Sent immediate alert for {len(high_priority)} opportunities")
                    except Exception as e:
                        logger.error(f"Email alert failed: {e}")
            
            # Log cycle summary
            rate_status = self.rate_manager.get_status()
            logger.info(f"Cycle complete: {len(all_opportunities)} opportunities, Rate limits: {rate_status}")
            
        except Exception as e:
            logger.error(f"Monitoring cycle error: {e}")
    
    async def save_metrics(self):
        """Save current metrics snapshot"""
        try:
            snapshot = self.metrics.get_current_snapshot()
            self.metrics.save_snapshot(snapshot)
            logger.info(f"Metrics saved: {snapshot.opportunities_found} opportunities, {snapshot.api_efficiency:.1f}% efficiency")
        except Exception as e:
            logger.error(f"Metrics save error: {e}")
    
    async def send_daily_report(self):
        """Send daily performance report"""
        try:
            logger.info("Sending daily performance report...")
            snapshot = self.metrics.get_current_snapshot()
            
            logger.info("📊 Daily Performance Summary:")
            logger.info(f"   API Calls: {snapshot.api_calls_made}")
            logger.info(f"   Opportunities: {snapshot.opportunities_found}")
            logger.info(f"   High Priority: {snapshot.high_priority_opportunities}")
            logger.info(f"   Email Alerts: {snapshot.email_alerts_sent}")
            logger.info(f"   API Efficiency: {snapshot.api_efficiency:.1f}%")
            logger.info(f"   Avg Opportunity Score: {snapshot.avg_opportunity_score:.2f}")
            
        except Exception as e:
            logger.error(f"Daily report error: {e}")
    
    async def run(self):
        """Main monitoring loop"""
        logger.info("🚀 Starting 24/7 X Engagement Bot Service (Fixed Rate Limiting)")
        
        # Start health server
        self.health_server.start()
        
        # Initialize clients without health check
        if not await self.initialize_clients():
            logger.error("Failed to initialize clients, exiting")
            return
        
        # Send test alert to verify email system
        logger.info("Sending test alert to verify email system...")
        await self.send_test_alert()
        
        logger.info(f"📊 Monitoring intervals: cycle={self.monitoring_interval/60:.0f}min, metrics={self.metrics_interval/60:.0f}min, reports={self.report_interval/3600:.0f}h")
        
        # Main monitoring loop
        while self.running:
            try:
                current_time = time.time()
                
                # Run monitoring cycle
                await self.monitoring_cycle()
                
                # Save metrics periodically
                if current_time - self.last_metrics_save >= self.metrics_interval:
                    await self.save_metrics()
                    self.last_metrics_save = current_time
                
                # Send daily report
                if current_time - self.last_report_sent >= self.report_interval:
                    await self.send_daily_report()
                    self.last_report_sent = current_time
                
                # Sleep until next cycle
                await asyncio.sleep(self.monitoring_interval)
                
            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                break
            except Exception as e:
                logger.error(f"Main loop error: {e}")
                await asyncio.sleep(60)  # Wait before retrying
        
        # Cleanup
        self.health_server.stop()
        logger.info("🛑 X Engagement Bot service stopped")
    
    def stop(self):
        """Stop the monitoring service"""
        self.running = False

# Global service instance
service = XEngagementService()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    service.stop()

# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

async def main():
    """Main entry point"""
    await service.run()

if __name__ == "__main__":
    asyncio.run(main())