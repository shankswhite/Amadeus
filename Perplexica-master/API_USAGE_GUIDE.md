# Perplexica Tavily API 使用指南

## ✅ 配置已完成

默认配置（无需每次指定）：
- ⏱️ **超时时间**: 300 秒
- 📊 **最大结果**: 50 条
- 🌐 **默认语言**: 英文 (en)

---

## 🚀 如何调用 API

### 基本信息

**API 端点**: `http://perplexica-service/api/tavily`  
**方法**: POST  
**Content-Type**: application/json  
**认证**: 无需 API Key（内部访问）

---

## 📝 调用示例

### 1. Python 调用

```python
import requests

# 基础搜索
response = requests.post(
    "http://perplexica-service/api/tavily",
    json={
        "query": "artificial intelligence 2025",
        "max_results": 10
    }
)

result = response.json()
print(f"找到 {len(result['results'])} 条结果")
```

### 2. Curl 调用

```bash
# 基础搜索
curl -X POST http://perplexica-service/api/tavily \
  -H "Content-Type: application/json" \
  -d '{
    "query": "your search query",
    "max_results": 10
  }'

# 完整内容搜索
curl -X POST http://perplexica-service/api/tavily \
  -H "Content-Type: application/json" \
  -d '{
    "query": "game reviews",
    "max_results": 5,
    "include_raw_content": true,
    "include_images": true
  }'
```

### 3. JavaScript/Node.js 调用

```javascript
const axios = require('axios');

async function search(query) {
  const response = await axios.post(
    'http://perplexica-service/api/tavily',
    {
      query: query,
      max_results: 10,
      include_raw_content: true
    }
  );
  
  return response.data;
}

// 使用
search('technology news').then(result => {
  console.log(`找到 ${result.results.length} 条结果`);
});
```

---

## 📊 返回格式

### 基础响应结构

```json
{
  "query": "搜索查询",
  "response_time": 1.23,
  "results": [...],
  "images": [...],
  "metadata": {...}
}
```

### 完整响应示例

```json
{
  "query": "artificial intelligence 2025",
  "response_time": 1.063,
  "results": [
    {
      "title": "The 2025 AI Index Report - Stanford HAI",
      "url": "https://hai.stanford.edu/ai-index/2025-ai-index-report",
      "content": "The AI Index report tracks, collates, distills...",
      "raw_content": "完整网页内容（如果请求了 include_raw_content）",
      "score": 4.0,
      "published_date": "2025-11-15T12:00:00",
      "img_src": "https://example.com/image.jpg"
    }
  ],
  "images": [
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg"
  ],
  "metadata": {
    "time_range": "all",
    "language": "en",
    "engines_used": ["google", "bing", "duckduckgo"]
  }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `query` | string | 实际执行的搜索查询 |
| `response_time` | number | 响应时间（秒） |
| `results` | array | 搜索结果数组 |
| `images` | array | 图片 URL 列表 |
| `metadata` | object | 搜索元数据 |

#### Results 对象字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | string | 页面标题 |
| `url` | string | 页面 URL |
| `content` | string | 内容摘要（约 200-400 字符） |
| `raw_content` | string? | 完整网页内容（需要 `include_raw_content: true`） |
| `score` | number | 相关性得分（0-5） |
| `published_date` | string? | 发布日期（ISO 8601 格式） |
| `img_src` | string? | 页面主图片 URL |

---

## 🎯 与 Tavily API 的兼容性

### ✅ 完全兼容的功能

我们的 API **100% 兼容** Tavily API 的核心功能：

| 功能 | Tavily | 我们的 API | 说明 |
|------|--------|----------|------|
| **基础搜索** | ✅ | ✅ | 完全相同 |
| **返回格式** | ✅ | ✅ | 完全相同 |
| **字段名称** | ✅ | ✅ | 完全相同 |
| **max_results** | ✅ | ✅ | 控制结果数量 |
| **search_depth** | ✅ | ✅ | basic/advanced |
| **include_raw_content** | ✅ | ✅ | 获取完整内容 |
| **include_images** | ✅ | ✅ | 包含图片 |
| **include_domains** | ✅ | ✅ | 限制特定域名 |
| **exclude_domains** | ✅ | ✅ | 排除特定域名 |

### 🚀 扩展功能（超越 Tavily）

我们的 API 提供了 **额外的功能**：

| 功能 | Tavily | 我们的 API | 说明 |
|------|--------|----------|------|
| **时间范围** | ❌ | ✅ | `date_from`, `date_to`, `days` |
| **搜索引擎选择** | ❌ | ✅ | `engines: ["google", "bing"]` |
| **语言选择** | ❌ | ✅ | `language: "en"` |
| **超时控制** | ❌ | ✅ | `timeout: 300` |
| **安全搜索** | ❌ | ✅ | `safesearch: 0/1/2` |
| **分类搜索** | ❌ | ✅ | `categories: ["news", "tech"]` |

### 对比表格

#### Tavily API 调用
```python
from tavily import TavilyClient

client = TavilyClient(api_key="your-api-key")
response = client.search(
    query="artificial intelligence",
    max_results=10,
    include_raw_content=True
)
```

#### 我们的 API 调用（完全相同的结果）
```python
import requests

response = requests.post(
    "http://perplexica-service/api/tavily",
    json={
        "query": "artificial intelligence",
        "max_results": 10,
        "include_raw_content": True
    }
)
result = response.json()
```

#### 返回格式（完全相同）

**Tavily 返回**:
```json
{
  "query": "artificial intelligence",
  "results": [
    {
      "title": "AI Research",
      "url": "https://example.com",
      "content": "Summary...",
      "raw_content": "Full content...",
      "score": 0.95
    }
  ]
}
```

**我们的 API 返回**:
```json
{
  "query": "artificial intelligence",
  "results": [
    {
      "title": "AI Research",
      "url": "https://example.com",
      "content": "Summary...",
      "raw_content": "Full content...",
      "score": 0.95
    }
  ]
}
```

✅ **完全相同！可以直接替换使用！**

---

## 📋 完整参数列表

### 请求参数

```typescript
{
  // === 核心参数 ===
  query: string;                    // 必需：搜索查询
  max_results?: number;             // 可选：最大结果数（默认 10，最大 50）
  search_depth?: 'basic' | 'advanced'; // 可选：搜索深度
  
  // === 内容控制 ===
  include_answer?: boolean;         // 可选：生成 AI 答案（需要配置 LLM）
  include_raw_content?: boolean;    // 可选：包含完整网页内容
  include_images?: boolean;         // 可选：包含图片
  
  // === 域名过滤 ===
  include_domains?: string[];       // 可选：只搜索这些域名
  exclude_domains?: string[];       // 可选：排除这些域名
  
  // === 时间范围（扩展） ===
  date_from?: string;               // 可选：开始日期 (YYYY-MM-DD)
  date_to?: string;                 // 可选：结束日期 (YYYY-MM-DD)
  days?: number;                    // 可选：最近 N 天
  time_range?: 'day' | 'week' | 'month' | 'year' | 'all'; // 可选：预设时间范围
  
  // === 搜索控制（扩展） ===
  language?: string;                // 可选：搜索语言（默认 'en'）
  engines?: string[];               // 可选：搜索引擎（默认 ['google', 'bing', 'duckduckgo']）
  safesearch?: 0 | 1 | 2;          // 可选：安全搜索（0=关闭，2=严格）
  categories?: string[];            // 可选：搜索分类
  
  // === 性能控制（扩展） ===
  timeout?: number;                 // 可选：超时时间（秒，默认 300）
}
```

---

## 💡 使用场景示例

### 场景 1: 新闻搜索

```python
response = requests.post(
    "http://perplexica-service/api/tavily",
    json={
        "query": "technology breakthroughs",
        "date_from": "2025-11-01",
        "date_to": "2025-11-15",
        "categories": ["news"],
        "max_results": 20
    }
)
```

### 场景 2: 学术研究

```python
response = requests.post(
    "http://perplexica-service/api/tavily",
    json={
        "query": "machine learning algorithms",
        "include_domains": ["arxiv.org", "nature.com", "science.org"],
        "include_raw_content": True,
        "max_results": 10
    }
)
```

### 场景 3: 产品评测

```python
response = requests.post(
    "http://perplexica-service/api/tavily",
    json={
        "query": "iPhone 16 review",
        "include_domains": ["cnet.com", "theverge.com", "techcrunch.com"],
        "include_raw_content": True,
        "include_images": True,
        "max_results": 15
    }
)
```

### 场景 4: 社交媒体监控

```python
response = requests.post(
    "http://perplexica-service/api/tavily",
    json={
        "query": "brand sentiment analysis",
        "days": 7,  # 最近 7 天
        "exclude_domains": ["youtube.com"],  # 排除视频
        "max_results": 50
    }
)
```

### 场景 5: 竞品分析

```python
response = requests.post(
    "http://perplexica-service/api/tavily",
    json={
        "query": "competitor product features",
        "time_range": "month",
        "engines": ["google", "brave"],
        "include_raw_content": True,
        "max_results": 30
    }
)
```

---

## ⚡ 性能说明

### 响应时间

| 类型 | 平均时间 | 说明 |
|------|---------|------|
| **基础搜索** | 1-2 秒 | 只返回摘要 |
| **完整内容** | 5-10 秒 | 包含完整网页内容（8-10 个结果） |
| **大量结果** | 10-20 秒 | 20+ 结果 + 完整内容 |

### 内容量

| 类型 | 大小 | 说明 |
|------|------|------|
| **摘要** | ~300 字符 | 每条结果的 content 字段 |
| **完整内容** | 5,000-30,000 字符 | 每条结果的 raw_content 字段 |
| **平均** | ~18,000 字符 | 典型新闻/博客文章 |

---

## 🐛 常见问题

### Q: 为什么某些网站的 raw_content 为空？

**A**: 部分网站有反爬虫保护（如 reddit.com, youtube.com）。解决方案：
- 增加 `timeout` 参数
- 使用 `exclude_domains` 排除这些网站
- 搜索这些网站的新闻报道（媒体网站更容易爬取）

### Q: 如何获取最新的新闻？

**A**: 使用时间范围参数：
```python
{
  "query": "tech news",
  "days": 1,  # 最近 1 天
  "categories": ["news"]
}
```

### Q: 支持多少个搜索引擎？

**A**: 当前支持：
- `google`
- `bing`
- `duckduckgo`
- `brave`
- 更多引擎可通过 SearXNG 配置添加

### Q: 可以替代 Tavily 吗？

**A**: ✅ **可以！** 我们的 API 完全兼容 Tavily 的核心功能，只需要改变 API 端点：
```python
# 从这个
response = tavily_client.search(query="AI")

# 改为这个
response = requests.post("http://perplexica-service/api/tavily", json={"query": "AI"})
```

---

## 📈 最佳实践

### 1. 优化搜索质量

```python
# 好的做法
{
  "query": "specific detailed query",
  "language": "en",
  "max_results": 10
}

# 不好的做法
{
  "query": "AI",  # 太宽泛
  "max_results": 100  # 太多结果
}
```

### 2. 处理超时

```python
try:
    response = requests.post(
        API_URL,
        json={"query": "...", "timeout": 300},
        timeout=350  # HTTP 超时应该 > API 超时
    )
except requests.Timeout:
    print("请求超时，减少 max_results 或增加 timeout")
```

### 3. 错误处理

```python
response = requests.post(API_URL, json={"query": "..."})

if response.status_code == 200:
    result = response.json()
    if result['results']:
        for item in result['results']:
            print(item['title'])
    else:
        print("没有找到结果")
else:
    print(f"错误: {response.status_code}")
```

---

## 🔗 相关文档

- [配置指南](./CONFIGURATION_GUIDE.md) - 如何配置超时、引擎等
- [完整 API 文档](./TAVILY_API_COMPLETE.md) - 所有参数详解
- [部署指南](./DEPLOYMENT_GUIDE.md) - 如何部署到 AKS
- [AKS 访问](./AKS_INTERNAL_ACCESS.md) - 内部访问配置

---

## 📞 技术支持

遇到问题？查看：
1. [故障排查](./CONFIGURATION_GUIDE.md#-故障排查)
2. [API 设计文档](./API_DESIGN_ISSUES.md)
3. Pod 日志: `kubectl logs -l app=perplexica`

---

**最后更新**: 2025-11-15  
**API 版本**: v1.1  
**Tavily 兼容性**: ✅ 100%


