# 📖 Perplexica Tavily API - 参数完整参考

## 概述

本文档详细列出了 Perplexica Tavily API 所有可控制的参数，包括参数类型、默认值、用途和使用示例。

**API 端点**: `POST http://perplexica-service/api/tavily`

---

## 📊 参数分类

### 1. 核心参数 (Core Parameters)

#### `query` ⭐ **必需**

- **类型**: `string`
- **必需**: ✅ 是
- **描述**: 搜索查询字符串
- **示例**: 
  ```json
  "query": "artificial intelligence trends 2025"
  ```

#### `max_results`

- **类型**: `number`
- **必需**: ❌ 否
- **默认值**: `10`
- **范围**: `1 - 50`
- **描述**: 返回的最大结果数量
- **示例**: 
  ```json
  "max_results": 20
  ```

#### `search_depth`

- **类型**: `string`
- **必需**: ❌ 否
- **默认值**: `"basic"`
- **可选值**: `"basic"` | `"advanced"`
- **描述**: 搜索深度级别
  - `basic`: 标准搜索
  - `advanced`: 更深入的搜索（可能返回更多结果）
- **示例**: 
  ```json
  "search_depth": "advanced"
  ```

---

### 2. 内容控制参数 (Content Control)

#### `include_answer`

- **类型**: `boolean`
- **必需**: ❌ 否
- **默认值**: `false`
- **描述**: 是否使用 LLM 生成综合答案
- **注意**: 需要配置 `llm_provider` 和 `llm_model` 或设置 API keys
- **示例**: 
  ```json
  "include_answer": true
  ```

#### `include_raw_content`

- **类型**: `boolean`
- **必需**: ❌ 否
- **默认值**: `false`
- **描述**: 是否抓取并返回网页的完整原始内容
- **注意**: 启用后会增加响应时间（60-300秒）
- **示例**: 
  ```json
  "include_raw_content": true
  ```

#### `include_images`

- **类型**: `boolean`
- **必需**: ❌ 否
- **默认值**: `false`
- **描述**: 是否返回相关图片
- **示例**: 
  ```json
  "include_images": true
  ```

---

### 3. 域名过滤参数 (Domain Filtering)

#### `include_domains`

- **类型**: `string[]`
- **必需**: ❌ 否
- **默认值**: `[]` (不限制)
- **描述**: 只从指定域名搜索结果
- **用途**: 限制搜索范围到特定网站
- **示例**: 
  ```json
  "include_domains": ["github.com", "stackoverflow.com", "medium.com"]
  ```

#### `exclude_domains`

- **类型**: `string[]`
- **必需**: ❌ 否
- **默认值**: `[]` (不排除)
- **描述**: 排除指定域名的搜索结果
- **用途**: 过滤不想要的来源
- **示例**: 
  ```json
  "exclude_domains": ["youtube.com", "twitter.com", "pinterest.com"]
  ```

---

### 4. 时间范围参数 (Time Range) 🆕

**优先级**: `date_from/date_to` > `days` > `time_range`

#### `date_from`

- **类型**: `string`
- **必需**: ❌ 否
- **格式**: `YYYY-MM-DD`
- **描述**: 搜索结果的开始日期
- **实现**: 通过 Google `after:` 操作符
- **示例**: 
  ```json
  "date_from": "2025-01-01"
  ```

#### `date_to`

- **类型**: `string`
- **必需**: ❌ 否
- **格式**: `YYYY-MM-DD`
- **描述**: 搜索结果的结束日期
- **实现**: 通过 Google `before:` 操作符
- **示例**: 
  ```json
  "date_to": "2025-12-31"
  ```

#### `days`

- **类型**: `number`
- **必需**: ❌ 否
- **范围**: `> 0`
- **描述**: 搜索最近 N 天的结果
- **实现**: 自动计算 `date_from` = 今天 - N 天
- **示例**: 
  ```json
  "days": 7
  ```
  相当于搜索最近 7 天的内容

#### `time_range`

- **类型**: `string`
- **必需**: ❌ 否
- **可选值**: `"day"` | `"week"` | `"month"` | `"year"` | `"all"`
- **默认值**: `"all"`
- **描述**: SearXNG 时间范围预设
- **优先级**: 最低（如果设置了 `date_from/to` 或 `days` 则忽略）
- **示例**: 
  ```json
  "time_range": "week"
  ```

---

### 5. 搜索控制参数 (Search Control) 🆕

#### `language`

- **类型**: `string`
- **必需**: ❌ 否
- **默认值**: `"en"` (可通过环境变量 `TAVILY_DEFAULT_LANGUAGE` 修改)
- **格式**: ISO 639-1 语言代码
- **描述**: 搜索结果的语言
- **常用值**: 
  - `"en"`: 英语
  - `"zh"`: 中文
  - `"ja"`: 日语
  - `"es"`: 西班牙语
  - `"fr"`: 法语
- **示例**: 
  ```json
  "language": "zh"
  ```

#### `engines`

- **类型**: `string[]`
- **必需**: ❌ 否
- **默认值**: `["google", "bing", "duckduckgo"]`
- **描述**: 使用的搜索引擎
- **可用引擎**: 
  - `"google"`
  - `"bing"`
  - `"duckduckgo"`
  - `"brave"`
  - `"qwant"`
  - `"startpage"`
  - 更多...（取决于 SearXNG 配置）
- **示例**: 
  ```json
  "engines": ["google", "bing"]
  ```

#### `safesearch`

- **类型**: `number`
- **必需**: ❌ 否
- **默认值**: `2` (严格)
- **可选值**: 
  - `0`: 关闭
  - `1`: 中等
  - `2`: 严格
- **描述**: 安全搜索级别
- **示例**: 
  ```json
  "safesearch": 1
  ```

#### `categories`

- **类型**: `string[]`
- **必需**: ❌ 否
- **默认值**: `["general"]`
- **描述**: 搜索类别
- **可用类别**: 
  - `"general"`: 通用搜索
  - `"news"`: 新闻
  - `"images"`: 图片
  - `"videos"`: 视频
  - `"science"`: 科学
  - `"it"`: 信息技术
  - 更多...（取决于 SearXNG 配置）
- **示例**: 
  ```json
  "categories": ["news", "general"]
  ```

---

### 6. LLM 控制参数 (LLM Control) 🆕

#### `llm_provider`

- **类型**: `string`
- **必需**: ❌ 否（但生成答案时必需）
- **描述**: LLM 提供商
- **可用值**: 
  - `"openai"`
  - `"anthropic"`
  - `"ollama"`
  - `"groq"`
  - 更多...（取决于配置）
- **示例**: 
  ```json
  "llm_provider": "openai"
  ```

#### `llm_model`

- **类型**: `string`
- **必需**: ❌ 否（但生成答案时必需）
- **描述**: 具体的 LLM 模型
- **示例**: 
  ```json
  "llm_model": "gpt-4"
  ```

#### `answer_max_tokens`

- **类型**: `number`
- **必需**: ❌ 否
- **默认值**: 模型默认值
- **描述**: 答案生成的最大 token 数
- **示例**: 
  ```json
  "answer_max_tokens": 500
  ```

#### `answer_temperature`

- **类型**: `number`
- **必需**: ❌ 否
- **范围**: `0.0 - 2.0`
- **默认值**: 模型默认值（通常 0.7-1.0）
- **描述**: 答案生成的温度（创造性）
  - `0.0`: 最确定/保守
  - `1.0`: 平衡
  - `2.0`: 最创造/随机
- **示例**: 
  ```json
  "answer_temperature": 0.7
  ```

#### `answer_context_size`

- **类型**: `number`
- **必需**: ❌ 否
- **默认值**: `5` (可通过环境变量 `TAVILY_ANSWER_CONTEXT` 修改)
- **描述**: 用于生成答案的搜索结果数量
- **示例**: 
  ```json
  "answer_context_size": 10
  ```

---

### 7. 性能参数 (Performance) 🆕

#### `timeout`

- **类型**: `number`
- **必需**: ❌ 否
- **默认值**: `60` 秒 (可通过环境变量 `TAVILY_TIMEOUT` 修改，当前设置为 300)
- **单位**: 秒
- **描述**: 内容抓取的超时时间
- **用途**: 防止慢速网站拖累整体响应
- **示例**: 
  ```json
  "timeout": 120
  ```

#### `api_key`

- **类型**: `string`
- **必需**: ❌ 否
- **描述**: API 认证密钥（可选）
- **用途**: 如果配置了认证，则需要提供
- **示例**: 
  ```json
  "api_key": "your-api-key-here"
  ```

---

## 📝 参数优先级

### 时间范围参数优先级

```
date_from / date_to (最高)
    ↓
days
    ↓
time_range (最低)
```

**示例**: 如果同时提供 `date_from` 和 `days`，只会使用 `date_from`

### 域名过滤优先级

```
include_domains (先执行)
    ↓
exclude_domains (后执行)
```

**示例**: 如果同时提供，会先限制到 `include_domains`，然后再排除 `exclude_domains`

---

## 🎯 使用示例

### 示例 1: 基础搜索

```json
{
  "query": "Python machine learning libraries"
}
```

### 示例 2: 获取完整内容

```json
{
  "query": "React hooks tutorial",
  "max_results": 5,
  "include_raw_content": true
}
```

### 示例 3: 时间范围搜索

```json
{
  "query": "AI breakthroughs",
  "date_from": "2025-01-01",
  "date_to": "2025-11-17",
  "max_results": 10
}
```

### 示例 4: 域名限制搜索

```json
{
  "query": "JavaScript frameworks comparison",
  "include_domains": ["medium.com", "dev.to", "hashnode.com"],
  "max_results": 15
}
```

### 示例 5: 排除域名搜索

```json
{
  "query": "travel guides Paris",
  "exclude_domains": ["tripadvisor.com", "booking.com"],
  "max_results": 10
}
```

### 示例 6: 多语言搜索

```json
{
  "query": "人工智能",
  "language": "zh",
  "max_results": 10
}
```

### 示例 7: 自定义搜索引擎

```json
{
  "query": "privacy-focused email services",
  "engines": ["duckduckgo", "brave", "qwant"],
  "max_results": 10
}
```

### 示例 8: 最近 N 天搜索

```json
{
  "query": "tech news",
  "days": 7,
  "max_results": 20
}
```

### 示例 9: 生成 LLM 答案

```json
{
  "query": "What is quantum computing?",
  "include_answer": true,
  "llm_provider": "openai",
  "llm_model": "gpt-4",
  "answer_context_size": 5,
  "max_results": 10
}
```

### 示例 10: 综合高级搜索

```json
{
  "query": "artificial intelligence ethics",
  "max_results": 20,
  "include_raw_content": true,
  "include_images": true,
  "date_from": "2024-01-01",
  "language": "en",
  "engines": ["google", "bing"],
  "exclude_domains": ["wikipedia.org", "youtube.com"],
  "safesearch": 2,
  "timeout": 300
}
```

---

## 🔧 环境变量配置

以下环境变量可以修改 API 的默认行为：

| 环境变量 | 默认值 | 描述 |
|---------|--------|------|
| `TAVILY_MAX_RESULTS` | `50` | 最大结果数上限 |
| `TAVILY_DEFAULT_LANGUAGE` | `en` | 默认搜索语言 |
| `TAVILY_TIMEOUT` | `60` | 默认超时（秒） |
| `TAVILY_ANSWER_CONTEXT` | `5` | 答案上下文大小 |

**当前部署配置**:
```yaml
env:
  - name: TAVILY_TIMEOUT
    value: "300"  # 5分钟
  - name: TAVILY_MAX_RESULTS
    value: "50"
  - name: TAVILY_DEFAULT_LANGUAGE
    value: "en"
```

---

## 📊 参数总览表

| 参数 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `query` | string | ✅ | - | 搜索查询 |
| `max_results` | number | ❌ | 10 | 最大结果数 |
| `search_depth` | string | ❌ | "basic" | 搜索深度 |
| `include_answer` | boolean | ❌ | false | 生成 LLM 答案 |
| `include_raw_content` | boolean | ❌ | false | 返回完整内容 |
| `include_images` | boolean | ❌ | false | 返回图片 |
| `include_domains` | string[] | ❌ | [] | 限制域名 |
| `exclude_domains` | string[] | ❌ | [] | 排除域名 |
| `date_from` | string | ❌ | - | 开始日期 |
| `date_to` | string | ❌ | - | 结束日期 |
| `days` | number | ❌ | - | 最近N天 |
| `time_range` | string | ❌ | "all" | 时间范围预设 |
| `language` | string | ❌ | "en" | 搜索语言 |
| `engines` | string[] | ❌ | ["google", "bing", "duckduckgo"] | 搜索引擎 |
| `safesearch` | number | ❌ | 2 | 安全搜索 |
| `categories` | string[] | ❌ | ["general"] | 搜索类别 |
| `llm_provider` | string | ❌ | - | LLM 提供商 |
| `llm_model` | string | ❌ | - | LLM 模型 |
| `answer_max_tokens` | number | ❌ | - | 答案最大tokens |
| `answer_temperature` | number | ❌ | - | 答案温度 |
| `answer_context_size` | number | ❌ | 5 | 答案上下文 |
| `timeout` | number | ❌ | 60 | 超时时间 |
| `api_key` | string | ❌ | - | API密钥 |

---

## 💡 最佳实践

### 1. 性能优化

- **不需要完整内容时**, 不要设置 `include_raw_content: true`
- **合理设置 `max_results`**: 10-20 通常足够，过多会增加响应时间
- **使用 `exclude_domains`** 排除不需要的来源（如社交媒体）

### 2. 内容质量

- **使用 `include_domains`** 限制到高质量来源
- **设置 `safesearch: 2`** 过滤不适当内容
- **使用时间范围** 获取最新信息

### 3. 成本控制

- **谨慎使用 `include_answer`**: LLM 调用会产生费用
- **合理设置 `timeout`**: 避免长时间等待
- **使用 `answer_context_size`** 控制 LLM 输入大小

### 4. 错误处理

- **始终检查响应状态**
- **处理超时情况**: `timeout` 参数防止无限等待
- **验证必需参数**: `query` 是唯一必需参数

---

## 🚨 常见问题

### Q1: 为什么 `include_answer` 不返回答案？

**A**: 需要同时提供 `llm_provider` 和 `llm_model`，并且配置相应的 API keys。

### Q2: `include_raw_content` 为什么很慢？

**A**: 因为需要抓取并解析每个网页的完整内容。可以：
- 减少 `max_results`
- 使用 `exclude_domains` 排除慢速网站
- 增加 `timeout` 避免超时

### Q3: 如何只搜索最近的新闻？

**A**: 组合使用：
```json
{
  "query": "your query",
  "days": 7,
  "categories": ["news"]
}
```

### Q4: 可以同时使用多种时间参数吗？

**A**: 可以提供，但只会使用优先级最高的：
- `date_from/to` (最高)
- `days`
- `time_range` (最低)

---

**文档版本**: 1.0  
**最后更新**: 2025-11-17  
**API 版本**: Tavily Compatible v1.1

