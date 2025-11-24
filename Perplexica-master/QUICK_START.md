# 🚀 Perplexica Tavily API 快速开始

## ✅ 已配置完成

- ⏱️ **超时**: 300 秒（默认）
- 📊 **最大结果**: 50 条
- 🌐 **语言**: 英文 (en)
- 🔧 **镜像**: tavily-v1.1

---

## 📍 API 地址

**内部访问**: `http://perplexica-service/api/tavily`

---

## 🎯 最简单的调用

### Python
```python
import requests

response = requests.post(
    "http://perplexica-service/api/tavily",
    json={"query": "你的搜索"}
)

result = response.json()
print(f"找到 {len(result['results'])} 条结果")
```

### Curl
```bash
curl -X POST http://perplexica-service/api/tavily \
  -H "Content-Type: application/json" \
  -d '{"query": "你的搜索"}'
```

---

## 💡 常用场景

### 1. 获取完整网页内容
```python
{
  "query": "搜索词",
  "max_results": 10,
  "include_raw_content": True  # 👈 完整内容
}
```

### 2. 时间范围搜索
```python
{
  "query": "新闻",
  "date_from": "2025-11-01",
  "date_to": "2025-11-15"
}
```

### 3. 限制特定网站
```python
{
  "query": "评测",
  "include_domains": ["ign.com", "gamespot.com"]
}
```

### 4. 排除特定网站
```python
{
  "query": "新闻",
  "exclude_domains": ["reddit.com", "youtube.com"]
}
```

---

## 📊 返回格式

```json
{
  "query": "搜索查询",
  "response_time": 1.23,
  "results": [
    {
      "title": "标题",
      "url": "链接",
      "content": "摘要",
      "raw_content": "完整内容（可选）",
      "score": 0.95,
      "published_date": "2025-11-15",
      "img_src": "图片链接"
    }
  ],
  "images": ["图片1", "图片2"],
  "metadata": {
    "language": "en",
    "engines_used": ["google", "bing"]
  }
}
```

---

## ✅ Tavily 兼容性

**100% 兼容 Tavily API！**

只需改变 API 端点：

```python
# Tavily
from tavily import TavilyClient
client = TavilyClient(api_key="...")
result = client.search("query")

# 我们的 API（完全相同的结果）
import requests
response = requests.post(
    "http://perplexica-service/api/tavily",
    json={"query": "query"}
)
result = response.json()
```

---

## 🎛️ 所有参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `query` | string | **必需** | 搜索查询 |
| `max_results` | number | 10 | 结果数量 |
| `include_raw_content` | boolean | false | 完整内容 |
| `include_images` | boolean | false | 包含图片 |
| `date_from` | string | - | 开始日期 |
| `date_to` | string | - | 结束日期 |
| `days` | number | - | 最近 N 天 |
| `language` | string | 'en' | 搜索语言 |
| `engines` | array | ['google','bing'] | 搜索引擎 |
| `timeout` | number | 300 | 超时（秒） |
| `include_domains` | array | [] | 只搜索这些域名 |
| `exclude_domains` | array | [] | 排除这些域名 |

---

## ⚡ 性能参考

| 类型 | 时间 | 内容量 |
|------|------|--------|
| 基础搜索 | 1-2s | 摘要 (~300字符) |
| 完整内容 | 5-10s | 完整 (~18,000字符) |

---

## 📚 完整文档

- 📖 [API 使用指南](./API_USAGE_GUIDE.md) - 详细用法
- ⚙️ [配置指南](./CONFIGURATION_GUIDE.md) - 参数配置
- 🔧 [完整 API 文档](./TAVILY_API_COMPLETE.md) - 所有功能

---

**现在就开始使用！** 🎉
