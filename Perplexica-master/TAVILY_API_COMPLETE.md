# 🚀 增强版 Tavily API 完整文档

## 📋 概览

增强版 Tavily API 完全兼容原版，并新增了大量灵活的参数：
- ✅ **时间范围控制**（date_from/date_to/days）
- ✅ **自定义搜索引擎**
- ✅ **语言选择**
- ✅ **LLM 模型选择**
- ✅ **零硬编码**（所有参数可配置）

---

## 🔌 API 端点

```
POST /api/tavily
GET  /api/tavily
```

---

## 📝 完整参数列表

### 🎯 核心参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `query` | string | ✅ | - | 搜索查询 |
| `max_results` | number | ❌ | 10 | 最大结果数（1-50） |
| `search_depth` | 'basic'\|'advanced' | ❌ | 'basic' | 搜索深度 |

### 📄 内容控制

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `include_answer` | boolean | ❌ | false | 是否生成答案 |
| `include_raw_content` | boolean | ❌ | false | 是否包含完整内容 |
| `include_images` | boolean | ❌ | false | 是否包含图片搜索 |

### 🌐 域名过滤

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `include_domains` | string[] | ❌ | [] | 限制搜索的域名列表 |
| `exclude_domains` | string[] | ❌ | [] | 排除的域名列表 |

### ⏰ 时间范围（新功能！）

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `date_from` | string | ❌ | - | 起始日期 (YYYY-MM-DD) |
| `date_to` | string | ❌ | - | 结束日期 (YYYY-MM-DD) |
| `days` | number | ❌ | - | 最近 N 天（相对时间） |
| `time_range` | 'day'\|'week'\|'month'\|'year'\|'all' | ❌ | - | SearXNG 预设时间范围 |

**优先级**: `date_from/date_to` > `days` > `time_range`

### 🔍 搜索控制（新功能！）

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `language` | string | ❌ | 'en' | 搜索语言（'en', 'zh', 'ja' 等） |
| `engines` | string[] | ❌ | ['google','bing','duckduckgo'] | 搜索引擎列表 |
| `safesearch` | 0\|1\|2 | ❌ | 2 | 安全搜索（0=关闭, 1=中等, 2=严格） |
| `categories` | string[] | ❌ | ['general'] | 搜索类别 |

### 🤖 LLM 控制（新功能！）

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `llm_provider` | string | ❌ | (自动) | LLM 提供商（'openai', 'anthropic' 等） |
| `llm_model` | string | ❌ | (自动) | 具体模型（'gpt-4', 'claude-3' 等） |
| `answer_max_tokens` | number | ❌ | - | 答案最大长度 |
| `answer_temperature` | number | ❌ | - | 答案生成温度（0-1） |
| `answer_context_size` | number | ❌ | 5 | 用于生成答案的结果数量 |

### ⚡ 性能控制（新功能！）

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `timeout` | number | ❌ | 60 | 请求超时时间（秒） |
| `api_key` | string | ❌ | - | API 密钥（可选验证） |

---

## 📊 响应格式

```typescript
{
  "query": string,                    // 原始查询
  "answer": string?,                  // 生成的答案（如果 include_answer=true）
  "follow_up_questions": string[]?,   // 后续问题建议
  "images": string[]?,                // 图片 URLs（如果 include_images=true）
  "results": [
    {
      "title": string,                // 标题
      "url": string,                  // URL
      "content": string,              // 摘要
      "raw_content": string?,         // 完整内容（如果 include_raw_content=true）
      "score": number,                // 相关性评分 (0-1)
      "published_date": string?       // 发布日期
    }
  ],
  "response_time": number,            // 响应时间（秒）
  "metadata": {                       // 扩展元数据
    "time_range": string,             // 实际使用的时间范围
    "language": string,               // 使用的语言
    "engines_used": string[],         // 使用的搜索引擎
    "llm_used": string?               // 使用的 LLM 模型
  }
}
```

---

## 💡 使用示例

### 示例 1: 基础搜索

```bash
curl -X POST http://localhost:3000/api/tavily \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence",
    "max_results": 10
  }'
```

### 示例 2: 指定时间范围（绝对日期）

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

### 示例 3: 相对时间范围

```bash
curl -X POST http://localhost:3000/api/tavily \
  -H "Content-Type: application/json" \
  -d '{
    "query": "latest AI breakthroughs",
    "days": 7,
    "max_results": 15
  }'
```

### 示例 4: SearXNG 预设时间范围

```bash
curl -X POST http://localhost:3000/api/tavily \
  -H "Content-Type: application/json" \
  -d '{
    "query": "tech news",
    "time_range": "week",
    "max_results": 10
  }'
```

### 示例 5: 自定义搜索引擎和语言

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

### 示例 6: 高级搜索 + 答案生成

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

### 示例 7: 限制域名 + 时间范围

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

### 示例 8: 完整配置示例

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

### 示例 9: GET 请求

```bash
curl "http://localhost:3000/api/tavily?query=AI+news&date_from=2025-01-01&date_to=2025-01-31&max_results=10&include_answer=true"
```

---

## 🎯 时间范围详解

### 方式 1: 绝对日期（推荐用于精确控制）

```json
{
  "query": "events",
  "date_from": "2025-10-01",
  "date_to": "2025-10-10"
}
```

**使用场景**: 
- 搜索特定日期范围的事件
- 历史数据查询
- 精确的时间窗口

**实现方式**: 添加 `after:YYYY-MM-DD before:YYYY-MM-DD` 到查询

### 方式 2: 相对天数（推荐用于近期内容）

```json
{
  "query": "latest news",
  "days": 7
}
```

**使用场景**:
- 最新新闻
- 近期更新
- 动态时间窗口

**实现方式**: 计算相对日期，添加 `after:YYYY-MM-DD`

### 方式 3: SearXNG 预设（最简单）

```json
{
  "query": "tech updates",
  "time_range": "week"
}
```

**可选值**: `day`, `week`, `month`, `year`, `all`

**使用场景**:
- 快速过滤
- 不需要精确日期
- 利用搜索引擎原生过滤

---

## 🛠️ 环境变量配置

在 Kubernetes 部署中添加环境变量来覆盖默认值：

```yaml
env:
- name: TAVILY_MAX_RESULTS
  value: "100"                      # 最大结果数上限
- name: TAVILY_DEFAULT_LANGUAGE
  value: "en"                       # 默认语言
- name: TAVILY_ANSWER_CONTEXT
  value: "10"                       # 答案生成使用的结果数
- name: TAVILY_TIMEOUT
  value: "120"                      # 默认超时（秒）
```

---

## 📊 与 SearCrawl 的对比

| 功能 | SearCrawl | 增强版 Tavily API |
|------|-----------|-------------------|
| 时间范围 | ⚠️  需要 `date_from`/`date_to` | ✅ 3种方式（绝对/相对/预设） |
| 语言选择 | ❌ 硬编码 'zh' | ✅ 可配置任意语言 |
| 搜索引擎 | ⚠️  通过 `enabled_engines` | ✅ 更灵活的 `engines` 数组 |
| 答案生成 | ❌ 无 | ✅ 自动生成 + 可配置 |
| 图片搜索 | ❌ 失败 | ✅ 原生支持 |
| LLM 选择 | ❌ 无 | ✅ 可指定提供商和模型 |
| 硬编码参数 | ❌ 很多 | ✅ 零硬编码 |
| 性能 | ⚠️  慢 (67秒) | ✅ 快 (2-5秒) |

---

## 🎨 迁移示例

### 从 SearCrawl 迁移

**之前（SearCrawl）**:
```python
response = requests.post('http://searcrawl/search', json={
    'query': 'AI news',
    'limit': 10,
    'date_from': '2025-10-01',
    'date_to': '2025-10-10',
    'enabled_engines': 'google__general',
    'include_raw_content': True
})
```

**现在（Perplexica Tavily）**:
```python
response = requests.post('http://perplexica/api/tavily', json={
    'query': 'AI news',
    'max_results': 10,              # 改名
    'date_from': '2025-10-01',      # 相同
    'date_to': '2025-10-10',        # 相同
    'engines': ['google'],          # 简化
    'include_raw_content': True,    # 相同
    'include_answer': True          # 新功能！
})
```

---

## 🔧 故障排查

### 时间范围不生效？

1. **检查日期格式**: 必须是 `YYYY-MM-DD`
2. **检查优先级**: `date_from/date_to` > `days` > `time_range`
3. **查看 metadata**: 响应中的 `metadata.time_range` 显示实际使用的时间范围

### 答案生成失败？

1. **确保 `search_depth: 'advanced'`**
2. **检查 LLM 配置**: 是否有可用的 LLM 模型
3. **查看日志**: `kubectl logs -f -l app=perplexica`

### 搜索结果太少？

1. **放宽时间限制**: 扩大 date_from/date_to 范围
2. **增加引擎**: 添加更多搜索引擎
3. **移除域名限制**: 去掉 `include_domains`

---

## 📚 相关文档

- [部署指南](./DEPLOYMENT_GUIDE.md)
- [迁移指南](./MIGRATION_FROM_SEARCRAWL.md)
- [设计问题分析](./API_DESIGN_ISSUES.md)
- [Tavily 官方文档](https://docs.tavily.com/)

---

## 🎉 总结

增强版 Tavily API 提供：

✅ **完整的时间控制** - 3种方式满足所有需求  
✅ **零硬编码** - 所有参数可配置  
✅ **LLM 集成** - 自动答案生成  
✅ **高度灵活** - 自定义引擎、语言、模型  
✅ **性能优秀** - 快速稳定  
✅ **Tavily 兼容** - 无缝替换  

**不再有 SearCrawl 的问题！** 🚀


