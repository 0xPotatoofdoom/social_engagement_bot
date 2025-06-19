# DigitalOcean VPS Deployment Guide

This guide walks you through deploying the X Engagement Bot to your DigitalOcean VPS for 24/7 production operation.

## 📋 Prerequisites

### **VPS Requirements**
- **Minimum**: 1GB RAM, 1 vCPU, 25GB SSD
- **Recommended**: 2GB RAM, 2 vCPU, 50GB SSD (for analytics data growth)
- **OS**: Ubuntu 22.04 LTS or newer

### **Required Software on VPS**
- Docker and Docker Compose
- Git
- Python 3.11+ (for management scripts)

## 🚀 Step 1: Prepare Local Repository

### **Clean and Commit Changes**
```bash
# From your local machine
cd /Users/matt/Dev/pod_x_bot

# Commit current analytics improvements
git add .
git commit -m "Add comprehensive analytics system

- Follower growth tracking with milestone progression
- Strategic relationship analytics with response rate tracking  
- Voice evolution metrics with feedback correlation analysis
- Comprehensive growth analytics with ROI tracking
- Growth dashboard with predictions and optimization recommendations"

# Push to public repository
git push origin main
```

### **Verify .env is NOT in Repository**
```bash
# Ensure .env is not tracked
cat .gitignore | grep .env
# Should show: .env

# Double-check no sensitive data
git log --oneline -n 5 | grep -i "env\|key\|secret" || echo "✅ No sensitive data in recent commits"
```

## 🔧 Step 2: VPS Setup

### **SSH to Your DigitalOcean VPS**
```bash
ssh root@your-vps-ip
# or
ssh your-username@your-vps-ip
```

### **Install Dependencies**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
sudo systemctl enable docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Git and Python
sudo apt install -y git python3 python3-pip python3-venv

# Logout and login again to apply Docker group changes
exit
ssh root@your-vps-ip  # or your username
```

### **Verify Installation**
```bash
docker --version
docker-compose --version
python3 --version
```

## 📥 Step 3: Deploy Application

### **Clone Repository**
```bash
# Create application directory
sudo mkdir -p /opt/x_engagement_bot
sudo chown $USER:$USER /opt/x_engagement_bot
cd /opt/x_engagement_bot

# Clone the repository
git clone https://github.com/0xPotatoofdoom/social_engagement_bot.git .
```

### **Create Environment Configuration**
```bash
# Copy environment template
cp .env.example .env

# Edit with your actual API keys
nano .env
```

**Fill in your actual values:**
```bash
# X API Pro Tier ($200/month) - REQUIRED
X_API_KEY=your_actual_api_key
X_API_SECRET=your_actual_api_secret
X_ACCESS_TOKEN=your_actual_access_token
X_ACCESS_TOKEN_SECRET=your_actual_access_token_secret
X_BEARER_TOKEN=your_actual_bearer_token

# Claude AI Integration - REQUIRED
CLAUDE_API_KEY=your_actual_claude_api_key

# Email Alert System - REQUIRED
SENDER_EMAIL=your_gmail_address
SENDER_PASSWORD=your_gmail_app_password
RECIPIENT_EMAIL=your_notification_email

# Production Settings
PYTHONPATH=/app/src
PYTHONUNBUFFERED=1
TZ=America/New_York

# Feedback URL Configuration (Replace with your VPS IP)
FEEDBACK_BASE_URL=http://your-vps-ip:8080
```

**Important**: Replace `your-vps-ip` with your actual VPS IP address. This URL will be used in email alerts for feedback buttons.

### **Set Proper Permissions**
```bash
# Secure the environment file
chmod 600 .env

# Make deployment script executable
chmod +x deployment/quick_deploy.py
```

## 🐳 Step 4: Build and Start Services

### **Build Docker Container**
```bash
# Build the production container
docker build -f deployment/Dockerfile.engagement -t x_engagement_bot .
```

### **Start the Bot**
```bash
# Start in detached mode
docker run -d \
  --name x_engagement_bot \
  --restart unless-stopped \
  -p 8080:8080 \
  --env-file .env \
  -v /opt/x_engagement_bot/data:/app/data \
  -v /opt/x_engagement_bot/logs:/app/logs \
  x_engagement_bot
```

### **Verify Deployment**
```bash
# Check container status
docker ps | grep x_engagement_bot

# Check logs
docker logs -f x_engagement_bot

# Test health endpoint
curl http://localhost:8080/health

# Check for successful startup
docker logs x_engagement_bot | grep "24/7 X Engagement Bot Service"
```

## 📊 Step 5: Setup Monitoring

### **Create Management Script**
```bash
# Create management script
cat > /opt/x_engagement_bot/manage.sh << 'EOF'
#!/bin/bash

case "$1" in
  start)
    docker start x_engagement_bot
    echo "✅ X Engagement Bot started"
    ;;
  stop)
    docker stop x_engagement_bot
    echo "🛑 X Engagement Bot stopped"
    ;;
  restart)
    docker restart x_engagement_bot
    echo "🔄 X Engagement Bot restarted"
    ;;
  status)
    docker ps | grep x_engagement_bot || echo "❌ Bot not running"
    ;;
  logs)
    docker logs -f x_engagement_bot
    ;;
  analytics)
    docker exec x_engagement_bot python -c "from src.analytics.growth_dashboard import GrowthDashboard; import json; d=GrowthDashboard(); print(json.dumps(d.get_growth_overview(), indent=2, default=str))"
    ;;
  health)
    curl -s http://localhost:8080/health || echo "❌ Health check failed"
    ;;
  update)
    git pull
    docker build -f deployment/Dockerfile.engagement -t x_engagement_bot .
    docker stop x_engagement_bot
    docker rm x_engagement_bot
    docker run -d --name x_engagement_bot --restart unless-stopped -p 8080:8080 --env-file .env -v /opt/x_engagement_bot/data:/app/data -v /opt/x_engagement_bot/logs:/app/logs x_engagement_bot
    echo "🚀 Bot updated and restarted"
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status|logs|analytics|health|update}"
    exit 1
    ;;
esac
EOF

chmod +x /opt/x_engagement_bot/manage.sh
```

### **Setup System Monitoring**
```bash
# Create systemd service for auto-recovery
sudo cat > /etc/systemd/system/x-engagement-bot.service << 'EOF'
[Unit]
Description=X Engagement Bot Container
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/docker start x_engagement_bot
ExecStop=/usr/bin/docker stop x_engagement_bot
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Enable service
sudo systemctl enable x-engagement-bot.service
sudo systemctl daemon-reload
```

### **Setup Log Rotation**
```bash
# Create logrotate configuration
sudo cat > /etc/logrotate.d/x-engagement-bot << 'EOF'
/opt/x_engagement_bot/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
    postrotate
        docker kill -s USR1 x_engagement_bot
    endscript
}
EOF
```

## 🔐 Step 6: Security Configuration

### **Setup Firewall**
```bash
# Configure UFW firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 8080/tcp  # For health checks
sudo ufw reload
```

### **Setup Automated Updates**
```bash
# Install unattended upgrades
sudo apt install -y unattended-upgrades

# Configure automatic security updates
sudo dpkg-reconfigure -plow unattended-upgrades
```

### **Backup Script**
```bash
# Create backup script
cat > /opt/x_engagement_bot/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/x_engagement_bot"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup data and configuration
tar -czf $BACKUP_DIR/x_engagement_bot_backup_$DATE.tar.gz \
  /opt/x_engagement_bot/data \
  /opt/x_engagement_bot/.env \
  /opt/x_engagement_bot/logs

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "✅ Backup completed: x_engagement_bot_backup_$DATE.tar.gz"
EOF

chmod +x /opt/x_engagement_bot/backup.sh

# Add to daily cron
echo "0 2 * * * /opt/x_engagement_bot/backup.sh" | sudo crontab -
```

## 📱 Step 7: Monitoring and Alerts

### **Check Analytics Dashboard**
```bash
# View growth analytics
/opt/x_engagement_bot/manage.sh analytics

# Check system health
/opt/x_engagement_bot/manage.sh health

# Monitor logs in real-time
/opt/x_engagement_bot/manage.sh logs
```

### **Setup Health Check Monitoring** (Optional)
```bash
# Add health check to cron (every 5 minutes)
echo "*/5 * * * * curl -f http://localhost:8080/health > /dev/null 2>&1 || echo 'X Engagement Bot health check failed' | mail -s 'Bot Alert' your-email@domain.com" | crontab -
```

## 🔄 Step 8: Ongoing Management

### **Common Operations**
```bash
# Check status
/opt/x_engagement_bot/manage.sh status

# View recent logs
/opt/x_engagement_bot/manage.sh logs | tail -50

# Restart if needed
/opt/x_engagement_bot/manage.sh restart

# Update to latest code
/opt/x_engagement_bot/manage.sh update

# View analytics
/opt/x_engagement_bot/manage.sh analytics
```

### **Troubleshooting**
```bash
# If container stops unexpectedly
docker logs x_engagement_bot | tail -100

# Check disk space
df -h

# Check memory usage
free -h

# Check container resource usage
docker stats x_engagement_bot
```

### **Growth Monitoring**
```bash
# Weekly analytics review
/opt/x_engagement_bot/manage.sh analytics > weekly_report_$(date +%Y%m%d).json

# Compare against baselines in data/analytics/baseline_metrics_2025-06-18.json
```

## ✅ Deployment Complete!

Your X Engagement Bot is now running 24/7 on DigitalOcean with:

- **🔄 Automatic restarts** on failure
- **📊 Comprehensive analytics** tracking growth toward your targets
- **🛡️ Security hardening** with firewall and updates
- **📱 Health monitoring** and alerting
- **💾 Automated backups** of data and configuration
- **🚀 Easy management** with the management script

**Next Steps:**
1. Monitor first 24 hours of operation
2. Review analytics dashboard daily
3. Track progress toward 700+ follower target by September
4. Optimize based on analytics insights

The bot will now systematically work toward your growth targets with full analytics tracking! 🎯