# SearCrawl Service Usage Guide

## 📋 Overview

This guide explains how to use SearCrawl after deployment, including:
- **Input**: What you send to the API
- **Output**: What you get back
- **Configurable Parameters**: What you can adjust

---

## 🎯 What is SearCrawl?

SearCrawl is a **search and web crawling API service** that:
1. **Searches** the web using SearXNG (metasearch engine)
2. **Crawls** the search result pages to extract content
3. **Ranks** results by relevance using hybrid scoring (BM25 + semantic similarity)
4. **Returns** structured data in Tavily-compatible format

**Think of it as:** Google Search + Web Scraper + Relevance Ranking = One API

---

## 🔗 Service Access

### After Deployment

Once deployed to Kubernetes, you can access the service via:

**Option 1: Ingress (Recommended)**
- HTTP: `http://<ingress-ip>/searcrawl`
- HTTPS: `https://your-domain.com/searcrawl`

**Option 2: Port Forward (For Testing)**
```bash
kubectl port-forward svc/searcrawl-service 3000:3000
```
- Access: `http://localhost:3000`

**Option 3: Service IP (Internal)**
- Internal cluster access: `http://searcrawl-service:3000`

---

## 📥 INPUT: What You Send

### 1. Search API (`/search`)

**Endpoint:** `POST /search`

**Request Body:**
```json
{
  "query": "Python asynchronous programming",
  "limit": 5,
  "include_raw_content": true,
  "topic": "general",
  "disabled_engines": "google__general,duckduckgo__general",
  "enabled_engines": "baidu__general"
}
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | ✅ **Yes** | - | Your search query (e.g., "Python async") |
| `limit` | integer | ❌ | 10 | Max results to return (1-50) |
| `include_raw_content` | boolean | ❌ | true | Include full page content |
| `topic` | string | ❌ | "general" | Topic filter: "general", "news", or "finance" |
| `disabled_engines` | string | ❌ | (see config) | Comma-separated list of engines to disable |
| `enabled_engines` | string | ❌ | "baidu__general" | Comma-separated list of engines to enable |

**Example Request:**
```bash
curl -X POST http://your-service/searcrawl/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning tutorials",
    "limit": 3,
    "include_raw_content": false
  }'
```

---

### 2. Crawl API (`/crawl`)

**Endpoint:** `POST /crawl`

**Request Body:**
```json
{
  "urls": [
    "https://example.com/page1",
    "https://example.com/page2"
  ],
  "instruction": "Extract main content about machine learning",
  "include_raw_content": true
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `urls` | array | ✅ **Yes** | List of URLs to crawl |
| `instruction` | string | ✅ **Yes** | What to extract (used for relevance scoring) |
| `include_raw_content` | boolean | ❌ | Include full page content (default: true) |

**Example Request:**
```bash
curl -X POST http://your-service/searcrawl/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://docs.python.org/3/library/asyncio.html"],
    "instruction": "Python async programming",
    "include_raw_content": true
  }'
```

---

### 3. Health Check (`/health`)

**Endpoint:** `GET /health`

**Request:** None

**Example:**
```bash
curl http://your-service/searcrawl/health
```

---

## 📤 OUTPUT: What You Get Back

### 1. Search API Response

**Response Format:**
```json
{
  "query": "Python asynchronous programming",
  "results": [
    {
      "title": "asyncio — Asynchronous I/O",
      "url": "https://docs.python.org/3/library/asyncio.html",
      "content": "The asyncio module provides infrastructure for writing single-threaded concurrent code using coroutines...",
      "raw_content": "Full page HTML content...",
      "score": 0.95
    },
    {
      "title": "Async/Await in Python",
      "url": "https://realpython.com/async-io-python/",
      "content": "Async IO is a concurrent programming design...",
      "raw_content": "Full page HTML content...",
      "score": 0.87
    }
  ],
  "answer": null,
  "images": [],
  "follow_up_questions": null
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `query` | string | Your original search query |
| `results` | array | List of search results |
| `results[].title` | string | Page title |
| `results[].url` | string | Page URL |
| `results[].content` | string | Content summary (extracted from page) |
| `results[].raw_content` | string | Full page content (if `include_raw_content=true`) |
| `results[].score` | float | Relevance score (0.0 to 1.0, higher = more relevant) |
| `answer` | string/null | AI-generated answer (currently null) |
| `images` | array | Image URLs (currently empty) |
| `follow_up_questions` | array/null | Suggested questions (currently null) |

**Score Explanation:**
- **0.9-1.0**: Highly relevant
- **0.7-0.9**: Relevant
- **0.5-0.7**: Somewhat relevant
- **0.0-0.5**: Less relevant

---

### 2. Crawl API Response

**Response Format:**
```json
{
  "results": [
    {
      "title": "Page Title",
      "url": "https://example.com/page",
      "content": "Extracted content...",
      "raw_content": "Full content...",
      "score": 0.85
    }
  ],
  "success_count": 1,
  "failed_urls": []
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `results` | array | Crawled results (same format as search results) |
| `success_count` | integer | Number of successfully crawled URLs |
| `failed_urls` | array | List of URLs that failed to crawl |

---

### 3. Health Check Response

**Response Format:**
```json
{
  "status": "healthy",
  "crawler_initialized": true
}
```

---

## ⚙️ Configurable Parameters

### 1. Environment Variables (Deployment Configuration)

These are set when deploying the service:

#### SearXNG Connection
```bash
SEARXNG_HOST=searxng-service      # SearXNG service hostname
SEARXNG_PORT=8080                 # SearXNG service port
SEARXNG_BASE_PATH=/search         # SearXNG API path
```

#### API Service
```bash
API_HOST=0.0.0.0                  # API bind address
API_PORT=3000                     # API port
```

#### Crawler Settings
```bash
DEFAULT_SEARCH_LIMIT=10           # Default max results
CONTENT_FILTER_THRESHOLD=0.6      # Content relevance threshold
WORD_COUNT_THRESHOLD=10           # Minimum word count for content
```

#### Search Engines
```bash
# Disabled engines (comma-separated)
DISABLED_ENGINES="google__general,duckduckgo__general,wikipedia__general,..."

# Enabled engines (comma-separated)
ENABLED_ENGINES="baidu__general"
```

**Available Search Engines:**
- `baidu__general` - Baidu search
- `google__general` - Google search
- `duckduckgo__general` - DuckDuckGo
- `bing__general` - Bing search
- `wikipedia__general` - Wikipedia
- `qwant__general` - Qwant
- `startpage__general` - Startpage
- And more...

**How to Change:**
1. Edit Kubernetes deployment YAML
2. Update environment variables
3. Restart pods: `kubectl rollout restart deployment/searcrawl`

---

### 2. Request Parameters (Per-Request Configuration)

These can be changed in each API call:

#### Search Request Parameters

**`limit`** - Control result count
```json
{
  "query": "Python",
  "limit": 5    // Get 5 results instead of default 10
}
```

**`include_raw_content`** - Control content detail
```json
{
  "query": "Python",
  "include_raw_content": false    // Only get summary, not full content
}
```

**`topic`** - Filter by topic
```json
{
  "query": "AI news",
  "topic": "news"    // Filter for news results
}
```

**`enabled_engines` / `disabled_engines`** - Control search engines
```json
{
  "query": "Python",
  "enabled_engines": "google__general,baidu__general",    // Use Google + Baidu
  "disabled_engines": "wikipedia__general"                // Exclude Wikipedia
}
```

---

## 🔧 Advanced Configuration

### 1. Relevance Scoring

The service uses **hybrid scoring** (BM25 + semantic similarity):

**How it works:**
1. **BM25** (60% weight) - Keyword matching
2. **Semantic Similarity** (40% weight) - Meaning similarity using sentence transformers

**Model:** `paraphrase-MiniLM-L6-v2` (default)

**To change scoring model:**
- Edit `searcrawl/crawler.py`
- Change `HybridScorer` model name
- Rebuild Docker image

---

### 2. Content Extraction

**What gets extracted:**
- Page title
- Main content (Markdown converted to text)
- Full raw HTML (if requested)

**Content filtering:**
- Minimum word count: `WORD_COUNT_THRESHOLD` (default: 10)
- Relevance threshold: `CONTENT_FILTER_THRESHOLD` (default: 0.6)

---

## 💻 Usage Examples

### Python Client

```python
import httpx
import asyncio

async def search_example():
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            "http://your-service/searcrawl/search",
            json={
                "query": "Python async programming",
                "limit": 5,
                "include_raw_content": True
            }
        )
        data = response.json()
        
        for result in data["results"]:
            print(f"Title: {result['title']}")
            print(f"URL: {result['url']}")
            print(f"Score: {result['score']:.2f}")
            print(f"Content: {result['content'][:100]}...")
            print()

asyncio.run(search_example())
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

async function search() {
  const response = await axios.post('http://your-service/searcrawl/search', {
    query: 'Python async programming',
    limit: 5,
    include_raw_content: true
  });
  
  response.data.results.forEach(result => {
    console.log(`Title: ${result.title}`);
    console.log(`Score: ${result.score}`);
    console.log(`URL: ${result.url}`);
  });
}

search();
```

### cURL

```bash
# Simple search
curl -X POST http://your-service/searcrawl/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Python", "limit": 3}'

# Search with specific engines
curl -X POST http://your-service/searcrawl/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning",
    "limit": 5,
    "enabled_engines": "google__general,baidu__general"
  }'

# Crawl specific URLs
curl -X POST http://your-service/searcrawl/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com"],
    "instruction": "Extract main content",
    "include_raw_content": true
  }'
```

---

## 📊 Workflow Diagram

```
User Request
    ↓
[Search API] → SearXNG → Get URLs
    ↓
[Crawl URLs] → Extract Content
    ↓
[Calculate Scores] → BM25 + Semantic Similarity
    ↓
[Rank Results] → Sort by Score
    ↓
[Return Response] → JSON with Results
```

---

## 🎯 Common Use Cases

### 1. Web Search with Content Extraction
```json
{
  "query": "latest AI research papers",
  "limit": 10,
  "include_raw_content": true
}
```

### 2. Quick Search (Summary Only)
```json
{
  "query": "Python tutorial",
  "limit": 5,
  "include_raw_content": false
}
```

### 3. Multi-Engine Search
```json
{
  "query": "weather forecast",
  "enabled_engines": "google__general,bing__general,duckduckgo__general"
}
```

### 4. Crawl Specific Pages
```json
{
  "urls": [
    "https://docs.python.org/3/",
    "https://realpython.com/"
  ],
  "instruction": "Python documentation",
  "include_raw_content": true
}
```

---

## ⚠️ Important Notes

1. **Timeout**: Search requests can take 30-120 seconds (depends on number of URLs)
2. **Rate Limiting**: No built-in rate limiting (consider adding if needed)
3. **Content Size**: `raw_content` can be large (several MB per page)
4. **Search Engines**: Some engines may be blocked or rate-limited
5. **Scoring**: Scores are relative to the query, not absolute

---

## 🔗 Related Documents

- [API Usage](./API_USAGE.md) - Detailed API examples
- [Deploy SearXNG](./DEPLOY_SEARXNG.md) - SearXNG deployment
- [Deploy SearCrawl](./DEPLOY_SEARCRAWL.md) - SearCrawl deployment
- [Ingress and HTTPS](./INGRESS_HTTPS.md) - HTTPS configuration

---

## 📝 Summary

**Input:**
- Search query or URLs to crawl
- Optional parameters (limit, engines, content detail)

**Output:**
- Structured results with title, URL, content, score
- Relevance-ranked by hybrid scoring

**Configurable:**
- Search engines (via environment or request)
- Result count (via request parameter)
- Content detail (via request parameter)
- Scoring weights (via code modification)

**Use Cases:**
- Web search with content extraction
- Research and information gathering
- Content aggregation
- Relevance-based ranking




