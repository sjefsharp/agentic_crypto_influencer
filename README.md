# 🤖 Agentic Crypto Influencer Bot

[![CI](https://github.com/sjefsharp/agentic_crypto_influencer/actions/workflows/ci.yml/badge.svg)](https://github.com/sjefsharp/agentic_crypto_influencer/actions/workflows/ci.yml)
[![Validate Workflows](https://github.com/sjefsharp/agentic_crypto_influencer/actions/workflows/validate-workflows.yml/badge.svg)](https://github.com/sjefsharp/agentic_crypto_influencer/actions/workflows/validate-workflows.yml)
[![Coverage](https://codecov.io/gh/sjefsharp/agentic_crypto_influencer/branch/main/graph/badge.svg)](https://codecov.io/gh/sjefsharp/agentic_crypto_influencer)
[![Python](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Poetry](https://img.shields.io/badge/poetry-dependency%20management-blue.svg)](https://python-poetry.org/)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Security: Bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![Type Checker: MyPy](https://img.shields.io/badge/type%20checker-mypy-blue.svg)](https://mypy-lang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent, multi-agent crypto content creation system that autonomously researches, analyzes, and publishes cryptocurrency content to social media platforms.

## 🌟 Overview

This project implements a sophisticated agentic AI system that operates as an autonomous crypto influencer. It leverages a multi-agent architecture to:

- **Research** the latest crypto news and market developments
- **Analyze** market data from exchanges like Bitvavo
- **Create** engaging, Twitter-optimized content
- **Publish** automatically to X (Twitter) and other social platforms

## 🏗️ Architecture

### Multi-Agent System

The bot uses **Microsoft AutoGen** framework with a graph-based workflow:

```
SearchAgent → SummaryAgent → PublishAgent
```

#### 🔍 **SearchAgent**

- Hunts for breaking crypto news from the last 24 hours
- Prioritizes major price movements, launches, regulations, and security incidents
- Uses Google Grounding Tool for real-time information gathering
- Outputs structured JSON with categorized news

#### 📝 **SummaryAgent**

- Transforms raw news into tweet-ready content
- Ensures content stays under 280 characters
- Maintains professional, neutral tone for crypto-savvy audience
- Includes strategic hashtags and emojis

#### 🚀 **PublishAgent**

- Handles multi-platform publishing (X/Twitter, Threads)
- Manages OAuth authentication flows
- Validates content before posting
- Provides posting analytics and error handling

### 🛠️ Tool Ecosystem

#### **Social Media Tools** (`tools/social_media/`)

- **X Integration**: Full Twitter API v2 support with OAuth 2.0
- **Threads Support**: Meta Threads API integration
- **OAuth Handler**: Secure authentication management
- **Post Handler**: Cross-platform posting utilities

#### **Market Data Tools** (`tools/market_data/`)

- **Bitvavo Handler**: Real-time crypto exchange data
- **Trends Handler**: Market trend analysis
- **Google Grounding Tool**: Real-time web search capabilities

#### **Infrastructure** (`tools/infrastructure/`)

- **Redis Handler**: State persistence and caching
- **Callback Server**: OAuth callback management

#### **Utilities** (`tools/utilities/`)

- **Validator**: Content validation and safety checks

## 🚀 Getting Started

### Prerequisites

- Python 3.13+
- Poetry for dependency management
- Redis server (for state persistence)
- API keys for various services

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/sjefsharp/agentic_crypto_influencer.git
   cd agentic_crypto_influencer
   ```

2. **Install dependencies**

   ```bash
   poetry install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

### Required Environment Variables

```bash
# Core AI Model
GOOGLE_GENAI_API_KEY=your_google_api_key

# X (Twitter) API
X_CLIENT_ID=your_x_client_id
X_CLIENT_SECRET=your_x_client_secret
X_REDIRECT_URI=http://localhost:3000/callback
X_USER_ID=your_x_user_id

# Threads API (optional)
THREADS_APP_ID=your_threads_app_id
THREADS_APP_SECRET=your_threads_app_secret
THREADS_ACCESS_TOKEN=your_threads_token

# Bitvavo Exchange
BITVAVO_API_KEY=your_bitvavo_key
BITVAVO_API_SECRET=your_bitvavo_secret

# Redis (optional, uses localhost:6379 by default)
REDIS_URL=redis://localhost:6379
```

### Running the Bot

```bash
poetry run python src/agentic_crypto_influencer/graphflow/graphflow.py
```

## 🔧 Configuration

### Agent Behavior

Customize agent behavior through configuration constants:

- `config/search_agent_constants.py` - News search priorities
- `config/summary_agent_constants.py` - Content creation guidelines
- `config/publish_agent_constants.py` - Publishing parameters

### Model Configuration

The system uses Google's Gemini models by default. Configure in:

- `config/model_constants.py`

## 🧪 Testing

Comprehensive test suite with 86+ tests:

```bash
# Run all tests
poetry run pytest

# Run specific test categories
poetry run pytest tests/test_agents.py
poetry run pytest tests/test_bitvavo_handler.py
poetry run pytest tests/test_x.py
```

## 📊 CI/CD

Automated GitHub Actions workflow:

- ✅ **Code Quality**: Ruff, MyPy, Bandit security scanning
- ✅ **Testing**: Full test suite with coverage
- ✅ **Validation**: Workflow validation with shellcheck

## 🔒 Security & Error Management

### Robust Error Handling

- Centralized error management system
- Comprehensive logging with structured output
- Graceful degradation for API failures

### Security Features

- Secure credential management
- Rate limiting and API quota monitoring
- Input validation and content safety checks

## 📦 Deployment

### Docker Support

```bash
# Build image
docker build -t agentic-crypto-influencer .

# Run container
docker run -d --env-file .env agentic-crypto-influencer
```

### Local Production Setup

```bash
# Install production dependencies
pip install -r requirements.txt

# Set production environment variables
export ENVIRONMENT=production

# Run with gunicorn (for web components)
gunicorn --bind 0.0.0.0:8000 wsgi:app
```

## 🔄 State Management

The system uses Redis for:

- **Workflow State**: Persistent agent conversation history
- **Rate Limiting**: API call tracking
- **Caching**: Frequently accessed data

## 📈 Monitoring & Analytics

### Structured Logging

- JSON-formatted logs for easy parsing
- Performance metrics tracking
- Error tracking and alerting

### Metrics Available

- Post engagement rates
- API response times
- Agent decision accuracy
- Content generation success rates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make changes with tests: `poetry run pytest`
4. Ensure code quality: `poetry run ruff check && poetry run mypy .`
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📋 Development Workflow

```bash
# Install pre-commit hooks
poetry run pre-commit install

# Run code quality checks
poetry run ruff check --fix
poetry run ruff format
poetry run mypy .
poetry run bandit -r src/

# Run tests with coverage
poetry run pytest --cov=src/
```

## 🐛 Troubleshooting

### Common Issues

**API Key Errors**

```bash
# Verify environment variables
poetry run python -c "from src.agentic_crypto_influencer.config.key_constants import *; print('Keys loaded')"
```

**Redis Connection Issues**

```bash
# Check Redis connection
redis-cli ping
```

**OAuth Flow Problems**

```bash
# Start callback server
poetry run python src/agentic_crypto_influencer/tools/infrastructure/callback_server.py
```

## 📚 Documentation

- **API Reference**: Auto-generated docs in `/docs`
- **Architecture Guide**: See `ARCHITECTURE.md`
- **Deployment Guide**: See `DEPLOYMENT.md`

## 🛣️ Roadmap

- [ ] **Multi-platform expansion**: Instagram, LinkedIn, TikTok
- [ ] **Advanced analytics**: Sentiment analysis, engagement prediction
- [ ] **Custom model training**: Fine-tuned models for crypto content
- [ ] **Community features**: User interaction and response handling
- [ ] **Portfolio integration**: DeFi protocol monitoring

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Sjef Jenniskens**

- GitHub: [@sjefsharp](https://github.com/sjefsharp)
- Email: 14937399+sjefsharp@users.noreply.github.com

## 🙏 Acknowledgments

- **Microsoft AutoGen**: Multi-agent framework
- **Google Gemini**: AI model capabilities
- **Bitvavo**: Crypto exchange API
- **X (Twitter)**: Social media platform APIs

---

⭐ **Star this repo** if you find it useful!

🔄 **Follow for updates** on autonomous AI agent development
