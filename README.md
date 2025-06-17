# Social Engagement Bot 🤖

An intelligent Twitter/X engagement bot powered by AI that monitors blockchain and AI conversations, identifies high-value opportunities, and generates contextually appropriate responses with voice evolution capabilities.

## ⚡ Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/0xPotatoofdoom/social_engagement_bot.git
   cd social_engagement_bot
   ```

2. **Set up environment**
   ```bash
   cp .env.template .env
   # Edit .env with your API credentials
   pip install -r requirements.txt
   ```

3. **Deploy with Docker**
   ```bash
   python deployment/quick_deploy.py
   ```

## 🚀 Features

### Core Capabilities
- **24/7 Monitoring**: Continuous monitoring of AI x blockchain conversations
- **Smart Filtering**: Advanced shill detection and quality scoring
- **AI-Powered Responses**: Context-aware reply generation using Claude AI
- **Voice Evolution**: Feedback system that learns and improves response quality
- **Strategic Account Tracking**: Monitor high-value thought leaders and developers

### Advanced Features
- **Email Alerts**: Real-time notifications with feedback buttons for quality rating
- **Original Content Generation**: Trending topics and unique takes
- **Comprehensive Analytics**: ROI tracking and performance metrics
- **Rate Limit Management**: Intelligent API usage optimization
- **Health Monitoring**: Container health checks and auto-recovery

## 📋 Requirements

### API Access
- **Twitter/X API Pro** ($200/month) - Required for comprehensive search
- **Claude API** - For AI content generation and analysis
- **SMTP Email** - For alert notifications

### System Requirements
- Python 3.8+
- Docker (for production deployment)
- 512MB+ RAM
- Stable internet connection

## ⚙️ Configuration

### Environment Variables
Copy `.env.template` to `.env` and configure:

```bash
# Twitter/X API Credentials
X_API_KEY=your_api_key
X_API_SECRET=your_api_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_TOKEN_SECRET=your_access_token_secret
X_BEARER_TOKEN=your_bearer_token

# Claude AI API
CLAUDE_API_KEY=your_claude_api_key

# Email Notifications
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password
RECIPIENT_EMAIL=notifications@your_domain.com
```

### Strategic Keywords
Customize monitoring keywords in `config/ai_blockchain/strategic_keywords.yaml`:
- AI agent development
- Blockchain infrastructure
- DeFi protocols
- Technical discussions

## 🐳 Deployment

### Production (Recommended)
```bash
# One-click deployment
python deployment/quick_deploy.py

# Monitor logs
docker logs -f x_engagement_bot

# Health check
curl http://localhost:8080/health
```

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v

# Start service
python x_engagement_service.py
```

## 📊 Monitoring & Analytics

### Performance Tracking
```bash
# View feedback analytics
python scripts/analysis/view_feedback_analytics.py

# ROI analysis
python scripts/analysis/roi_analysis.py

# System health report
python scripts/maintenance/send_email_report.py
```

### Email Feedback System
Each alert email includes:
- ⭐ Quality rating buttons (1-5 stars)
- 🎯 Reply usage tracking (Primary/Alt1/Alt2/Custom/None)
- 🔗 Direct action links for immediate engagement
- 📈 Voice evolution data collection

## 🧪 Testing

### Run Test Suite
```bash
# Unit tests
python -m pytest tests/unit/ -v

# Integration tests
python -m pytest tests/integration/ -v

# Live API validation
python scripts/testing/test_live_x_api.py
```

### TDD Workflow
The project follows Test-Driven Development:
1. Write failing tests first
2. Implement minimal code to pass
3. Refactor and optimize
4. Run full test suite before deployment

## 🎯 Strategy & Voice Evolution

### Voice Profile  
- **Technical Authority**: AI x blockchain expertise
- **Authentic Voice**: Crypto-native language without corporate speak
- **Quality Focus**: Substance over promotional content
- **No Hashtags**: Clean, conversational approach

### Content Strategy
- **AI Agents on Unichain** (30%): Autonomous trading, intelligent hooks
- **HFT + AI Integration** (25%): ML models, trading strategies
- **Technical Commentary** (25%): Breaking developments, analysis
- **Community Engagement** (20%): Strategic relationship building

## 📁 Project Structure

```
social_engagement_bot/
├── 🐳 deployment/          # Docker deployment scripts
├── 🔧 scripts/             # Management and analysis tools
├── 🧠 src/bot/             # Core application logic
├── ⚙️ config/              # Configuration files
├── 📊 data/                # Runtime data (gitignored)
├── 📋 logs/                # Application logs (gitignored)
├── 🧪 tests/               # Comprehensive test suite
└── 📖 docs/                # Technical documentation
```

## 🛡️ Security & Privacy

- **No API Keys in Code**: All credentials via environment variables
- **Secure Logging**: No sensitive data in logs
- **Rate Limiting**: Respect API limits and terms of service
- **Data Privacy**: Minimal data retention, no personal information storage

## 🚀 Recent Improvements

### Code Quality (June 2025)
- ✅ **Removed 1,646+ lines of dead code** for cleaner architecture
- ✅ **Enhanced filtering** with shill detection and v4/Unichain focus
- ✅ **Improved voice system** with active feedback tracking
- ✅ **Comprehensive refactoring** with full test coverage analysis

### Performance Enhancements
- 🛡️ **Advanced Shill Detection**: Multi-layer filtering for quality content
- 🎯 **Focused Opportunities**: Higher relevance thresholds (0.7+ scores)
- 📊 **Real-time Feedback**: Quality ratings improving (3+ star average)
- 🧹 **Clean Architecture**: Removed unused components for better maintainability

## 📈 Success Metrics

### Current Performance
- **Quality Detection**: High-relevance v4/Unichain opportunities
- **Email Success**: 100% delivery with comprehensive feedback (45+ pending)
- **Voice Evolution**: Active feedback system with 3+ star ratings
- **API Efficiency**: Intelligent rate limiting with <1% utilization
- **Code Quality**: Clean, maintainable architecture post-refactoring

### Strategic Objectives
- **Authority Building**: Technical thought leadership in AI x blockchain
- **Community Growth**: 75% follower increase (1,115 → 2,000+)
- **Engagement Quality**: 80%+ voice alignment with technical authority
- **ROI Optimization**: $5-50 value per high-quality opportunity

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests first (TDD approach)
4. Implement features
5. Ensure all tests pass
6. Submit pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

- **Documentation**: Complete guides in `/docs` directory
- **Issues**: Report bugs via GitHub Issues
- **Email**: Technical questions via configured email system

---

**⚡ Ready to engage with AI x blockchain conversations intelligently!**

*Built with AI-first architecture for authentic, valuable community engagement.*