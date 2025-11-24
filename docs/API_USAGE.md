# SearCrawl API Usage Guide

## 📋 Overview

This guide shows how to use the SearCrawl API after deployment.

---

## 🔗 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/health` | GET | Health check |
| `/docs` | GET | Swagger UI documentation |
| `/search` | POST | Search API |
| `/crawl` | POST | Crawl API |

---

## 🚀 Quick Start

### Base URL

**If using Ingress:**
- HTTP: `http://<ingress-ip>/searcrawl`
- HTTPS: `https://your-domain.com/searcrawl`

**If using port forward:**
- `http://localhost:3000`

---

## 📖 API Examples

### 1. Health Check

```bash
curl http://<ingress-ip>/searcrawl/health
```

**Response:**
```json
{
  "status": "healthy",
  "crawler_initialized": true
}
```

### 2. Search API

```bash
curl -X POST http://<ingress-ip>/searcrawl/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python asynchronous programming",
    "limit": 5,
    "include_raw_content": true,
    "topic": "general"
  }'
```

**Response:**
```json
{
  "query": "Python asynchronous programming",
  "results": [
    {
      "title": "asyncio — Asynchronous I/O",
      "url": "https://docs.python.org/3/library/asyncio.html",
      "content": "asyncio is a library to write concurrent code...",
      "raw_content": "Full page content...",
      "score": 0.95
    }
  ],
  "answer": null,
  "images": [],
  "follow_up_questions": null
}
```

### 3. Crawl API

```bash
curl -X POST http://<ingress-ip>/searcrawl/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://docs.python.org/3/library/asyncio.html"
    ],
    "instruction": "Extract main content",
    "include_raw_content": true
  }'
```

---

## 💻 Python Client Example

```python
import httpx
import asyncio

class SearCrawlClient:
    def __init__(self, base_url: str = "http://<ingress-ip>/searcrawl"):
        self.base_url = base_url.rstrip('/')
    
    async def search(
        self,
        query: str,
        limit: int = 5,
        include_raw_content: bool = True
    ):
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/search",
                json={
                    "query": query,
                    "limit": limit,
                    "include_raw_content": include_raw_content
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def health_check(self):
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()

# Usage
async def main():
    client = SearCrawlClient()
    
    # Health check
    health = await client.health_check()
    print(f"Status: {health['status']}")
    
    # Search
    results = await client.search("Python programming", limit=3)
    for result in results["results"]:
        print(f"Title: {result['title']}")
        print(f"Score: {result['score']:.2f}")
        print()

asyncio.run(main())
```

---

## 📚 Request Parameters

### Search Request

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | ✅ | - | Search query |
| `limit` | integer | ❌ | 10 | Max results (1-50) |
| `include_raw_content` | boolean | ❌ | true | Include full content |
| `topic` | string | ❌ | "general" | Topic filter (general/news/finance) |

### Crawl Request

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `urls` | array | ✅ | List of URLs to crawl |
| `instruction` | string | ✅ | Crawl instruction/query |
| `include_raw_content` | boolean | ❌ | Include full content |

---

## 🔗 Related Documents

- [Deploy SearXNG](./DEPLOY_SEARXNG.md)
- [Deploy SearCrawl](./DEPLOY_SEARCRAWL.md)

