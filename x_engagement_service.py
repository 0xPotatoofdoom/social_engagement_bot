"""
24/7 X Engagement Bot Service - Fixed Rate Limiting Issue
Intelligent X engagement monitoring with AI-powered responses and ROI tracking
"""

import asyncio
import json
import os
import time
import signal
from datetime import datetime
from typing import Dict
from pathlib import Path
from dataclasses import dataclass, asdict
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
    """Health check and feedback request handler"""
    
    def do_GET(self):
        from urllib.parse import urlparse
        parsed_url = urlparse(self.path)
        path_parts = parsed_url.path.strip('/').split('/')
        
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "healthy", "service": "x_engagement_bot"}')
        elif len(path_parts) >= 4 and path_parts[0] == 'feedback':
            # Handle feedback endpoints: /feedback/{opportunity_id}/{type}/{value}
            self._handle_feedback(path_parts[1], path_parts[2], path_parts[3])
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        from urllib.parse import urlparse, parse_qs
        parsed_url = urlparse(self.path)
        path_parts = parsed_url.path.strip('/').split('/')
        
        if len(path_parts) >= 3 and path_parts[0] == 'feedback' and path_parts[2] == 'improvement':
            # Handle improvement suggestions: POST /feedback/{opportunity_id}/improvement
            self._handle_improvement_suggestion(path_parts[1])
        else:
            self.send_response(404)
            self.end_headers()
    
    def _handle_feedback(self, opportunity_id: str, feedback_type: str, value: str):
        """Handle feedback endpoints"""
        try:
            from bot.analytics.feedback_tracker import get_feedback_tracker
            
            feedback_tracker = get_feedback_tracker()
            success = False
            message = ""
            
            if feedback_type == 'quality':
                rating = int(value)
                if 1 <= rating <= 5:
                    success = feedback_tracker.record_quality_feedback(
                        opportunity_id, rating, "Quality rating via email feedback"
                    )
                    message = f"Quality rating {rating} stars recorded for opportunity {opportunity_id}"
                else:
                    message = "Rating must be between 1 and 5"
            elif feedback_type == 'reply':
                valid_types = ['primary', 'alt1', 'alt2', 'custom', 'none']
                if value in valid_types:
                    success = feedback_tracker.record_reply_selection(opportunity_id, value)
                    reply_labels = {
                        'primary': 'Primary reply',
                        'alt1': 'Alternative 1',
                        'alt2': 'Alternative 2', 
                        'custom': 'Custom reply',
                        'none': 'No reply used'
                    }
                    message = f"{reply_labels[value]} usage recorded for opportunity {opportunity_id}"
                else:
                    message = f"Invalid reply type. Must be one of: {valid_types}"
            else:
                message = "Invalid feedback type"
            
            if success:
                self._send_success_page(message)
            else:
                self._send_error_page(message)
                
        except Exception as e:
            logger.error(f"Feedback handling error: {e}")
            self._send_error_page(f"Internal error: {e}")
    
    def _handle_improvement_suggestion(self, opportunity_id: str):
        """Handle improvement suggestion submissions"""
        try:
            # Parse the POST data
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            from urllib.parse import parse_qs
            parsed_data = parse_qs(post_data)
            
            improvement_text = parsed_data.get('improvement', [''])[0].strip()
            
            if improvement_text:
                from bot.analytics.feedback_tracker import get_feedback_tracker
                feedback_tracker = get_feedback_tracker()
                
                # Record the improvement suggestion
                success = feedback_tracker.record_improvement_suggestion(
                    opportunity_id, 
                    improvement_text, 
                    "User improvement suggestion via feedback form"
                )
                
                if success:
                    self._send_improvement_success_page(opportunity_id, improvement_text)
                else:
                    self._send_error_page("Failed to save improvement suggestion")
            else:
                self._send_error_page("No improvement suggestion provided")
                
        except Exception as e:
            logger.error(f"Improvement suggestion handling error: {e}")
            self._send_error_page(f"Internal error: {e}")
    
    def _send_success_page(self, message: str):
        """Send success feedback page with improvement suggestion form"""
        # Extract opportunity ID from the message if possible
        opportunity_id = "unknown"
        if "opportunity" in message.lower():
            import re
            match = re.search(r'opportunity (\w+)', message)
            if match:
                opportunity_id = match.group(1)
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Feedback Recorded</title><style>
        body {{ font-family: Arial, sans-serif; max-width: 700px; margin: 50px auto; padding: 20px; }}
        .success {{ background: #d4edda; color: #155724; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .improvement-form {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff; }}
        .form-group {{ margin: 15px 0; }}
        label {{ display: block; font-weight: bold; margin-bottom: 5px; color: #495057; }}
        textarea {{ width: 100%; min-height: 100px; padding: 10px; border: 1px solid #ced4da; border-radius: 4px; font-family: Arial, sans-serif; resize: vertical; }}
        .btn {{ background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }}
        .btn:hover {{ background: #0056b3; }}
        .btn-secondary {{ background: #6c757d; margin-left: 10px; }}
        .btn-secondary:hover {{ background: #545b62; }}
        </style></head>
        <body>
        <h1>🎯 X Engagement Bot Feedback</h1>
        <div class="success">
        <h3>✅ Feedback Recorded Successfully</h3>
        <p>{message}</p>
        <p>Thank you for helping improve the voice evolution system!</p>
        </div>
        
        <div class="improvement-form">
        <h3>💡 Help Improve Content Generation</h3>
        <p>Got specific ideas on how this content could be better? Your suggestions help fine-tune the sprotogremlin voice!</p>
        
        <form method="POST" action="/feedback/{opportunity_id}/improvement">
            <div class="form-group">
                <label for="improvement">Improvement Suggestions:</label>
                <textarea 
                    id="improvement" 
                    name="improvement" 
                    placeholder="Example: 'Make it more technical', 'Add more dad energy', 'Less formal, more degen', 'Needs more crypto slang', etc..."
                    maxlength="1000"
                ></textarea>
                <small style="color: #6c757d;">Max 1000 characters. Be specific about voice, tone, technical depth, etc.</small>
            </div>
            
            <button type="submit" class="btn">💾 Submit Suggestion</button>
            <button type="button" class="btn btn-secondary" onclick="window.close()">❌ Skip & Close</button>
        </form>
        </div>
        </body></html>
        """
        self.wfile.write(html.encode())
    
    def _send_improvement_success_page(self, opportunity_id: str, improvement_text: str):
        """Send success page for improvement suggestion submission"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Improvement Suggestion Recorded</title><style>
        body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
        .success {{ background: #d4edda; color: #155724; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .suggestion-preview {{ background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #007bff; margin: 15px 0; }}
        .btn {{ background: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; text-decoration: none; display: inline-block; }}
        </style></head>
        <body>
        <h1>🎯 X Engagement Bot Feedback</h1>
        
        <div class="success">
        <h3>💡 Improvement Suggestion Saved!</h3>
        <p>Your suggestion for opportunity <strong>{opportunity_id}</strong> has been recorded and will be used to fine-tune future content generation.</p>
        </div>
        
        <div class="suggestion-preview">
        <h4>Your Suggestion:</h4>
        <p>"{improvement_text}"</p>
        </div>
        
        <p><strong>What happens next?</strong></p>
        <ul>
        <li>✅ Your feedback is stored with the opportunity data</li>
        <li>🧠 The AI will learn from this input for future content</li>
        <li>🎯 Patterns in suggestions help evolve the sprotogremlin voice</li>
        <li>📊 Combined with quality ratings to improve generation prompts</li>
        </ul>
        
        <p style="text-align: center; margin-top: 30px;">
        <button onclick="window.close()" class="btn">✅ Close Window</button>
        </p>
        
        <p style="font-size: 12px; color: #6c757d; text-align: center; margin-top: 20px;">
        Thank you for helping improve the voice evolution system!<br>
        Your input is valuable for creating more authentic sprotogremlin content.
        </p>
        </body></html>
        """
        self.wfile.write(html.encode())
    
    def _send_error_page(self, message: str):
        """Send error feedback page"""
        self.send_response(400)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Feedback Error</title><style>
        body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
        .error {{ background: #f8d7da; color: #721c24; padding: 20px; border-radius: 8px; }}
        </style></head>
        <body>
        <h1>🎯 X Engagement Bot Feedback</h1>
        <div class="error">
        <h3>❌ Feedback Error</h3>
        <p>{message}</p>
        </div>
        <button onclick="window.close()">Close Window</button>
        </body></html>
        """
        self.wfile.write(html.encode())
    
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
        self.strategic_monitor = None
        
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
            
            # Strategic Account Monitor
            self.strategic_monitor = StrategicAccountMonitor()
            logger.info(f"Loaded {len(self.strategic_monitor.get_strategic_accounts()['tier_1']) + len(self.strategic_monitor.get_strategic_accounts()['tier_2'])} strategic accounts")
            
            # SKIP API health check to avoid rate limits - just check object creation
            if self.x_client and self.claude_client and self.monitor and self.strategic_monitor:
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
            
            # Create startup verification test alert (clearly marked as system test)
            test_alert = AlertOpportunity(
                account_username="SYSTEM_STARTUP", 
                account_tier=1,
                content_text=f"[STARTUP VERIFICATION] ✅ X Engagement Bot operational - email system test. Monitoring v4/Unichain/AI opportunities active. {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                content_url="https://system.test/startup/verification",
                timestamp=datetime.now().isoformat(),
                overall_score=0.85,
                ai_blockchain_relevance=0.80,
                technical_depth=0.80,
                opportunity_type="system_startup_verification",
                suggested_response_type="system_test",
                time_sensitivity="startup_verification",
                strategic_context="[SYSTEM TEST] Automated startup verification message",
                suggested_response="System verification - email alerts operational",
                generated_reply="[STARTUP TEST] This is an automated system verification message confirming the X Engagement Bot email system is operational and ready to monitor AI x blockchain opportunities.",
                reply_reasoning="[SYSTEM MESSAGE] Automated startup verification",
                alternative_responses=[
                    "[TEST] System operational and monitoring active",
                    "[TEST] Email alerts configured and functional"
                ],
                engagement_prediction=0.75,
                voice_alignment_score=0.80
            )
            
            # Send the test alert using new concise system
            await self.monitor._send_priority_alerts([test_alert])
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
            
            # Monitor strategic accounts if rate limits allow
            if can_timeline:
                try:
                    logger.info("Checking strategic accounts...")
                    strategic_opportunities = await self.monitor_strategic_accounts()
                    if strategic_opportunities:
                        all_opportunities.extend(strategic_opportunities)
                        logger.info(f"Found {len(strategic_opportunities)} strategic opportunities")
                        
                        for opp in strategic_opportunities:
                            self.metrics.record_opportunity(opp)
                            
                except Exception as e:
                    if "rate limit" in str(e).lower():
                        self.rate_manager.handle_rate_limit('user_timeline')
                        self.metrics.record_rate_limit_hit()
                        logger.warning(f"Strategic monitoring hit rate limit: {e}")
                    else:
                        logger.warning(f"Strategic monitoring error: {e}")
            
            # Send alerts using NEW CONCISE SYSTEM ONLY
            if all_opportunities:
                try:
                    # Use new concise email system instead of old immediate alerts
                    await self.monitor._send_priority_alerts(all_opportunities)
                    self.metrics.record_email_sent()
                    logger.info(f"Sent concise alert for {len(all_opportunities)} opportunities")
                except Exception as e:
                    logger.error(f"Concise email alert failed: {e}")
            
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
    
    async def monitor_strategic_accounts(self) -> List[AlertOpportunity]:
        """Monitor strategic KOL accounts for opportunities"""
        try:
            # Use the strategic monitor to check accounts
            raw_opportunities = await asyncio.to_thread(
                self.strategic_monitor.check_strategic_accounts,
                self.x_client,
                self.rate_manager
            )
            
            if not raw_opportunities:
                return []
            
            # Convert to AlertOpportunity objects
            alert_opportunities = []
            for opp in raw_opportunities:
                # Enrich with AI content
                enriched = await asyncio.to_thread(
                    self.strategic_monitor.enrich_opportunity_with_ai,
                    opp,
                    self.claude_client
                )
                
                # Create AlertOpportunity
                alert_opp = AlertOpportunity(
                    account_username=enriched['account'],
                    account_tier=enriched.get('tier', 2),
                    content_text=enriched['text'],
                    content_url=f"https://x.com/{enriched['account']}/status/{enriched['tweet_id']}",
                    timestamp=enriched['created_at'],
                    overall_score=enriched['relevance_score'],
                    ai_blockchain_relevance=enriched['relevance_score'],
                    technical_depth=0.8,  # High for strategic accounts
                    opportunity_type="strategic_account",
                    suggested_response_type="technical_insight",
                    time_sensitivity="high",
                    strategic_context=f"Strategic Tier {enriched.get('tier', 2)} Account",
                    suggested_response=enriched.get('ai_content', {}).get('primary', ''),
                    generated_reply=enriched.get('ai_content', {}).get('primary', ''),
                    reply_reasoning="High-value strategic account engagement",
                    alternative_responses=[
                        enriched.get('ai_content', {}).get('alt1', ''),
                        enriched.get('ai_content', {}).get('alt2', '')
                    ],
                    confidence_score=enriched.get('ai_content', {}).get('confidence', 0.9),
                    voice_alignment_score=enriched.get('ai_content', {}).get('voice_alignment', 0.85)
                )
                alert_opportunities.append(alert_opp)
                
            return alert_opportunities
            
        except Exception as e:
            logger.error(f"Strategic account monitoring error: {e}")
            return []
    
    async def run(self):
        """Main monitoring loop"""
        logger.info("🚀 Starting 24/7 X Engagement Bot Service (Fixed Rate Limiting)")
        
        # Start health server
        self.health_server.start()
        
        # Feedback endpoints now handled by health server on port 8080
        logger.info("✅ Feedback endpoints enabled on main health server (port 8080)")
        
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
    
    def run_monitoring_cycle(self):
        """Synchronous wrapper for monitoring cycle (for tests)"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.monitoring_cycle())
        finally:
            loop.close()

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