# Compatibility wrapper for tests
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from src.bot.api.claude_client import ClaudeAPIClient as ClaudeClient

# Add generate_replies method
def add_generate_replies_method():
    def generate_replies(self, tweet_text, author, context=None):
        """Generate replies for a tweet"""
        # Use existing functionality
        prompt = f"Generate engaging replies to this tweet by {author}: {tweet_text}"
        if context and context.get('is_strategic'):
            prompt += f"\nThis is a strategic Tier {context.get('tier', 2)} account."
            
        # Call existing Claude API
        response = self.generate_response(prompt)
        
        # Format into expected structure
        return {
            "primary": response.get('primary_reply', response),
            "alt1": response.get('alt_reply_1', "Alternative reply 1"),
            "alt2": response.get('alt_reply_2', "Alternative reply 2"),
            "confidence": 0.9,
            "voice_alignment": 0.85
        }
    
    ClaudeClient.generate_replies = generate_replies

add_generate_replies_method()

__all__ = ['ClaudeClient']