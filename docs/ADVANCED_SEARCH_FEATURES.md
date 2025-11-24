# Advanced Search Features

## 📋 Overview

This document explains how to implement advanced search features:
1. **Site-specific search** - Search within a specific website
2. **Time range filtering** - Limit results to a specific date range
3. **Content requirement** - Ensure results contain specific keywords

---

## 🎯 Current Capabilities

### ✅ What Works Now

1. **Basic search** - Search across the web
2. **Engine selection** - Choose which search engines to use
3. **Time range** - Currently hardcoded to "week" in the code
4. **Relevance scoring** - Results are ranked by relevance

### ❌ What's Missing

1. **Site-specific search** - No `site:` operator support
2. **Configurable time range** - Time range is hardcoded
3. **Content requirement** - No way to require specific keywords in results

---

## 🔧 Implementation Plan

### Feature 1: Site-Specific Search

**How it works:**
- SearXNG supports `site:` operator in the query string
- Example: `"年度报告 site:example.com"` searches only on example.com

**Implementation:**
- Add `site` parameter to `SearchRequest` model
- Modify query string to include `site:` operator when provided
- No changes needed to SearXNG request format

**Example Usage:**
```json
{
  "query": "年度报告",
  "site": "example.com",
  "limit": 10
}
```

**Resulting query:** `"年度报告 site:example.com"`

---

### Feature 2: Time Range Filtering

**How it works:**
- SearXNG supports `time_range` parameter with values:
  - `"day"` - Past 24 hours
  - `"week"` - Past week
  - `"month"` - Past month
  - `"year"` - Past year
  - `""` - All time (empty string)

**Current state:**
- Hardcoded to `"week"` in `crawler.py` line 380

**Implementation:**
- Add `time_range` parameter to `SearchRequest` model
- Pass it to `make_searxng_request` method
- Update `make_searxng_request` to use the parameter

**Example Usage:**
```json
{
  "query": "市场分析",
  "time_range": "month",
  "limit": 10
}
```

---

### Feature 3: Content Requirement (Must Contain)

**How it works:**
- After crawling, filter results that don't contain required keywords
- Use content matching or semantic similarity

**Implementation Options:**

**Option A: Simple Keyword Matching**
- Add `required_keywords` parameter (list of strings)
- Filter results where content doesn't contain all keywords
- Simple but may miss semantically similar content

**Option B: Semantic Similarity**
- Add `required_keywords` parameter
- Use semantic similarity to check if content matches
- More flexible but slower

**Option C: Query Enhancement**
- Add required keywords to the search query with `+` operator
- Let SearXNG handle it
- Simplest but less control

**Recommended: Option A + Option C (Hybrid)**
- Add keywords to query with `+` operator (let search engine filter)
- Also filter results after crawling (double check)

**Example Usage:**
```json
{
  "query": "市场分析",
  "required_keywords": ["2024", "季度"],
  "time_range": "month",
  "limit": 10
}
```

**Resulting query:** `"+2024 +季度 市场分析"`

---

## 📝 Code Changes Required

### 1. Update `SearchRequest` Model

**File:** `searcrawl/models.py`

```python
class SearchRequest(BaseModel):
    """Search request model."""
    
    query: str = Field(..., description="Search query string")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of results")
    disabled_engines: Optional[str] = Field(
        default=None, description="Comma-separated disabled engines"
    )
    enabled_engines: Optional[str] = Field(
        default=None, description="Comma-separated enabled engines"
    )
    include_raw_content: bool = Field(
        default=True, description="Include raw content in response"
    )
    topic: Literal["general", "news", "finance"] = Field(
        default="general", description="Search topic filter"
    )
    # NEW: Site-specific search
    site: Optional[str] = Field(
        default=None, description="Limit search to specific site (e.g., 'example.com')"
    )
    # NEW: Time range filter
    time_range: Optional[Literal["day", "week", "month", "year", ""]] = Field(
        default="week", description="Time range filter"
    )
    # NEW: Required keywords
    required_keywords: Optional[List[str]] = Field(
        default=None, description="Keywords that must appear in results"
    )
```

### 2. Update `make_searxng_request` Method

**File:** `searcrawl/crawler.py`

```python
@staticmethod
def make_searxng_request(
    query: str,
    limit: int = 10,
    disabled_engines: str = DISABLED_ENGINES,
    enabled_engines: str = ENABLED_ENGINES,
    site: Optional[str] = None,  # NEW
    time_range: str = "week",  # NEW: Make it a parameter
    required_keywords: Optional[List[str]] = None,  # NEW
) -> dict:
    """Send search request to SearXNG."""
    
    # Build query string
    search_query = query
    
    # Add site: operator if provided
    if site:
        # Remove 'site:' if already in query
        search_query = re.sub(r'site:\S+\s*', '', search_query)
        search_query = f"{search_query} site:{site}".strip()
    
    # Add required keywords with + operator
    if required_keywords:
        keywords_str = " ".join([f"+{kw}" for kw in required_keywords])
        search_query = f"{keywords_str} {search_query}".strip()
    
    form_data = {
        "q": search_query,
        "format": "json",
        "language": "zh",
        "time_range": time_range,  # Use parameter instead of hardcoded
        "safesearch": "2",
        "pageno": "1",
        "category_general": "1",
    }
    
    # ... rest of the method
```

### 3. Update API Endpoint

**File:** `searcrawl/api.py`

```python
@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    """Search API endpoint."""
    
    # Call SearXNG search engine
    response = WebCrawler.make_searxng_request(
        query=request.query,
        limit=request.limit,
        disabled_engines=request.disabled_engines or DISABLED_ENGINES,
        enabled_engines=request.enabled_engines or ENABLED_ENGINES,
        site=request.site,  # NEW
        time_range=request.time_range or "week",  # NEW
        required_keywords=request.required_keywords,  # NEW
    )
    
    # ... rest of the method
    
    # Optional: Additional filtering for required keywords
    if request.required_keywords:
        filtered_results = []
        for result in search_results:
            content_lower = (result.content + " " + result.title).lower()
            if all(kw.lower() in content_lower for kw in request.required_keywords):
                filtered_results.append(result)
        
        if filtered_results:
            search_results = filtered_results
        else:
            # If no results match, return original but with warning
            logger.warning(f"No results contain all required keywords: {request.required_keywords}")
    
    return SearchResponse(...)
```

---

## 📖 Usage Examples

### Example 1: Site-Specific Search

**Request:**
```json
{
  "query": "年度报告",
  "site": "example.com",
  "limit": 10
}
```

**What happens:**
- Searches for "年度报告" only on example.com
- Returns results only from that domain

---

### Example 2: Time Range + Site

**Request:**
```json
{
  "query": "季度报告",
  "site": "finance.example.com",
  "time_range": "month",
  "limit": 5
}
```

**What happens:**
- Searches for "季度报告" on finance.example.com
- Only returns results from the past month

---

### Example 3: Required Keywords

**Request:**
```json
{
  "query": "市场分析",
  "required_keywords": ["2024", "Q3"],
  "time_range": "year",
  "limit": 10
}
```

**What happens:**
- Searches for "+2024 +Q3 市场分析"
- Only returns results containing both "2024" and "Q3"
- Results are from the past year

---

### Example 4: All Features Combined

**Request:**
```json
{
  "query": "研究报告",
  "site": "research.example.com",
  "time_range": "month",
  "required_keywords": ["2024", "季度"],
  "limit": 10,
  "include_raw_content": true
}
```

**What happens:**
- Searches for "+2024 +季度 研究报告 site:research.example.com"
- Only past month results
- Only from research.example.com
- Must contain "2024" and "季度"

---

## ⚠️ Important Notes

### Site-Specific Search

1. **Format:** Just the domain, not `https://` or `www.`
   - ✅ Correct: `"example.com"`
   - ❌ Wrong: `"https://example.com"` or `"www.example.com"`

2. **Subdomains:** `site:example.com` includes all subdomains
   - To limit to specific subdomain: `site:subdomain.example.com`

3. **Multiple sites:** Not directly supported, but can be done with multiple queries

### Time Range

1. **Values:** `"day"`, `"week"`, `"month"`, `"year"`, or `""` (all time)

2. **Accuracy:** Depends on search engine's ability to detect dates
   - Some engines are better than others
   - May not work perfectly for all websites

3. **Custom dates:** SearXNG doesn't support custom date ranges directly
   - Would need to filter results after crawling by parsing dates

### Required Keywords

1. **Case sensitivity:** Currently case-insensitive (can be made case-sensitive)

2. **Multiple keywords:** All keywords must appear (AND logic)

3. **Performance:** Adding keywords to query is faster than filtering after

4. **Semantic matching:** Current implementation is keyword-based
   - For semantic matching, would need additional processing

---

## 🚀 Implementation Status

- [ ] Update `SearchRequest` model
- [ ] Update `make_searxng_request` method
- [ ] Update API endpoint
- [ ] Add tests
- [ ] Update documentation

---

## 🔗 Related Documents

- [Service Usage Guide](./SERVICE_USAGE_GUIDE.md)
- [API Usage](./API_USAGE.md)




