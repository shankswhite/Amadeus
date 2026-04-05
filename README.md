# Amadeus

Enterprise-grade AI Research Platform powered by Open Deep Research (ODR) and Perplexica.
[Check it here](https://aiverse.chat)

## 🎯 Overview

Amadeus is a comprehensive research automation platform that combines:
- **Open Deep Research (ODR)**: Advanced AI-powered research agent
- **Perplexica**: Intelligent search engine with web crawling
- **Azure Kubernetes Service**: Enterprise-grade deployment

## 🚀 Features

- **Deep Research Capabilities**: Multi-step research with AI-powered analysis
- **Advanced Search**: Integration with multiple search engines via Perplexica
- **Web Crawling**: Automatic content extraction from search results
- **Image Extraction**: Captures and includes images in research reports
- **Rate Limiting**: Built-in protection against API throttling
- **JWT Authentication**: Secure API access with token-based auth
- **Kubernetes Native**: Fully containerized and orchestrated

## 📦 Components

### 1. Open Deep Research (ODR)
- AI research orchestration using LangGraph
- Support for multiple LLM models (GPT-4, Claude, o4-mini)
- Configurable search depth and research parameters
- Automatic report generation with citations

### 2. Perplexica
- Meta-search aggregation via SearXNG
- Multiple search engine support (Google, Bing, DuckDuckGo, etc.)
- Built-in web content extraction
- Tavily-compatible API interface

### 3. Cloudflare Tunnel
- Secure public access to private services
- Zero-trust network architecture
- Automatic SSL/TLS termination

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│   Cloudflare Tunnel                 │
│   (Public Access)                   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Azure Kubernetes Service (AKS)    │
│   ┌─────────────────────────────┐   │
│   │  ODR                        │   │
│   │  - Research orchestration   │   │
│   │  - LangGraph runtime        │   │
│   │  - Report generation        │   │
│   └──────────┬──────────────────┘   │
│              │                       │
│   ┌──────────▼──────────────────┐   │
│   │  Perplexica                 │   │
│   │  - Search aggregation       │   │
│   │  - Web crawling             │   │
│   │  - Content extraction       │   │
│   └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Azure account with AKS access
- Docker installed
- kubectl configured
- OpenAI or Anthropic API key

### Deployment

1. **Create AKS Cluster** (see `AZURE_ENTERPRISE_DEPLOYMENT.md`)
2. **Deploy Perplexica**
3. **Deploy ODR**
4. **Configure Cloudflare Tunnel** (optional)

Detailed deployment instructions: [AZURE_ENTERPRISE_DEPLOYMENT.md](./AZURE_ENTERPRISE_DEPLOYMENT.md)

## 📖 Documentation

- **[Enterprise Deployment Guide](./AZURE_ENTERPRISE_DEPLOYMENT.md)**: Complete Azure deployment walkthrough
- **[ODR Usage Guide](./open_deep_research-main/HOW_TO_USE.md)**: How to use the research API
- **[API Parameters](./open_deep_research-main/API_PARAMETERS_COMPLETE.md)**: Complete API reference
- **[Cloudflare Tunnel Setup](./cloudflare-tunnel/README.md)**: Public access configuration

## 🔧 Configuration

### ODR Environment Variables

```bash
# LLM API Keys
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Search Configuration
USE_PERPLEXICA=true
PERPLEXICA_API_URL=http://perplexica-service/api/tavily

# Rate Limiting
SEARCH_REQUEST_DELAY=15.0
PERPLEXICA_TIMEOUT=300

# Authentication
LANGGRAPH_AUTH_SECRET=your_secret_here
JWT_SECRET=your_jwt_secret_here
```

### Perplexica Configuration

```bash
NODE_ENV=production
```

## 📊 Resource Requirements

### Minimum (Development)
- Node: 1x Standard_B2s (2 cores, 4GB RAM)
- Cost: ~$30-40/month

### Recommended (Production)
- Nodes: 2x Standard_D2s_v3 (4 cores, 8GB RAM each)
- Cost: ~$140-180/month

### Enterprise (High Availability)
- Nodes: 3x Standard_D4s_v3 (8 cores, 16GB RAM each)
- Cost: ~$320-400/month

## 🔐 Security

- **JWT Authentication**: All API endpoints protected
- **Network Policies**: Pod-to-pod communication restrictions
- **Secrets Management**: Kubernetes secrets for sensitive data
- **HTTPS/TLS**: End-to-end encryption via Cloudflare

## 🧪 Testing

Test the research API:

```bash
# Generate JWT token
python generate_jwt_token.py

# Run research query
curl -X POST https://your-domain.com/threads/create \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "Deep Researcher",
    "input": {"query": "What are the latest developments in AI?"}
  }'
```

## 🤝 Contributing

Contributions welcome! Please read our contributing guidelines first.

## 📝 License

This project builds upon:
- [Open Deep Research](https://github.com/langchain-ai/open-deep-research) - Licensed under MIT
- [Perplexica](https://github.com/ItzCrazyKns/Perplexica) - Licensed under MIT

## 🙏 Acknowledgments

- LangChain team for Open Deep Research
- Perplexica team for the excellent search engine
- Azure for reliable cloud infrastructure

## 📧 Contact

For questions and support, please open an issue.

---

**Built with ❤️ for enterprise AI research**

