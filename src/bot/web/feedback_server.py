"""
Feedback Web Server for Voice Evolution Tracking
Handles HTTP endpoints for opportunity quality ratings and reply selection tracking
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import threading
import structlog

try:
    from bot.analytics.feedback_tracker import get_feedback_tracker
    from bot.utils.logging_config import get_component_logger
except ImportError:
    # Fallback for import issues
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from analytics.feedback_tracker import get_feedback_tracker
    from utils.logging_config import get_component_logger

logger = get_component_logger("feedback_server")

class FeedbackHandler(BaseHTTPRequestHandler):
    """Handle feedback HTTP requests"""
    
    def do_GET(self):
        """Handle GET requests for feedback endpoints"""
        parsed_url = urlparse(self.path)
        path_parts = parsed_url.path.strip('/').split('/')
        
        # Handle health check
        if self.path == '/health':
            self._send_health_response()
            return
        
        # Handle feedback endpoints: /feedback/{opportunity_id}/{type}/{value}
        if len(path_parts) >= 4 and path_parts[0] == 'feedback':
            opportunity_id = path_parts[1]
            feedback_type = path_parts[2]  # 'quality' or 'reply'
            value = path_parts[3]
            
            if feedback_type == 'quality':
                self._handle_quality_feedback(opportunity_id, value)
            elif feedback_type == 'reply':
                self._handle_reply_feedback(opportunity_id, value)
            else:
                self._send_error_response(400, "Invalid feedback type")
        else:
            self._send_error_response(404, "Endpoint not found")
    
    def _handle_quality_feedback(self, opportunity_id: str, rating_str: str):
        """Handle opportunity quality rating feedback"""
        try:
            rating = int(rating_str)
            if rating < 1 or rating > 5:
                self._send_error_response(400, "Rating must be between 1 and 5")
                return
            
            feedback_tracker = get_feedback_tracker()
            success = feedback_tracker.record_quality_feedback(
                opportunity_id, 
                rating, 
                reason=f"Quality rating submitted via email feedback"
            )
            
            if success:
                logger.info(
                    "quality_feedback_received",
                    opportunity_id=opportunity_id,
                    rating=rating,
                    source="email_feedback"
                )
                self._send_success_response(f"Quality rating {rating} recorded for opportunity {opportunity_id}")
            else:
                self._send_error_response(404, "Opportunity not found")
                
        except ValueError:
            self._send_error_response(400, "Invalid rating value")
        except Exception as e:
            logger.error(f"Error handling quality feedback: {e}")
            self._send_error_response(500, "Internal server error")
    
    def _handle_reply_feedback(self, opportunity_id: str, reply_type: str):
        """Handle reply selection feedback"""
        try:
            valid_reply_types = ['primary', 'alt1', 'alt2', 'custom', 'none']
            if reply_type not in valid_reply_types:
                self._send_error_response(400, f"Invalid reply type. Must be one of: {valid_reply_types}")
                return
            
            feedback_tracker = get_feedback_tracker()
            success = feedback_tracker.record_reply_selection(opportunity_id, reply_type)
            
            if success:
                logger.info(
                    "reply_feedback_received",
                    opportunity_id=opportunity_id,
                    reply_type=reply_type,
                    source="email_feedback"
                )
                
                # Create user-friendly response message
                reply_messages = {
                    'primary': "Primary reply usage recorded",
                    'alt1': "Alternative 1 reply usage recorded", 
                    'alt2': "Alternative 2 reply usage recorded",
                    'custom': "Custom reply usage recorded",
                    'none': "No reply usage recorded"
                }
                
                self._send_success_response(f"{reply_messages[reply_type]} for opportunity {opportunity_id}")
            else:
                self._send_error_response(404, "Opportunity not found")
                
        except Exception as e:
            logger.error(f"Error handling reply feedback: {e}")
            self._send_error_response(500, "Internal server error")
    
    def _send_health_response(self):
        """Send health check response"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {"status": "healthy", "service": "feedback_server"}
        self.wfile.write(json.dumps(response).encode())
    
    def _send_success_response(self, message: str):
        """Send success response with user-friendly HTML"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html_response = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Feedback Recorded</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
                .success {{ background: #d4edda; color: #155724; padding: 20px; border-radius: 8px; border: 1px solid #c3e6cb; }}
                .header {{ color: #2c3e50; margin-bottom: 20px; }}
                .button {{ background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 15px; }}
            </style>
        </head>
        <body>
            <h1 class="header">🎯 X Engagement Bot Feedback</h1>
            <div class="success">
                <h3>✅ Feedback Recorded Successfully</h3>
                <p>{message}</p>
                <p>This feedback helps improve AI x blockchain voice evolution and content quality over time.</p>
                <p><strong>Thank you for contributing to the learning system!</strong></p>
            </div>
            <a href="#" onclick="window.close()" class="button">Close Window</a>
        </body>
        </html>
        """
        
        self.wfile.write(html_response.encode())
    
    def _send_error_response(self, status_code: int, message: str):
        """Send error response with user-friendly HTML"""
        self.send_response(status_code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html_response = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Feedback Error</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
                .error {{ background: #f8d7da; color: #721c24; padding: 20px; border-radius: 8px; border: 1px solid #f5c6cb; }}
                .header {{ color: #2c3e50; margin-bottom: 20px; }}
                .button {{ background: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 15px; }}
            </style>
        </head>
        <body>
            <h1 class="header">🎯 X Engagement Bot Feedback</h1>
            <div class="error">
                <h3>❌ Feedback Error</h3>
                <p>{message}</p>
                <p>Please try again or contact support if the issue persists.</p>
            </div>
            <a href="#" onclick="window.close()" class="button">Close Window</a>
        </body>
        </html>
        """
        
        self.wfile.write(html_response.encode())
    
    def log_message(self, format, *args):
        """Override to use structured logging"""
        logger.info("http_request", message=format % args)

class FeedbackServer:
    """Web server for handling feedback HTTP requests"""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.server = None
        self.thread = None
        self.running = False
    
    def start(self):
        """Start the feedback server"""
        if self.running:
            logger.warning("Feedback server already running")
            return
        
        try:
            self.server = HTTPServer(('0.0.0.0', self.port), FeedbackHandler)
            self.thread = threading.Thread(target=self._run_server)
            self.thread.daemon = True
            self.thread.start()
            self.running = True
            
            logger.info(
                "feedback_server_started",
                port=self.port,
                endpoints=["GET /health", "GET /feedback/{id}/quality/{1-5}", "GET /feedback/{id}/reply/{type}"]
            )
            
        except Exception as e:
            logger.error(f"Failed to start feedback server: {e}")
            raise
    
    def _run_server(self):
        """Run the server in a separate thread"""
        try:
            self.server.serve_forever()
        except Exception as e:
            logger.error(f"Feedback server error: {e}")
    
    def stop(self):
        """Stop the feedback server"""
        if not self.running:
            return
        
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        
        self.running = False
        logger.info("feedback_server_stopped")
    
    def is_running(self) -> bool:
        """Check if server is running"""
        return self.running and self.thread and self.thread.is_alive()

# Global feedback server instance
_feedback_server: FeedbackServer = None

def get_feedback_server(port: int = 8080) -> FeedbackServer:
    """Get or create global feedback server instance"""
    global _feedback_server
    if _feedback_server is None:
        _feedback_server = FeedbackServer(port)
    return _feedback_server

def start_feedback_server(port: int = 8080):
    """Start the global feedback server"""
    server = get_feedback_server(port)
    if not server.is_running():
        server.start()
    return server