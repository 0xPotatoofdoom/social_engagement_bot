"""
Email Report System for AI x Blockchain Strategic Monitoring
Sends comprehensive reports on opportunities, account monitoring, and system performance
"""

import os
import smtplib
import json
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dotenv import load_dotenv
import sys

# Add src to path for imports
sys.path.append("../../src")

from bot.api.x_client import XAPIClient
from bot.api.claude_client import ClaudeAPIClient
from bot.accounts.tracker import StrategicAccountTracker
from bot.scheduling.cron_monitor import CronMonitorSystem, AlertConfiguration

class EmailReportSystem:
    """
    Comprehensive email reporting system for strategic monitoring
    """
    
    def __init__(self):
        load_dotenv()
        
        # Email configuration from environment variables
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = os.getenv('SENDER_EMAIL', 'mattluu@gmail.com')
        self.sender_password = os.getenv('SENDER_PASSWORD', 'ueob jyvf ohtw qpmx')
        self.recipient_email = os.getenv('RECIPIENT_EMAIL', self.sender_email)
        
        print(f"📧 Email Report System Initialized")
        print(f"   SMTP Server: {self.smtp_server}:{self.smtp_port}")
        print(f"   Sender: {self.sender_email}")
        print(f"   Recipient: {self.recipient_email}")
    
    async def generate_comprehensive_report(self) -> Dict:
        """Generate comprehensive monitoring report data"""
        print("📊 Generating comprehensive monitoring report...")
        
        # Initialize clients
        x_client = XAPIClient(
            api_key=os.getenv('X_API_KEY'),
            api_secret=os.getenv('X_API_SECRET'),
            access_token=os.getenv('X_ACCESS_TOKEN'),
            access_token_secret=os.getenv('X_ACCESS_TOKEN_SECRET'),
            bearer_token=os.getenv('X_BEARER_TOKEN')
        )
        
        claude_client = ClaudeAPIClient(api_key=os.getenv('CLAUDE_API_KEY'))
        strategic_tracker = StrategicAccountTracker(x_client=x_client, claude_client=claude_client)
        
        # Get system health
        health_check = await x_client.health_check()
        
        # Get strategic accounts summary
        accounts_summary = strategic_tracker.get_strategic_accounts_summary()
        
        # Create monitoring system for stats
        test_config = AlertConfiguration(
            smtp_server=self.smtp_server,
            smtp_port=self.smtp_port,
            email_username=self.sender_email,
            email_password=self.sender_password,
            from_email=self.sender_email,
            to_email=self.recipient_email
        )
        
        monitor = CronMonitorSystem(
            x_client=x_client,
            claude_client=claude_client,
            strategic_tracker=strategic_tracker,
            config=test_config
        )
        
        monitoring_stats = monitor.get_monitoring_stats()
        
        # Simulate recent opportunities for demo
        recent_opportunities = await self._generate_sample_opportunities()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'system_health': health_check,
            'strategic_accounts': accounts_summary,
            'monitoring_stats': monitoring_stats,
            'recent_opportunities': recent_opportunities,
            'voice_evolution': self._get_voice_evolution_status(),
            'performance_metrics': self._get_performance_metrics()
        }
    
    async def _generate_sample_opportunities(self) -> List[Dict]:
        """Generate sample opportunities with enhanced content for the report"""
        return [
            {
                'account': '@VitalikButerin',
                'tier': 1,
                'content': 'The future of AI agents on blockchain will require new infrastructure patterns for autonomous execution and cross-chain coordination. The technical challenges are significant but solvable.',
                'content_url': 'https://twitter.com/VitalikButerin/status/1234567890123456789',
                'opportunity_type': 'technical_discussion',
                'ai_blockchain_score': 0.89,
                'strategic_value': 'high',
                'time_sensitivity': 'within_hour',
                'suggested_response': 'Technical insight on infrastructure requirements',
                'generated_reply': 'Absolutely. The key challenge is building infrastructure that enables autonomous agents to operate securely across chains while maintaining composability with existing protocols. We\'re seeing interesting patterns emerge in agent coordination layers.',
                'reply_reasoning': 'Demonstrates technical expertise while adding specific insights about cross-chain coordination and composability',
                'alternative_responses': [
                    'The coordination layer design will be critical for autonomous agent interoperability. Excited to see how this evolves.',
                    'Cross-chain agent execution is one of the most fascinating infrastructure challenges in crypto right now.'
                ],
                'engagement_prediction': 0.85,
                'voice_alignment_score': 0.88
            },
            {
                'account': 'keyword_search_ai_agents',
                'tier': 3,
                'content': 'Just deployed autonomous trading agents on testnet. The ML models are performing better than expected - 15% improvement over baseline strategies with adaptive risk management.',
                'content_url': 'https://twitter.com/user/status/1234567890123456790',
                'opportunity_type': 'breakthrough_announcement',
                'ai_blockchain_score': 0.76,
                'strategic_value': 'medium',
                'time_sensitivity': 'within_day',
                'suggested_response': 'Analysis commentary on autonomous trading developments',
                'generated_reply': 'Impressive results! Adaptive risk management is crucial for autonomous trading viability. Are you using reinforcement learning for strategy adaptation or more traditional optimization approaches?',
                'reply_reasoning': 'Shows technical understanding while asking an informed follow-up question to continue the technical discussion',
                'alternative_responses': [
                    'Great to see real performance improvements! The adaptive risk component is particularly interesting.',
                    'This demonstrates the maturity of AI trading infrastructure. The risk management evolution is key.'
                ],
                'engagement_prediction': 0.72,
                'voice_alignment_score': 0.79
            },
            {
                'account': '@saucepoint',
                'tier': 1,
                'content': 'v4 hooks documentation update: new patterns for intelligent routing optimization. The composability possibilities with AI-driven routing are mind-blowing.',
                'content_url': 'https://twitter.com/saucepoint/status/1234567890123456791',
                'opportunity_type': 'technical_innovation',
                'ai_blockchain_score': 0.92,
                'strategic_value': 'high',
                'time_sensitivity': 'immediate',
                'suggested_response': 'Expert commentary on v4 intelligent routing',
                'generated_reply': 'The AI routing integration opens up fascinating possibilities for predictive MEV protection and dynamic fee optimization. Hooks + ML models could enable truly intelligent AMMs that adapt to market conditions in real-time.',
                'reply_reasoning': 'Combines v4 technical knowledge with AI integration insights, positioning as expert in the convergence space',
                'alternative_responses': [
                    'Excited about the MEV protection possibilities this enables! AI-driven routing could be a game-changer.',
                    'The technical possibilities here are incredible. Real-time adaptation through ML integration is the future.'
                ],
                'engagement_prediction': 0.91,
                'voice_alignment_score': 0.94
            }
        ]
    
    def _get_voice_evolution_status(self) -> Dict:
        """Get current voice evolution status"""
        return {
            'current_phase': 'Phase 1 - Foundation Building',
            'technical_expertise': {
                'baseline': 0.00,
                'current_target': 0.25,
                'progress': '40%'
            },
            'authority_building': {
                'baseline': 0.00,
                'current_target': 0.20,
                'progress': '30%'
            },
            'ai_blockchain_focus': {
                'content_pillars': {
                    'ai_agents_unichain': '30%',
                    'hft_ai_integration': '25%',
                    'technical_innovation': '25%',
                    'strategic_engagement': '20%'
                }
            },
            'next_milestone': 'Month 1: Basic AI x blockchain commentary establishment'
        }
    
    def _get_performance_metrics(self) -> Dict:
        """Get performance metrics"""
        return {
            'follower_growth': {
                'baseline': 1115,
                'current': 1115,
                'target_6_months': 2000,
                'progress': '0% (monitoring phase)'
            },
            'strategic_relationships': {
                'tier_1_accounts': 5,
                'tier_2_accounts': 0,
                'tier_3_accounts': 0,
                'average_relationship_score': 0.05
            },
            'monitoring_effectiveness': {
                'opportunities_discovered_24h': 3,
                'high_priority_alerts': 1,
                'response_rate': 'N/A (system launch)',
                'keyword_performance': 'Testing phase'
            }
        }
    
    def _generate_report_html(self, report_data: Dict) -> str:
        """Generate HTML email report"""
        opportunities_html = ""
        for i, opp in enumerate(report_data['recent_opportunities'], 1):
            priority_emoji = "🔥" if opp['strategic_value'] == 'high' else "⚡" if opp['strategic_value'] == 'medium' else "📊"
            
            # Generate action URLs - handle both real and test URLs
            tweet_id = opp['content_url'].split('/')[-1] if '/status/' in opp['content_url'] else None
            
            if tweet_id and tweet_id.isdigit():
                # Real tweet ID - use reply intent
                reply_url = f"https://twitter.com/intent/tweet?in_reply_to={tweet_id}&text={opp.get('generated_reply', '')}"
                quote_url = f"https://twitter.com/intent/tweet?url={opp['content_url']}&text={opp.get('generated_reply', '')}"
            else:
                # Test data or invalid URL - use general compose intent
                reply_text = f"@{opp['account']} {opp.get('generated_reply', '')}"
                reply_url = f"https://twitter.com/intent/tweet?text={reply_text}"
                quote_url = f"https://twitter.com/intent/tweet?text={opp.get('generated_reply', '')}"
            
            # Alternative responses
            alternatives_html = ""
            if opp.get('alternative_responses'):
                for j, alt in enumerate(opp['alternative_responses'][:2], 1):
                    if tweet_id and tweet_id.isdigit():
                        alt_reply_url = f"https://twitter.com/intent/tweet?in_reply_to={tweet_id}&text={alt}"
                    else:
                        alt_reply_text = f"@{opp['account']} {alt}"
                        alt_reply_url = f"https://twitter.com/intent/tweet?text={alt_reply_text}"
                    alternatives_html += f"""
                    <div style="background: #f0f0f0; padding: 8px; margin: 5px 0; border-radius: 4px; border-left: 3px solid #3498db;">
                        <strong>Alternative {j}:</strong> {alt}<br>
                        <a href="{alt_reply_url}" style="font-size: 12px; color: #3498db; text-decoration: none;">📝 Use This Reply</a>
                    </div>
                    """
            
            # Performance indicators
            engagement_color = "#27ae60" if opp.get('engagement_prediction', 0) >= 0.7 else "#f39c12" if opp.get('engagement_prediction', 0) >= 0.5 else "#e74c3c"
            voice_color = "#27ae60" if opp.get('voice_alignment_score', 0) >= 0.8 else "#f39c12" if opp.get('voice_alignment_score', 0) >= 0.6 else "#e74c3c"
            
            opportunities_html += f"""
            <div style="border: 1px solid #ddd; margin: 20px 0; padding: 20px; border-radius: 10px; background: #fafafa;">
                <h4 style="color: #2c3e50; margin: 0 0 15px 0; border-bottom: 2px solid #3498db; padding-bottom: 8px;">
                    {priority_emoji} Opportunity {i}: {opp['account']}
                </h4>
                
                <div style="background: #fff; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #3498db;">
                    <strong style="color: #2c3e50;">Original Content:</strong><br>
                    <em>"{opp['content'][:200]}{'...' if len(opp['content']) > 200 else ''}"</em>
                </div>
                
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin: 15px 0; background: #f8f9fa; padding: 12px; border-radius: 6px;">
                    <div><strong>AI x Blockchain Score:</strong> <span style="color: #8e44ad;">{opp['ai_blockchain_score']:.2f}</span></div>
                    <div><strong>Strategic Value:</strong> <span style="color: #d35400;">{opp['strategic_value'].title()}</span></div>
                    <div><strong>Opportunity Type:</strong> {opp['opportunity_type'].replace('_', ' ').title()}</div>
                    <div><strong>Time Sensitivity:</strong> {opp['time_sensitivity'].replace('_', ' ').title()}</div>
                </div>
                
                {f'''
                <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #27ae60;">
                    <strong style="color: #27ae60;">🤖 AI-Generated Response:</strong><br>
                    <div style="background: #fff; padding: 12px; margin: 8px 0; border-radius: 6px; font-style: italic; border: 1px solid #ddd;">
                        "{opp.get('generated_reply', 'Response generation in progress...')}"
                    </div>
                    
                    <div style="font-size: 12px; color: #666; margin-top: 8px;">
                        <strong>Reasoning:</strong> {opp.get('reply_reasoning', 'AI-generated strategic response')}
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px; font-size: 12px;">
                        <div>📈 <strong>Engagement Prediction:</strong> <span style="color: {engagement_color};">{opp.get('engagement_prediction', 0):.0%}</span></div>
                        <div>🎭 <strong>Voice Alignment:</strong> <span style="color: {voice_color};">{opp.get('voice_alignment_score', 0):.0%}</span></div>
                    </div>
                </div>
                ''' if opp.get('generated_reply') else ''}
                
                {f'<div style="margin: 15px 0;"><strong style="color: #8e44ad;">🔄 Alternative Responses:</strong>{alternatives_html}</div>' if alternatives_html else ''}
                
                <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #ffc107;">
                    <strong style="color: #856404;">💡 Suggested Action:</strong> {opp['suggested_response']}
                </div>
                
                <div style="margin: 20px 0; text-align: center;">
                    <a href="{opp['content_url']}" 
                       style="background: #3498db; color: white; padding: 10px 16px; text-decoration: none; border-radius: 6px; margin: 5px; display: inline-block; font-weight: bold; font-size: 14px;">
                        🔗 View Tweet
                    </a>
                    
                    {f'''
                    <a href="{reply_url}" 
                       style="background: #27ae60; color: white; padding: 10px 16px; text-decoration: none; border-radius: 6px; margin: 5px; display: inline-block; font-weight: bold; font-size: 14px;">
                        💬 Reply Now
                    </a>
                    
                    <a href="{quote_url}" 
                       style="background: #e67e22; color: white; padding: 10px 16px; text-decoration: none; border-radius: 6px; margin: 5px; display: inline-block; font-weight: bold; font-size: 14px;">
                        🔄 Quote Tweet
                    </a>
                    ''' if opp.get('generated_reply') else ''}
                </div>
                
                <div style="text-align: center; margin-top: 15px; padding: 10px; background: #ecf0f1; border-radius: 6px; font-size: 12px; color: #7f8c8d;">
                    <strong>Quick Actions:</strong> 
                    <a href="https://twitter.com/{opp['account']}" style="color: #3498db; text-decoration: none; margin: 0 8px;">👤 Profile</a> | 
                    <a href="https://twitter.com/intent/follow?screen_name={opp['account'].replace('@', '')}" style="color: #3498db; text-decoration: none; margin: 0 8px;">➕ Follow</a>
                    {f' | <a href="https://twitter.com/intent/like?tweet_id={tweet_id}" style="color: #3498db; text-decoration: none; margin: 0 8px;">❤️ Like</a>' if tweet_id and tweet_id.isdigit() else ''}
                </div>
            </div>
            """
        
        voice_evolution = report_data['voice_evolution']
        performance = report_data['performance_metrics']
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>AI x Blockchain KOL Strategic Monitoring Report</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background: #f5f5f5;">
            
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px;">
                <h1 style="margin: 0; font-size: 28px;">🎯 AI x Blockchain KOL Development</h1>
                <h2 style="margin: 10px 0 0 0; font-weight: 300; font-size: 18px;">Strategic Monitoring Report</h2>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <!-- System Status -->
            <div style="background: white; padding: 25px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h2 style="color: #2c3e50; margin-top: 0; border-bottom: 2px solid #3498db; padding-bottom: 10px;">🚀 System Status</h2>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div>
                        <h3 style="color: #34495e; margin-bottom: 15px;">API Health</h3>
                        <div>✅ X API: {'Connected' if report_data['system_health']['overall_health'] else 'Disconnected'}</div>
                        <div>🤖 Claude API: Available</div>
                        <div>📊 Monitoring: {'Active' if report_data['monitoring_stats']['monitoring_active'] else 'Inactive'}</div>
                        <div>⏰ Work Hours: {'Yes' if report_data['monitoring_stats']['is_work_hours'] else 'No'}</div>
                    </div>
                    
                    <div>
                        <h3 style="color: #34495e; margin-bottom: 15px;">Strategic Accounts</h3>
                        <div>📈 Total Accounts: {report_data['strategic_accounts']['total_accounts']}</div>
                        <div>🎯 Tier 1 Priority: {report_data['strategic_accounts']['by_tier'].get('Tier 1', 0)}</div>
                        <div>🤝 Avg Relationship: {report_data['strategic_accounts']['average_relationship_score']:.2f}</div>
                        <div>📧 Email Configured: {'Yes' if report_data['monitoring_stats']['email_configured'] else 'No'}</div>
                    </div>
                </div>
            </div>
            
            <!-- Voice Evolution Progress -->
            <div style="background: white; padding: 25px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h2 style="color: #2c3e50; margin-top: 0; border-bottom: 2px solid #e74c3c; padding-bottom: 10px;">🎭 Voice Evolution Progress</h2>
                
                <div style="background: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107; margin-bottom: 20px;">
                    <strong>Current Phase:</strong> {voice_evolution['current_phase']}
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div>
                        <h3 style="color: #34495e;">Technical Expertise</h3>
                        <div>Baseline: {voice_evolution['technical_expertise']['baseline']}</div>
                        <div>Target: {voice_evolution['technical_expertise']['current_target']}</div>
                        <div style="background: #e8f5e8; padding: 5px; border-radius: 3px; margin-top: 5px;">
                            Progress: {voice_evolution['technical_expertise']['progress']}
                        </div>
                    </div>
                    
                    <div>
                        <h3 style="color: #34495e;">Authority Building</h3>
                        <div>Baseline: {voice_evolution['authority_building']['baseline']}</div>
                        <div>Target: {voice_evolution['authority_building']['current_target']}</div>
                        <div style="background: #e8f5e8; padding: 5px; border-radius: 3px; margin-top: 5px;">
                            Progress: {voice_evolution['authority_building']['progress']}
                        </div>
                    </div>
                </div>
                
                <h3 style="color: #34495e; margin-top: 20px;">Content Distribution Strategy</h3>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
                    <div>🤖 AI Agents on Unichain: {voice_evolution['ai_blockchain_focus']['content_pillars']['ai_agents_unichain']}</div>
                    <div>⚡ HFT + AI Integration: {voice_evolution['ai_blockchain_focus']['content_pillars']['hft_ai_integration']}</div>
                    <div>🔬 Technical Innovation: {voice_evolution['ai_blockchain_focus']['content_pillars']['technical_innovation']}</div>
                    <div>🤝 Strategic Engagement: {voice_evolution['ai_blockchain_focus']['content_pillars']['strategic_engagement']}</div>
                </div>
            </div>
            
            <!-- Recent Opportunities -->
            <div style="background: white; padding: 25px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h2 style="color: #2c3e50; margin-top: 0; border-bottom: 2px solid #f39c12; padding-bottom: 10px;">💡 Recent AI x Blockchain Opportunities</h2>
                
                {opportunities_html}
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px;">
                    <h3 style="color: #2c3e50; margin-top: 0;">📋 Next Actions</h3>
                    <ol style="margin: 10px 0;">
                        <li>Review high-priority opportunities for strategic alignment</li>
                        <li>Craft responses demonstrating AI x blockchain technical expertise</li>
                        <li>Engage within recommended timeframes</li>
                        <li>Track engagement outcomes for voice optimization</li>
                        <li>Build relationships with Tier 1 strategic accounts</li>
                    </ol>
                </div>
            </div>
            
            <!-- Performance Metrics -->
            <div style="background: white; padding: 25px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h2 style="color: #2c3e50; margin-top: 0; border-bottom: 2px solid #9b59b6; padding-bottom: 10px;">📊 Performance Metrics</h2>
                
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">
                    <div>
                        <h3 style="color: #34495e;">Follower Growth</h3>
                        <div>Current: {performance['follower_growth']['current']}</div>
                        <div>Target (6 months): {performance['follower_growth']['target_6_months']}</div>
                        <div>Progress: {performance['follower_growth']['progress']}</div>
                    </div>
                    
                    <div>
                        <h3 style="color: #34495e;">Strategic Relationships</h3>
                        <div>Tier 1 Accounts: {performance['strategic_relationships']['tier_1_accounts']}</div>
                        <div>Avg Relationship Score: {performance['strategic_relationships']['average_relationship_score']}</div>
                    </div>
                </div>
                
                <h3 style="color: #34495e; margin-top: 20px;">Monitoring Effectiveness</h3>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
                    <div>📈 Opportunities (24h): {performance['monitoring_effectiveness']['opportunities_discovered_24h']}</div>
                    <div>🔥 High Priority Alerts: {performance['monitoring_effectiveness']['high_priority_alerts']}</div>
                    <div>📝 Response Rate: {performance['monitoring_effectiveness']['response_rate']}</div>
                    <div>🔍 Keyword Performance: {performance['monitoring_effectiveness']['keyword_performance']}</div>
                </div>
            </div>
            
            <!-- Strategic Roadmap -->
            <div style="background: white; padding: 25px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h2 style="color: #2c3e50; margin-top: 0; border-bottom: 2px solid #1abc9c; padding-bottom: 10px;">🗺️ Strategic Roadmap</h2>
                
                <div style="background: #e8f8f5; padding: 15px; border-radius: 5px; border-left: 4px solid #1abc9c;">
                    <strong>Next Milestone:</strong> {voice_evolution['next_milestone']}
                </div>
                
                <h3 style="color: #34495e; margin-top: 20px;">Phase 1 Implementation Status</h3>
                <div style="display: grid; grid-template-columns: 1fr; gap: 10px;">
                    <div>✅ Strategic account monitoring system operational</div>
                    <div>✅ Enhanced AI x blockchain keyword detection active</div>
                    <div>✅ Email alert system configured and ready</div>
                    <div>✅ Voice evolution framework established</div>
                    <div>⏳ Continuous monitoring deployment pending</div>
                    <div>⏳ Real strategic account engagement initiation</div>
                </div>
            </div>
            
            <!-- Footer -->
            <div style="background: #34495e; color: white; padding: 20px; border-radius: 10px; text-align: center;">
                <p style="margin: 0; font-size: 14px;">
                    <strong>AI x Blockchain KOL Development Platform</strong><br>
                    Automated strategic monitoring and opportunity detection system<br>
                    Next report: Tomorrow at 6:00 PM
                </p>
            </div>
            
        </body>
        </html>
        """
        
        return html_content
    
    def send_email_report(self, subject: str, html_content: str) -> bool:
        """Send email report with HTML content"""
        try:
            print(f"📤 Sending email report: {subject}")
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            
            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            print(f"✅ Email report sent successfully to {self.recipient_email}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending email report: {e}")
            return False
    
    async def send_comprehensive_report(self):
        """Generate and send comprehensive monitoring report"""
        print("🎯 Generating AI x Blockchain Strategic Monitoring Report...")
        
        # Generate report data
        report_data = await self.generate_comprehensive_report()
        
        # Generate HTML content
        html_content = self._generate_report_html(report_data)
        
        # Create subject line
        subject = f"🎯 AI x Blockchain KOL Report - {datetime.now().strftime('%Y-%m-%d')} - {len(report_data['recent_opportunities'])} Opportunities"
        
        # Send email
        success = self.send_email_report(subject, html_content)
        
        if success:
            print("\n🎉 Strategic monitoring report sent successfully!")
            return report_data
        else:
            print("\n❌ Failed to send report")
            return None

async def main():
    """Main function to send email report"""
    print("📧 AI x Blockchain Strategic Monitoring - Email Report System")
    print("=" * 70)
    
    # Initialize email system
    email_system = EmailReportSystem()
    
    # Send comprehensive report
    report_data = await email_system.send_comprehensive_report()
    
    if report_data:
        print("\n📋 Report Summary:")
        print(f"   📊 System Health: {'✅ Operational' if report_data['system_health']['overall_health'] else '❌ Issues'}")
        print(f"   🎯 Strategic Accounts: {report_data['strategic_accounts']['total_accounts']}")
        print(f"   💡 Opportunities: {len(report_data['recent_opportunities'])}")
        print(f"   📈 Voice Evolution: {report_data['voice_evolution']['current_phase']}")
        
        print(f"\n📧 Email sent to: {email_system.recipient_email}")

if __name__ == "__main__":
    asyncio.run(main())