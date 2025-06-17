"""
Verify Strategic Accounts Added to Monitoring System
Quick verification without API calls to avoid rate limits
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.append('src')

def verify_strategic_accounts():
    """Verify and display all strategic accounts in the system"""
    
    print("🎯 Strategic Account Verification Report")
    print("=" * 60)
    print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load accounts from storage
    accounts_file = Path("data/strategic_accounts/accounts.json")
    
    if not accounts_file.exists():
        print("❌ No strategic accounts found")
        return
    
    try:
        with open(accounts_file, 'r') as f:
            accounts_data = json.load(f)
        
        print(f"\n📊 Total Strategic Accounts: {len(accounts_data)}")
        
        # Categorize accounts
        tier_counts = {}
        category_counts = {}
        ai_blockchain_scores = []
        
        print(f"\n📋 Account Details:")
        print("-" * 60)
        
        for username, account in accounts_data.items():
            tier = account['tier']
            category = account['category']
            ai_blockchain_focus = account['ai_blockchain_focus']
            technical_depth = account['technical_depth']
            influence_score = account['influence_score']
            
            # Count by tier and category
            tier_counts[f"Tier {tier}"] = tier_counts.get(f"Tier {tier}", 0) + 1
            category_counts[category] = category_counts.get(category, 0) + 1
            ai_blockchain_scores.append(ai_blockchain_focus)
            
            # Display account info
            tier_emoji = "🔥" if tier == 1 else "⚡" if tier == 2 else "📊"
            category_emoji = {
                'ai_blockchain': '🤖',
                'uniswap': '🦄', 
                'developers': '👨‍💻',
                'trading': '📈',
                'defi': '💰',
                'creators': '🎬'
            }.get(category, '📊')
            
            print(f"{tier_emoji} @{username:<20} {category_emoji} {category:<12} | AI x Blockchain: {ai_blockchain_focus:.2f} | Technical: {technical_depth:.2f} | Influence: {influence_score:.2f}")
        
        # Summary statistics
        print(f"\n📈 Strategic Distribution:")
        print("-" * 40)
        for tier, count in sorted(tier_counts.items()):
            print(f"   {tier}: {count} accounts")
        
        print(f"\n🎯 Category Breakdown:")
        print("-" * 40)
        for category, count in sorted(category_counts.items()):
            emoji = {
                'ai_blockchain': '🤖',
                'uniswap': '🦄',
                'developers': '👨‍💻', 
                'trading': '📈',
                'defi': '💰',
                'creators': '🎬'
            }.get(category, '📊')
            print(f"   {emoji} {category.replace('_', ' ').title()}: {count} accounts")
        
        # AI x Blockchain focus analysis
        avg_ai_blockchain = sum(ai_blockchain_scores) / len(ai_blockchain_scores)
        high_ai_focus = len([score for score in ai_blockchain_scores if score >= 0.7])
        
        print(f"\n🤖 AI x Blockchain Analysis:")
        print("-" * 40)
        print(f"   Average AI x Blockchain Focus: {avg_ai_blockchain:.2f}")
        print(f"   High AI Focus Accounts (≥0.7): {high_ai_focus}/{len(accounts_data)}")
        
        # Strategic insights
        print(f"\n🎯 Strategic Insights:")
        print("-" * 40)
        
        # Tier 1 analysis
        tier_1_accounts = [acc for acc in accounts_data.values() if acc['tier'] == 1]
        if tier_1_accounts:
            tier_1_ai_avg = sum(acc['ai_blockchain_focus'] for acc in tier_1_accounts) / len(tier_1_accounts)
            tier_1_influence_avg = sum(acc['influence_score'] for acc in tier_1_accounts) / len(tier_1_accounts)
            print(f"   🔥 Tier 1 Priority: {len(tier_1_accounts)} accounts")
            print(f"      - Avg AI x Blockchain Focus: {tier_1_ai_avg:.2f}")
            print(f"      - Avg Influence Score: {tier_1_influence_avg:.2f}")
        
        # High-value targets
        high_value = [
            (username, acc) for username, acc in accounts_data.items() 
            if acc['ai_blockchain_focus'] >= 0.7 and acc['influence_score'] >= 0.8
        ]
        
        print(f"\n🚀 High-Value Targets (AI Focus ≥0.7, Influence ≥0.8):")
        print("-" * 60)
        if high_value:
            for username, account in high_value:
                tier_emoji = "🔥" if account['tier'] == 1 else "⚡"
                print(f"   {tier_emoji} @{username} - AI: {account['ai_blockchain_focus']:.2f}, Influence: {account['influence_score']:.2f}")
        else:
            print("   No accounts meet high-value criteria")
        
        # Newly added accounts
        print(f"\n🆕 Recently Added Accounts:")
        print("-" * 40)
        
        # Based on the URLs provided, these should be the new accounts
        new_accounts = ['dabit3', 'PatrickAlphaC', 'TheCryptoLark', 'VirtualBacon0x', 'Morecryptoonl', 'AzFlin', 'saucepoint']
        found_new = []
        
        for username in new_accounts:
            if username in accounts_data:
                account = accounts_data[username]
                tier_emoji = "🔥" if account['tier'] == 1 else "⚡"
                found_new.append(username)
                print(f"   ✅ {tier_emoji} @{username} (Tier {account['tier']}, {account['category']})")
        
        if found_new:
            print(f"\n🎉 Successfully added {len(found_new)} new strategic accounts!")
        
        # Monitoring readiness
        print(f"\n🔧 Monitoring System Readiness:")
        print("-" * 40)
        print(f"   ✅ Strategic accounts database: {len(accounts_data)} accounts")
        print(f"   ✅ Tier 1 priority monitoring: {tier_counts.get('Tier 1', 0)} accounts")
        print(f"   ✅ AI x blockchain focus: {avg_ai_blockchain:.2f} average")
        print(f"   ✅ Developer community coverage: {category_counts.get('developers', 0)} accounts")
        print(f"   ✅ Uniswap ecosystem coverage: {category_counts.get('uniswap', 0)} accounts")
        
        print(f"\n🚀 System ready for enhanced AI x blockchain opportunity monitoring!")
        
        return {
            'total_accounts': len(accounts_data),
            'tier_distribution': tier_counts,
            'category_distribution': category_counts,
            'avg_ai_blockchain_focus': avg_ai_blockchain,
            'high_value_targets': len(high_value),
            'new_accounts_added': len(found_new)
        }
        
    except Exception as e:
        print(f"❌ Error reading accounts: {e}")
        return None

def main():
    """Main verification function"""
    print("🔍 Strategic Account Verification System")
    print()
    
    result = verify_strategic_accounts()
    
    if result:
        print(f"\n📊 Summary Statistics:")
        print(f"   Total Strategic Accounts: {result['total_accounts']}")
        print(f"   High-Value Targets: {result['high_value_targets']}")
        print(f"   Average AI x Blockchain Focus: {result['avg_ai_blockchain_focus']:.2f}")
        print(f"   New Accounts Added: {result['new_accounts_added']}")

if __name__ == "__main__":
    main()