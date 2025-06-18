"""Rate limiter wrapper for tests"""

class RateLimiter:
    """Rate limiter for API calls"""
    
    def __init__(self):
        self.limits = {
            'user_timeline': {'calls_made': 0, 'remaining': 1500},
            'search_tweets': {'calls_made': 0, 'remaining': 300}
        }
        
    def can_make_request(self, endpoint):
        """Check if request can be made"""
        return self.limits.get(endpoint, {}).get('remaining', 0) > 0
        
    def update_limits(self, endpoint, calls_made, remaining):
        """Update rate limits"""
        if endpoint in self.limits:
            self.limits[endpoint]['calls_made'] = calls_made
            self.limits[endpoint]['remaining'] = remaining
            
    def update_from_response(self, endpoint, response):
        """Update from API response"""
        # Mock implementation
        if endpoint in self.limits and self.limits[endpoint]['remaining'] > 0:
            self.limits[endpoint]['remaining'] -= 1
            self.limits[endpoint]['calls_made'] += 1