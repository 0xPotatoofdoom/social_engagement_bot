"""
Add Strategic Accounts to AI x Blockchain Monitoring System
Analyzes and adds new accounts with appropriate tier classification
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add src to path for imports
sys.path.append('src')

from bot.api.x_client import XAPIClient
from bot.api.claude_client import ClaudeAPIClient
from bot.accounts.tracker import StrategicAccountTracker

class StrategicAccountManager:
    """Manage strategic account additions with proper classification"""
    
    def __init__(self):
        load_dotenv()
        
        # Initialize clients
        self.x_client = XAPIClient(
            api_key=os.getenv('X_API_KEY'),
            api_secret=os.getenv('X_API_SECRET'),
            access_token=os.getenv('X_ACCESS_TOKEN'),
            access_token_secret=os.getenv('X_ACCESS_TOKEN_SECRET'),
            bearer_token=os.getenv('X_BEARER_TOKEN')
        )
        
        self.claude_client = ClaudeAPIClient(api_key=os.getenv('CLAUDE_API_KEY'))
        self.strategic_tracker = StrategicAccountTracker(
            x_client=self.x_client, 
            claude_client=self.claude_client
        )
    
    async def analyze_and_add_accounts(self, account_list):
        """Analyze and add accounts with strategic classification"""
        
        # Strategic accounts with analysis
        strategic_accounts = [
            {
                'username': 'dabit3',
                'display_name': 'Nader Dabit',
                'tier': 1,
                'category': 'developers',
                'analysis': {
                    'focus': 'Full-stack blockchain development, developer education',
                    'ai_blockchain_relevance': 'High - covers AI/ML integration with blockchain',
                    'influence': 'Very high - major developer community influence',
                    'content_type': 'Technical tutorials, developer tools, blockchain education'
                },
                'classification': {
                    'influence_score': 0.95,
                    'relevance_score': 0.85,
                    'engagement_potential': 0.90,
                    'technical_depth': 0.90,
                    'ai_blockchain_focus': 0.70
                }
            },
            {
                'username': 'PatrickAlphaC',
                'display_name': 'Patrick Collins',
                'tier': 1,
                'category': 'developers',
                'analysis': {
                    'focus': 'Smart contract security, blockchain education, Chainlink',
                    'ai_blockchain_relevance': 'High - covers AI oracles and smart contract automation',
                    'influence': 'Very high - massive educational following',
                    'content_type': 'Educational content, security analysis, development tutorials'
                },
                'classification': {
                    'influence_score': 0.92,
                    'relevance_score': 0.88,
                    'engagement_potential': 0.95,
                    'technical_depth': 0.95,
                    'ai_blockchain_focus': 0.75
                }
            },
            {
                'username': 'TheCryptoLark',
                'display_name': 'Lark Davis',
                'tier': 2,
                'category': 'creators',
                'analysis': {
                    'focus': 'Crypto market analysis, project reviews, educational content',
                    'ai_blockchain_relevance': 'Medium - covers AI crypto projects and trends',
                    'influence': 'High - large content creator following',
                    'content_type': 'Market analysis, project reviews, trend commentary'
                },
                'classification': {
                    'influence_score': 0.85,
                    'relevance_score': 0.65,
                    'engagement_potential': 0.80,
                    'technical_depth': 0.60,
                    'ai_blockchain_focus': 0.50
                }
            },
            {
                'username': 'VirtualBacon0x',
                'display_name': 'Virtual Bacon',
                'tier': 2,
                'category': 'defi',
                'analysis': {
                    'focus': 'DeFi analysis, yield farming, protocol deep dives',
                    'ai_blockchain_relevance': 'Medium-High - covers automated strategies and AI tools',
                    'influence': 'Medium-High - strong DeFi community presence',
                    'content_type': 'DeFi analysis, yield strategies, protocol reviews'
                },
                'classification': {
                    'influence_score': 0.75,
                    'relevance_score': 0.75,
                    'engagement_potential': 0.70,
                    'technical_depth': 0.80,
                    'ai_blockchain_focus': 0.60
                }
            },
            {
                'username': 'Morecryptoonl',
                'display_name': 'MoreCrypto Online',
                'tier': 2,
                'category': 'creators',
                'analysis': {
                    'focus': 'Crypto news, market analysis, project coverage',
                    'ai_blockchain_relevance': 'Medium - covers AI crypto developments',
                    'influence': 'Medium - growing crypto content creator',
                    'content_type': 'News analysis, market commentary, project reviews'
                },
                'classification': {
                    'influence_score': 0.70,
                    'relevance_score': 0.60,
                    'engagement_potential': 0.65,
                    'technical_depth': 0.55,
                    'ai_blockchain_focus': 0.45
                }
            },
            {
                'username': 'AzFlin',
                'display_name': 'Azflin',
                'tier': 2,
                'category': 'defi',
                'analysis': {
                    'focus': 'DeFi protocols, yield farming, on-chain analysis',
                    'ai_blockchain_relevance': 'Medium - covers automated strategies',
                    'influence': 'Medium - active DeFi community member',
                    'content_type': 'DeFi strategies, protocol analysis, on-chain data'
                },
                'classification': {
                    'influence_score': 0.65,
                    'relevance_score': 0.70,
                    'engagement_potential': 0.60,
                    'technical_depth': 0.75,
                    'ai_blockchain_focus': 0.50
                }
            },
            {
                'username': 'saucepoint',
                'display_name': 'saucepoint',
                'tier': 1,
                'category': 'uniswap',
                'analysis': {
                    'focus': 'Uniswap v4 development, hooks, AMM innovation',
                    'ai_blockchain_relevance': 'Very High - v4 hooks + AI integration expert',
                    'influence': 'High - core Uniswap ecosystem contributor',
                    'content_type': 'Technical development, v4 hooks, AMM research'
                },
                'classification': {
                    'influence_score': 0.85,
                    'relevance_score': 0.95,
                    'engagement_potential': 0.80,
                    'technical_depth': 0.95,
                    'ai_blockchain_focus': 0.85
                }
            }
        ]
        
        print("🎯 Adding Strategic Accounts to AI x Blockchain Monitoring")
        print("=" * 60)
        
        added_accounts = []
        
        for account_info in strategic_accounts:
            try:
                print(f"\n📊 Analyzing @{account_info['username']}...")
                print(f"   Focus: {account_info['analysis']['focus']}")
                print(f"   AI x Blockchain Relevance: {account_info['analysis']['ai_blockchain_relevance']}")
                print(f"   Tier: {account_info['tier']} ({account_info['category']})")
                
                # Add account to strategic tracker
                account = await self.strategic_tracker.add_strategic_account(
                    username=account_info['username'],
                    tier=account_info['tier'],
                    category=account_info['category'],
                    manual_classification=account_info['classification']
                )
                
                added_accounts.append(account)
                print(f"   ✅ Added successfully")
                print(f"   - AI x Blockchain Focus: {account.ai_blockchain_focus:.2f}")
                print(f"   - Technical Depth: {account.technical_depth:.2f}")
                print(f"   - Influence Score: {account.influence_score:.2f}")
                
            except Exception as e:
                print(f"   ❌ Error adding @{account_info['username']}: {e}")
        
        return added_accounts
    
    async def generate_monitoring_summary(self):
        """Generate summary of all strategic accounts"""
        summary = self.strategic_tracker.get_strategic_accounts_summary()
        
        print(f"\n📋 Strategic Account Monitoring Summary")
        print("=" * 50)
        print(f"Total Strategic Accounts: {summary['total_accounts']}")
        print(f"By Tier: {summary['by_tier']}")
        print(f"By Category: {summary['by_category']}")
        print(f"Average Relationship Score: {summary['average_relationship_score']:.2f}")
        
        # Show detailed account list
        print(f"\n📊 Account Details:")
        for username, account in self.strategic_tracker.accounts.items():
            tier_emoji = "🔥" if account.tier == 1 else "⚡" if account.tier == 2 else "📊"
            print(f"   {tier_emoji} @{username} (Tier {account.tier}, {account.category})")
            print(f"      AI x Blockchain: {account.ai_blockchain_focus:.2f} | Technical: {account.technical_depth:.2f} | Influence: {account.influence_score:.2f}")
        
        return summary

async def main():
    """Main function to add strategic accounts"""
    print("🎯 Strategic Account Addition System")
    print("📅 Date:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    # Initialize account manager
    manager = StrategicAccountManager()
    
    # Test X API connection
    health = await manager.x_client.health_check()
    print(f"✅ X API Status: {health['overall_health']}")
    
    # Account URLs provided
    account_urls = [
        'https://x.com/dabit3',
        'https://x.com/PatrickAlphaC', 
        'https://x.com/TheCryptoLark',
        'https://x.com/VirtualBacon0x',
        'https://x.com/Morecryptoonl',
        'https://x.com/AzFlin',
        'https://x.com/saucepoint'
    ]
    
    print(f"\n📝 Processing {len(account_urls)} strategic accounts...")
    
    # Add accounts with strategic analysis
    added_accounts = await manager.analyze_and_add_accounts(account_urls)
    
    # Generate comprehensive summary
    summary = await manager.generate_monitoring_summary()
    
    print(f"\n🎉 Strategic Account Addition Complete!")
    print(f"✅ Successfully added: {len(added_accounts)} accounts")
    print(f"📊 Total accounts now monitoring: {summary['total_accounts']}")
    
    # Show strategic insights
    print(f"\n🎯 Strategic Insights:")
    
    # Tier 1 accounts (highest priority)
    tier_1_accounts = [acc for acc in manager.strategic_tracker.accounts.values() if acc.tier == 1]
    tier_1_ai_focus = sum(acc.ai_blockchain_focus for acc in tier_1_accounts) / len(tier_1_accounts) if tier_1_accounts else 0
    
    print(f"   🔥 Tier 1 Accounts: {len(tier_1_accounts)} (Average AI x Blockchain Focus: {tier_1_ai_focus:.2f})")
    print(f"   ⚡ Tier 2 Accounts: {summary['by_tier'].get('Tier 2', 0)}")
    print(f"   📈 Developer-Focused Accounts: {summary['by_category'].get('developers', 0)}")
    print(f"   🦄 Uniswap Ecosystem: {summary['by_category'].get('uniswap', 0)}")
    
    print(f"\n🚀 Ready for enhanced AI x blockchain opportunity monitoring!")

if __name__ == "__main__":
    asyncio.run(main())