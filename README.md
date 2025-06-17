# 🐦 X Engagement Bot

**AI-Powered 24/7 X (Twitter) Engagement Monitoring & Automation System**

[![Status](https://img.shields.io/badge/Status-🚀%20DEPLOYED-brightgreen)]()
[![Docker](https://img.shields.io/badge/Docker-✅%20Ready-blue)]()
[![AI](https://img.shields.io/badge/AI-Claude%20API-purple)]()
[![API](https://img.shields.io/badge/X%20API-v2%20Integrated-1da1f2)]()

## 🎯 What This Bot Does

- **🔍 Strategic Monitoring**: Tracks 10 high-value X accounts for engagement opportunities
- **🤖 AI Content Generation**: Creates contextual replies using Claude API with voice alignment
- **📧 Smart Email Alerts**: Sends opportunities with AI-generated responses and one-click action links
- **💰 ROI Tracking**: Measures engagement value to justify API upgrade investments
- **⚡ Intelligent Rate Limiting**: Maximizes free tier API efficiency with exponential backoff
- **📊 Performance Analytics**: Tracks conversion rates, voice consistency, and strategic value

## 🚀 Quick Start

### Deploy 24/7 Monitoring
```bash
# Clone and setup
git clone [repo-url]
cd pod_x_bot
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Deploy the bot
python quick_deploy.py

# Monitor activity
docker logs -f x_engagement_bot
```

### Test Locally First
```bash
# Test email alerts
python test_enhanced_email.py

# Check system health
python test_local_monitoring.py

# Verify accounts
python verify_strategic_accounts.py
```

## 📧 Email Alert System

The bot sends intelligent email alerts with:

- **🔥 Immediate Alerts** (Score ≥ 0.8): High-priority opportunities from Tier 1 accounts
- **⚡ Priority Alerts** (Score ≥ 0.6): Medium-priority strategic opportunities
- **📊 Daily Reports**: System performance and ROI metrics

Each alert includes:
- AI-generated response content with reasoning
- One-click Twitter action buttons (reply, quote, follow)
- Alternative response options
- Engagement predictions and voice alignment scores

## 🎯 Strategic Accounts (10 Total)

### Tier 1 Priority (6 accounts)
- @VitalikButerin - Ethereum thought leader
- @dabit3 - Developer advocate
- @PatrickAlphaC - Smart contract expert
- @saucepoint - Uniswap v4 contributor
- @TheCryptoLark - Crypto analyst

### Tier 2 Strategic (4 accounts)
- @VirtualBacon0x, @Morecryptoonl, @AzFlin, @TheCryptoLark

## 💰 ROI Analysis

### Current: Free Tier ($0/month)
- 300 search requests per 15 minutes
- 1,500 user timeline requests per 15 minutes
- Smart rate limiting optimization

### Target: Pro Tier ($200/month)
- 50,000 tweets per month (vs 1,500)
- Advanced analytics and insights
- Higher rate limits

### Upgrade Decision
```bash
# Generate ROI analysis
python roi_analysis.py

# Upgrade when:
# - Monthly value > $300
# - Rate limit hits > 15%
# - High conversion rate > 30%
```

## ⚙️ Management Commands

### Container Operations
```bash
# View live logs
docker logs -f x_engagement_bot

# Stop/Start/Restart
docker stop x_engagement_bot
docker start x_engagement_bot  
docker restart x_engagement_bot

# Health check
curl http://localhost:8080/health
```

### Performance Analysis
```bash
# ROI metrics
python roi_analysis.py

# System reports
python send_email_report.py

# Account verification
python verify_strategic_accounts.py
```

## 📊 Key Features

### AI-Powered Content Generation
- Contextual response creation using Claude API
- Voice alignment scoring for brand consistency
- Alternative response options for flexibility
- Engagement prediction analysis

### Intelligent Monitoring
- Strategic account activity tracking
- Keyword monitoring for trending topics
- Sentiment analysis and opportunity scoring
- Time-sensitive alert prioritization

### Production Ready
- 24/7 Docker container deployment
- Health monitoring and auto-recovery
- Comprehensive logging and metrics
- Email alert system with SMTP integration

## 🔄 Monitoring Keywords

- **Primary**: "uniswap v4", "unichain", "defi protocol"
- **AI Focus**: "ai agents", "autonomous trading", "blockchain ai"
- **Technical**: "smart contracts", "mev protection", "liquidity optimization"

## 📈 Success Metrics

After 30 days of operation, expect:

- ✅ 5+ high-quality opportunity alerts per week
- ✅ 80%+ voice alignment scores for AI-generated content  
- ✅ 2+ meaningful strategic account interactions per week
- ✅ Clear ROI data for API upgrade decision
- ✅ <10% rate limit hit rate (efficient API usage)

## 📚 Documentation

- **[Complete Guide](X_ENGAGEMENT_BOT_GUIDE.md)**: Comprehensive user manual
- **[CLAUDE.md](CLAUDE.md)**: Development reference and system status
- **[Docker Guide](DOCKER_MONITORING_GUIDE.md)**: Container deployment details

## 🛠️ Tech Stack

- **Language**: Python 3.11+
- **APIs**: X (Twitter) API v2, Claude API
- **Container**: Docker with health checks
- **Email**: SMTP with HTML templates
- **Storage**: JSON files with backup system
- **Monitoring**: Structured logging with performance metrics

## 🎯 Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  X API Client   │───▶│ Strategic Monitor │───▶│  Email Alerts   │
│ (Rate Limited)  │    │   (AI Analysis)   │    │ (Action Links)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                       │
         ▼                        ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Health Check  │    │  Claude Content  │    │   ROI Tracking  │
│   (localhost)   │    │   Generation     │    │   (Metrics)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🤝 Contributing

This is a production system for strategic X engagement. See [CLAUDE.md](CLAUDE.md) for development guidelines.

## 📄 License

Private project for strategic social media automation.

---

**🚀 Ready to automate your X engagement with AI-powered monitoring!**

For questions or issues, check the logs: `docker logs x_engagement_bot`