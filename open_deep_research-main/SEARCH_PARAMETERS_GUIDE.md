# Search Parameters Guide

A comprehensive guide to controlling search scope and quality with Perplexica integration.

---

## Overview

Open Deep Research integrates with Perplexica to provide powerful search capabilities. You can control **what**, **where**, **when**, and **how** to search using a rich set of parameters.

---

## Quick Reference

| Control | Parameters | Purpose |
|---------|------------|---------|
| **What to search** | `query`, `max_results`, `include_raw_content` | Define search content |
| **When to search** | `time_range`, `date_from`, `date_to`, `days` | Filter by time |
| **Where to search** | `include_domains`, `exclude_domains`, `engines` | Target specific sources |
| **How to search** | `language`, `search_depth`, `safesearch` | Control search behavior |
| **Performance** | `timeout` | Manage execution time |

---

## Core Parameters

### Query Configuration

```yaml
query: string (required)
  Description: Your search query
  Example: "Call of Duty Black Ops 7 player reviews"

max_results: integer
  Description: Maximum number of results per search
  Default: 5
  Range: 1-20
  Example: 10

include_raw_content: boolean
  Description: Include full webpage content
  Default: true
  Note: Essential for detailed analysis

topic: string
  Description: Search category
  Default: "general"
  Options: "general", "news", "finance"
```

---

## Time Range Control

Filter results by time period to get relevant, up-to-date information.

### Simple Time Ranges

```yaml
time_range: string
  Description: Preset time period
  Default: null (auto for news/finance)
  Options:
    - "day"   → Last 24 hours
    - "week"  → Last 7 days
    - "month" → Last 30 days (recommended for news)
    - "year"  → Last 12 months

days: integer
  Description: Last N days
  Example: 15 (last 15 days)
```

### Custom Date Ranges

```yaml
date_from: string (ISO 8601)
  Description: Start date
  Format: "YYYY-MM-DD"
  Example: "2024-11-01"

date_to: string (ISO 8601)
  Description: End date
  Format: "YYYY-MM-DD"
  Example: "2024-11-15"
```

### Examples

```bash
# Latest news (last 30 days)
PERPLEXICA_TIME_RANGE=month

# Specific date range
# Use direct API call for date_from/date_to

# Last 2 weeks
PERPLEXICA_DAYS=14
```

---

## Domain Filtering

Control which websites to include or exclude from search results.

### Include Specific Domains

```yaml
include_domains: list[string]
  Description: Search ONLY these domains
  Default: null (search all)
  Format: Comma-separated list
  
Examples:
  # Academic research
  PERPLEXICA_INCLUDE_DOMAINS=arxiv.org,scholar.google.com,ieee.org
  
  # Social media sentiment
  PERPLEXICA_INCLUDE_DOMAINS=reddit.com,twitter.com,news.ycombinator.com
  
  # Gaming forums
  PERPLEXICA_INCLUDE_DOMAINS=reddit.com,steampowered.com,metacritic.com
```

### Exclude Domains

```yaml
exclude_domains: list[string]
  Description: Exclude specific domains
  Default: "pinterest.com,instagram.com,tiktok.com"
  Format: Comma-separated list
  
Examples:
  # Filter out low-quality image sites
  PERPLEXICA_EXCLUDE_DOMAINS=pinterest.com,instagram.com
  
  # Exclude official marketing
  PERPLEXICA_EXCLUDE_DOMAINS=activision.com,callofduty.com
```

---

## Search Engines

Choose which search engines to use.

```yaml
engines: list[string]
  Description: Search engines to query
  Default: All available engines
  Options: "google", "bing", "duckduckgo", "brave"
  Format: Comma-separated list

Examples:
  # Use only Google and Bing
  PERPLEXICA_ENGINES=google,bing
  
  # Privacy-focused search
  PERPLEXICA_ENGINES=duckduckgo,brave
```

---

## Language Control

```yaml
language: string
  Description: Search language
  Default: "en"
  Common options:
    - "en"  → English
    - "zh"  → Chinese
    - "ja"  → Japanese
    - "ko"  → Korean
    - "es"  → Spanish
    - "fr"  → French
    - "de"  → German

Example:
  PERPLEXICA_LANGUAGE=en
```

---

## Search Quality

### Search Depth

```yaml
search_depth: string
  Description: How deep to search
  Default: "basic"
  Options:
    - "basic"  → Fast, sufficient for most cases
    - "deep"   → Thorough, more results (slower)

Example:
  PERPLEXICA_SEARCH_DEPTH=basic
```

### Safe Search

```yaml
safesearch: string
  Description: Content filtering level
  Default: "2" (strict)
  Options:
    - "0" → Off (no filtering)
    - "1" → Moderate
    - "2" → Strict (recommended)

Example:
  PERPLEXICA_SAFESEARCH=2
```

---

## Performance Control

```yaml
timeout: integer
  Description: Maximum search time (seconds)
  Default: 300 (5 minutes)
  Range: 30-600
  Recommendation:
    - Basic search: 300 (5 min)
    - Deep search: 600 (10 min)

Example:
  PERPLEXICA_TIMEOUT=300
```

---

## Configuration Methods

### Method 1: Environment Variables (Recommended)

Best for consistent behavior across all searches.

```bash
# .env file
USE_PERPLEXICA=true
PERPLEXICA_API_URL=http://perplexica-service/api/tavily

# Time control
PERPLEXICA_TIME_RANGE=month

# Domain filtering
PERPLEXICA_EXCLUDE_DOMAINS=pinterest.com,instagram.com

# Language and quality
PERPLEXICA_LANGUAGE=en
PERPLEXICA_SAFESEARCH=2
PERPLEXICA_SEARCH_DEPTH=basic

# Performance
PERPLEXICA_TIMEOUT=300
```

### Method 2: Direct API Calls

Best for query-specific overrides.

```python
from open_deep_research.perplexica_client import AsyncPerplexicaClient

client = AsyncPerplexicaClient(base_url="http://perplexica-service/api/tavily")

results = await client.search(
    query="iPhone 15 reviews",
    max_results=10,
    time_range="month",
    include_domains=["reddit.com", "twitter.com"],
    exclude_domains=["apple.com"],
    language="en"
)
```

---

## Use Case Examples

### 🎮 Gaming Sentiment Analysis

**Goal**: Analyze recent player feedback for a game

```bash
# Configuration
PERPLEXICA_TIME_RANGE=month
PERPLEXICA_INCLUDE_DOMAINS=reddit.com,steampowered.com,metacritic.com
PERPLEXICA_EXCLUDE_DOMAINS=ign.com,gamespot.com
PERPLEXICA_LANGUAGE=en
```

**Why**:
- `time_range=month` → Recent opinions only
- `include_domains` → User-generated content
- `exclude_domains` → Avoid paid reviews
- Results: Authentic player sentiment

---

### 📰 Breaking News Research

**Goal**: Get latest news on a topic

```bash
# Configuration
PERPLEXICA_TIME_RANGE=week
PERPLEXICA_EXCLUDE_DOMAINS=pinterest.com,instagram.com
PERPLEXICA_LANGUAGE=en
PERPLEXICA_SEARCH_DEPTH=basic
```

**Why**:
- `time_range=week` → Very recent news
- `exclude_domains` → No image spam
- Fast and relevant results

---

### 🎓 Academic Research

**Goal**: Find recent academic papers

```bash
# Configuration
PERPLEXICA_TIME_RANGE=year
PERPLEXICA_INCLUDE_DOMAINS=arxiv.org,scholar.google.com,ieee.org,acm.org
PERPLEXICA_LANGUAGE=en
PERPLEXICA_TIMEOUT=600
```

**Why**:
- `time_range=year` → Recent publications
- `include_domains` → Academic sources only
- `timeout=600` → Allow time for full PDFs
- Results: High-quality academic sources

---

### 🌏 Multilingual Research

**Goal**: Research in Chinese market

```bash
# Configuration
PERPLEXICA_LANGUAGE=zh
PERPLEXICA_ENGINES=baidu,bing
PERPLEXICA_TIME_RANGE=month
```

**Why**:
- `language=zh` → Chinese results
- `engines=baidu,bing` → Better for Chinese content
- Relevant for regional research

---

### 💼 Competitive Intelligence

**Goal**: Monitor competitor mentions

```bash
# Configuration
PERPLEXICA_TIME_RANGE=month
PERPLEXICA_EXCLUDE_DOMAINS=competitor-site.com
PERPLEXICA_INCLUDE_DOMAINS=reddit.com,twitter.com,news.ycombinator.com
PERPLEXICA_LANGUAGE=en
```

**Why**:
- `exclude_domains` → No official PR
- `include_domains` → Real discussions
- Get authentic market perception

---

## Parameter Priority

When parameters are set in multiple places:

```
Direct API Call > Environment Variable > Smart Default
```

**Example**:

```python
# Environment variable
os.environ['PERPLEXICA_TIME_RANGE'] = 'month'

# Direct call (overrides env var)
client.search(
    query="test",
    time_range="week"  # ← This wins
)
```

---

## Smart Defaults

The system applies intelligent defaults automatically:

| Condition | Auto-Applied Setting | Reason |
|-----------|---------------------|---------|
| `topic="news"` | `time_range="month"` | News is time-sensitive |
| `topic="finance"` | `time_range="month"` | Recent data matters |
| No domain filter | Exclude pinterest.com, instagram.com, tiktok.com | Filter low-quality sites |
| No safesearch | `safesearch="2"` | Safe by default |
| No language | `language="en"` | English default |

---

## Best Practices

### ✅ DO

- **Use time ranges** for news and trending topics
- **Filter domains** for specific source types
- **Exclude low-quality sites** (pinterest, instagram)
- **Set reasonable timeouts** (300s for basic, 600s for deep)
- **Use include_domains** for focused research

### ❌ DON'T

- Don't use very short timeouts (< 60s)
- Don't include too many domains (> 20)
- Don't forget to exclude spam sites
- Don't use `search_depth=deep` unless necessary
- Don't mix incompatible parameters (e.g., `time_range` + `date_from`)

---

## Troubleshooting

### No recent results?

```bash
# Check time range setting
echo $PERPLEXICA_TIME_RANGE

# Verify it's set
PERPLEXICA_TIME_RANGE=month
```

### Unwanted domains appearing?

```bash
# Add to exclusion list
PERPLEXICA_EXCLUDE_DOMAINS=site1.com,site2.com,site3.com
```

### Timeouts occurring?

```bash
# Increase timeout
PERPLEXICA_TIMEOUT=600  # 10 minutes
```

### Wrong language results?

```bash
# Set language explicitly
PERPLEXICA_LANGUAGE=en
```

---

## Complete Example: Gaming Analysis

Let's analyze "Call of Duty Black Ops 7" player sentiment:

```bash
# .env configuration
USE_PERPLEXICA=true
PERPLEXICA_API_URL=http://perplexica-service/api/tavily

# Time: Last month of player feedback
PERPLEXICA_TIME_RANGE=month

# Sources: User communities, not official sites
PERPLEXICA_INCLUDE_DOMAINS=reddit.com,twitter.com,steampowered.com
PERPLEXICA_EXCLUDE_DOMAINS=activision.com,callofduty.com

# Quality: English language, safe search
PERPLEXICA_LANGUAGE=en
PERPLEXICA_SAFESEARCH=2
PERPLEXICA_SEARCH_DEPTH=basic

# Performance: Standard timeout
PERPLEXICA_TIMEOUT=300
```

**Expected Results**:
- ✅ Recent player opinions (last 30 days)
- ✅ From gaming communities (Reddit, Steam, Twitter)
- ✅ No official marketing content
- ✅ English language results
- ✅ Completed within 5 minutes

---

## Summary

| Parameter Category | Key Benefit | When to Use |
|-------------------|-------------|-------------|
| **Time Range** | Get relevant, timely results | News, trends, sentiment |
| **Domain Filtering** | Target specific sources | Focused research, quality control |
| **Search Engines** | Optimize for content type | Regional research, privacy |
| **Language** | Get native content | Multilingual research |
| **Search Depth** | Balance speed vs completeness | Time-critical vs thorough research |
| **Performance** | Prevent timeouts | Large-scale research |


