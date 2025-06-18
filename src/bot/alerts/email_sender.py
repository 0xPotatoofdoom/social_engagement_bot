"""Email sender wrapper for tests"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailSender:
    """Email sender for opportunity alerts"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.sender_password = os.getenv('SENDER_PASSWORD')
        self.recipient_email = os.getenv('RECIPIENT_EMAIL')
        
    def send_opportunity_alert(self, opportunities, alert_type="strategic"):
        """Send email alert for opportunities"""
        if not opportunities:
            return False
            
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = self.sender_email
        msg['To'] = self.recipient_email
        msg['Subject'] = f'🎯 {len(opportunities)} Strategic AI x Blockchain Opportunities'
        
        # Build HTML content
        html_parts = ['<h2>Strategic Account Opportunities</h2>']
        for opp in opportunities:
            html_parts.append(f'''
            <div style="margin: 20px 0; padding: 15px; border: 1px solid #ddd;">
                <h3>{opp.get("account", "Unknown")} (Strategic Account)</h3>
                <p>{opp.get("text", "")}</p>
                <p><strong>AI Response:</strong> {opp.get("ai_content", {}).get("primary", "")}</p>
                <div>
                    <a href="#" data-opportunity-id="{opp.get("tweet_id", "")}">Rate this opportunity</a>
                </div>
            </div>
            ''')
            
        html = '<html><body>' + ''.join(html_parts) + '</body></html>'
        msg.attach(MIMEText(html, 'html'))
        
        # Send email
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Email send error: {e}")
            return False
            
    def send_html_email(self, subject, html_content):
        """Send HTML email"""
        msg = MIMEMultipart('alternative')
        msg['From'] = self.sender_email
        msg['To'] = self.recipient_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(html_content, 'html'))
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Email send error: {e}")
            return False