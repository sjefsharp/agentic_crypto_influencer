# 🚀 Render.com Deployment Guide

This project deploys two services on Render.com:

## 📋 Services Overview

### 1. 🌐 OAuth Callback Service (Web Service)

- **Purpose**: Handles X/Twitter OAuth authentication
- **URL**: `https://crypto-influencer-oauth.onrender.com`
- **File**: `src/agentic_crypto_influencer/tools/callback_server.py`

### 2. ⏰ Crypto Influencer Scheduler (Cron Job)

- **Purpose**: Runs the main crypto news workflow every 6 hours
- **File**: `src/agentic_crypto_influencer/graphflow/graphflow.py`

## 🔧 Deployment Steps

### 1. Fork & Connect Repository

1. Fork this repository to your GitHub account
2. Connect your GitHub account to Render.com
3. Create a new "Blueprint" deployment using `render.yaml`

### 2. Configure Environment Variables

#### For OAuth Service (`crypto-influencer-oauth`):

```bash
# Redis (required)
REDIS_URL=redis://your-redis-instance

# Callback Server Configuration
CALLBACK_SERVER_HOST=0.0.0.0  # Production
CALLBACK_SERVER_PORT=10000    # Production

# X/Twitter OAuth (required)
X_CLIENT_ID=your_client_id
X_CLIENT_SECRET=your_client_secret
X_REDIRECT_URI=https://crypto-influencer-oauth.onrender.com/callback
X_SCOPES=tweet.read tweet.write users.read
```

#### For Scheduler (`crypto-influencer-scheduler`):

```bash
# All the same as OAuth service, plus:

# API Keys (required)
GOOGLE_GENAI_API_KEY=your_gemini_api_key
BITVAVO_API_KEY=your_bitvavo_key
BITVAVO_API_SECRET=your_bitvavo_secret

# X/Twitter User (required after OAuth)
X_USER_ID=your_twitter_user_id
X_ACCESS_TOKEN=extracted_from_oauth
X_REFRESH_TOKEN=extracted_from_oauth
```

### 3. OAuth Setup Process

1. **Deploy OAuth service first**
2. **Visit**: `https://crypto-influencer-oauth.onrender.com`
3. **Click**: "Authorize with X/Twitter" button
4. **Complete OAuth flow** - tokens are automatically saved to Redis
5. **Visit**: `https://crypto-influencer-oauth.onrender.com/test_authorization` to verify
6. **Copy tokens** and add them to scheduler environment variables

### 4. Deploy Scheduler

Once OAuth is complete and tokens are configured, deploy the scheduler service.

## 🌐 Service Endpoints

### OAuth Service

- `/` - Home page with authorization link
- `/callback` - OAuth callback (automatic)
- `/test_authorization` - Check stored tokens
- `/health` - Health check

### Scheduler

- Runs automatically every 6 hours
- Logs visible in Render.com dashboard

## 🔍 Monitoring

- **Logs**: Check Render.com service dashboards
- **Health**: OAuth service `/health` endpoint
- **Tokens**: OAuth service `/test_authorization` endpoint

## 🛠️ Local Development

```bash
# Install dependencies
poetry install

# Set environment variables in .env file:
CALLBACK_SERVER_HOST=127.0.0.1  # Local development
CALLBACK_SERVER_PORT=5000        # Local development
X_REDIRECT_URI=http://localhost:5000/callback  # Local callback

# Run OAuth server locally
poetry run python src/agentic_crypto_influencer/tools/callback_server.py

# Visit: http://127.0.0.1:5000 to authorize

# Run workflow once
poetry run python src/agentic_crypto_influencer/graphflow/graphflow.py
```

## ⚠️ Important Notes

1. **OAuth Tokens**: Must be obtained before scheduler will work
2. **Redis**: Required for state persistence between services
3. **API Keys**: All external APIs need valid keys configured
4. **Redirect URI**: Must match exactly in X/Twitter app settings

## 📞 Support

- Check service logs in Render.com dashboard
- Verify environment variables are set correctly
- Ensure OAuth flow is completed successfully
