# Complete API Parameters Reference

## 📝 Complete Parameter List

### 🎯 Core Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | ✅ | - | Search query |
| `max_results` | number | ❌ | 10 | Maximum number of results (1-50) |
| `search_depth` | 'basic'\|'advanced' | ❌ | 'basic' | Search depth |

### 📄 Content Control

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `include_answer` | boolean | ❌ | false | Generate AI answer |
| `include_raw_content` | boolean | ❌ | false | Include full webpage content |
| `include_images` | boolean | ❌ | false | Include image search |

### 🌐 Domain Filtering

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `include_domains` | string[] | ❌ | [] | Limit search to these domains |
| `exclude_domains` | string[] | ❌ | [] | Exclude these domains |

### ⏰ Time Range (New Feature!)

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `date_from` | string | ❌ | - | Start date (YYYY-MM-DD) |
| `date_to` | string | ❌ | - | End date (YYYY-MM-DD) |
| `days` | number | ❌ | - | Last N days (relative time) |
| `time_range` | 'day'\|'week'\|'month'\|'year'\|'all' | ❌ | - | SearXNG preset time range |

**Priority**: `date_from/date_to` > `days` > `time_range`

### 🔍 Search Control (New Feature!)

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `language` | string | ❌ | 'en' | Search language ('en', 'zh', 'ja', etc.) |
| `engines` | string[] | ❌ | ['google','bing','duckduckgo'] | Search engine list |
| `safesearch` | 0\|1\|2 | ❌ | 2 | Safe search (0=off, 1=moderate, 2=strict) |
| `categories` | string[] | ❌ | ['general'] | Search categories |

### 🤖 LLM Control (New Feature!)

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `llm_provider` | string | ❌ | (auto) | LLM provider ('openai', 'anthropic', etc.) |
| `llm_model` | string | ❌ | (auto) | Specific model ('gpt-4', 'claude-3', etc.) |
| `answer_max_tokens` | number | ❌ | - | Maximum answer length |
| `answer_temperature` | number | ❌ | - | Answer generation temperature (0-1) |
| `answer_context_size` | number | ❌ | 5 | Number of results used for answer |

### ⚡ Performance Control (New Feature!)

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `timeout` | number | ❌ | 60 | Request timeout (seconds) |
| `api_key` | string | ❌ | - | API key (optional authentication) |

---

## 📊 Response Format

```typescript
{
  "query": string,                    // Original query
  "answer": string?,                  // Generated answer (if include_answer=true)
  "follow_up_questions": string[]?,   // Follow-up question suggestions
  "images": string[]?,                // Image URLs (if include_images=true)
  "results": [
    {
      "title": string,                // Title
      "url": string,                  // URL
      "content": string,              // Summary
      "raw_content": string?,         // Full content (if include_raw_content=true)
      "score": number,                // Relevance score (0-1)
      "published_date": string?       // Publication date
    }
  ],
  "response_time": number,            // Response time (seconds)
  "metadata": {                       // Extended metadata
    "time_range": string,             // Actual time range used
    "language": string,               // Language used
    "engines_used": string[],         // Search engines used
    "llm_used": string?               // LLM model used
  }
}
```

---

## 💡 Usage Examples

### Example 1: Basic Search

```bash
curl -X POST http://localhost:3000/api/tavily \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence",
    "max_results": 10
  }'
```

### Example 2: Specific Time Range (Absolute Dates)

```bash
curl -X POST http://localhost:3000/api/tavily \
  -H "Content-Type: application/json" \
  -d '{
    "query": "COD BO6 events",
    "date_from": "2025-10-01",
    "date_to": "2025-10-10",
    "max_results": 20
  }'
```

### Example 3: Relative Time Range

```bash
curl -X POST http://localhost:3000/api/tavily \
  -H "Content-Type: application/json" \
  -d '{
    "query": "latest AI breakthroughs",
    "days": 7,
    "max_results": 15
  }'
```

### Example 4: SearXNG Preset Time Range

```bash
curl -X POST http://localhost:3000/api/tavily \
  -H "Content-Type: application/json" \
  -d '{
    "query": "tech news",
    "time_range": "week",
    "max_results": 10
  }'
```

### Example 5: Custom Search Engines and Language

```bash
curl -X POST http://localhost:3000/api/tavily \
  -H "Content-Type: application/json" \
  -d '{
    "query": "人工智能",
    "language": "zh",
    "engines": ["baidu", "bing"],
    "max_results": 10
  }'
```

### Example 6: Advanced Search + Answer Generation

```bash
curl -X POST http://localhost:3000/api/tavily \
  -H "Content-Type: application/json" \
  -d '{
    "query": "quantum computing vs classical computing",
    "search_depth": "advanced",
    "include_answer": true,
    "include_raw_content": true,
    "include_images": true,
    "max_results": 10,
    "llm_provider": "openai",
    "llm_model": "gpt-4",
    "answer_temperature": 0.7
  }'
```

### Example 7: Domain Filtering + Time Range

```bash
curl -X POST http://localhost:3000/api/tavily \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning papers",
    "include_domains": ["arxiv.org", "nature.com"],
    "date_from": "2025-01-01",
    "max_results": 20
  }'
```

### Example 8: Complete Configuration Example

```bash
curl -X POST http://localhost:3000/api/tavily \
  -H "Content-Type: application/json" \
  -d '{
    "query": "climate change solutions",
    "max_results": 15,
    "search_depth": "advanced",
    
    "date_from": "2024-01-01",
    "date_to": "2025-01-31",
    
    "include_answer": true,
    "include_raw_content": true,
    "include_images": true,
    
    "include_domains": ["nature.com", "science.org"],
    "exclude_domains": ["spam.com"],
    
    "language": "en",
    "engines": ["google", "duckduckgo"],
    "safesearch": 1,
    
    "llm_provider": "openai",
    "llm_model": "gpt-4",
    "answer_max_tokens": 500,
    "answer_temperature": 0.7,
    "answer_context_size": 10,
    
    "timeout": 120
  }'
```

---

**Open Deep Research - Powered by Perplexica**

