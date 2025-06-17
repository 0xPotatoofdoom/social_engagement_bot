#!/usr/bin/env python3
"""
View Feedback Analytics for Voice Evolution
Shows feedback trends, reply effectiveness, and voice learning insights
"""

import sys
import os

# Add src to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(script_dir, '..', '..', 'src')
sys.path.insert(0, src_path)

from bot.analytics.feedback_tracker import get_feedback_tracker
from datetime import datetime, timedelta
import json

def print_feedback_summary():
    """Print comprehensive feedback analytics"""
    tracker = get_feedback_tracker()
    summary = tracker.get_feedback_summary()
    
    print("🎯 X ENGAGEMENT BOT FEEDBACK ANALYTICS")
    print("=" * 60)
    print()
    
    if summary["total_feedback"] == 0:
        print("📊 No feedback data available yet.")
        print("🔄 Feedback will accumulate as you rate opportunities and track reply usage.")
        print()
        print("📧 Next email alert will include feedback tracking buttons!")
        return
    
    print(f"📊 OVERALL FEEDBACK SUMMARY")
    print(f"Total Feedback Records: {summary['total_feedback']}")
    print(f"Pending Feedback: {summary['pending_feedback']}")
    print()
    
    # Quality ratings analysis
    quality_data = summary["quality_ratings"]
    if quality_data["count"] > 0:
        print(f"⭐ OPPORTUNITY QUALITY RATINGS")
        print(f"Average Rating: {quality_data['average']:.2f}/5.0")
        print(f"Total Rated: {quality_data['count']}")
        print("Rating Distribution:")
        for rating in range(1, 6):
            count = quality_data["distribution"].get(rating, 0)
            stars = "⭐" * rating
            bar = "█" * (count * 3) if count > 0 else ""
            print(f"  {stars} ({rating}): {count:2d} {bar}")
        print()
    
    # Reply selection analysis
    reply_data = summary["reply_selections"]
    if reply_data:
        print(f"🎯 REPLY USAGE TRACKING")
        total_replies = sum(reply_data.values())
        print(f"Total Reply Selections: {total_replies}")
        print("Reply Type Usage:")
        
        reply_labels = {
            'primary': '🎯 Primary Reply',
            'alt1': '🔄 Alternative 1',
            'alt2': '🔄 Alternative 2', 
            'custom': '✏️ Custom Reply',
            'none': '❌ Not Used'
        }
        
        for reply_type, count in sorted(reply_data.items(), key=lambda x: x[1], reverse=True):
            label = reply_labels.get(reply_type, reply_type)
            percentage = (count / total_replies * 100) if total_replies > 0 else 0
            bar = "█" * int(percentage / 5) if percentage > 0 else ""
            print(f"  {label}: {count:2d} ({percentage:5.1f}%) {bar}")
        print()

def print_voice_insights():
    """Print voice evolution insights"""
    tracker = get_feedback_tracker()
    
    print(f"🧠 VOICE EVOLUTION INSIGHTS")
    print("-" * 40)
    
    # Analyze last 30 days
    insights = tracker.analyze_voice_performance(days_back=30)
    
    print(f"Analysis Period: {insights.period_analyzed}")
    print(f"Average Quality: {insights.avg_quality_rating:.2f}/5.0")
    print(f"Quality Trend: {insights.quality_trend.replace('_', ' ').title()}")
    print()
    
    if insights.primary_vs_alt_success_rate:
        print(f"📈 REPLY EFFECTIVENESS")
        success_rates = insights.primary_vs_alt_success_rate
        for reply_type, rate in sorted(success_rates.items(), key=lambda x: x[1], reverse=True):
            print(f"  {reply_type.title()}: {rate:.1%}")
        print()
    
    if insights.recommended_adjustments:
        print(f"🎯 RECOMMENDED VOICE ADJUSTMENTS")
        for i, recommendation in enumerate(insights.recommended_adjustments, 1):
            print(f"  {i}. {recommendation}")
        print()

def print_recent_feedback():
    """Print recent feedback entries"""
    tracker = get_feedback_tracker()
    
    # Get recent feedback (last 10 entries)
    recent_feedback = tracker.feedback_data[-10:] if tracker.feedback_data else []
    
    if not recent_feedback:
        print("📝 No recent feedback entries found")
        return
    
    print(f"📝 RECENT FEEDBACK ENTRIES")
    print("-" * 40)
    
    for feedback in reversed(recent_feedback):  # Most recent first
        timestamp = datetime.fromisoformat(feedback.timestamp).strftime("%m/%d %H:%M")
        
        # Quality rating display
        quality_str = ""
        if feedback.quality_rating:
            stars = "⭐" * feedback.quality_rating
            quality_str = f"Quality: {stars} ({feedback.quality_rating}/5)"
        
        # Reply selection display
        reply_str = ""
        if feedback.selected_reply_version:
            reply_labels = {
                'primary': '🎯 Primary',
                'alt1': '🔄 Alt1', 
                'alt2': '🔄 Alt2',
                'custom': '✏️ Custom',
                'none': '❌ None'
            }
            reply_str = f"Reply: {reply_labels.get(feedback.selected_reply_version, feedback.selected_reply_version)}"
        
        # Combine feedback info
        feedback_info = " | ".join([s for s in [quality_str, reply_str] if s])
        
        print(f"  {timestamp} [{feedback.opportunity_id[:8]}] {feedback_info}")
    
    print()

def main():
    """Main analytics display"""
    try:
        print_feedback_summary()
        print_voice_insights()
        print_recent_feedback()
        
        print("🔄 NEXT STEPS:")
        print("• Rate opportunities in upcoming email alerts")
        print("• Track which reply versions you actually use")
        print("• Review voice evolution recommendations")
        print("• Check analytics weekly to see improvement trends")
        print()
        print("📧 Feedback tracking is now enabled in all email alerts!")
        
    except Exception as e:
        print(f"❌ Error displaying feedback analytics: {e}")
        print("🔧 Make sure the feedback system is properly initialized.")

if __name__ == "__main__":
    main()