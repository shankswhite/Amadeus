# 📦 Perplexica Tavily API - 返回格式与 Tavily 对比

## 概述

本文档详细说明 Perplexica Tavily API 的返回格式，并与标准 Tavily API 进行对比，确认兼容性。

**结论**: ✅ **100% 兼容 Tavily API 标准格式，并提供扩展功能**

---

## 📊 返回格式结构

### 完整响应对象

```typescript
{
  query: string;                      // 原始搜索查询
  answer?: string;                    // LLM 生成的答案（如果请求）
  follow_up_questions?: string[];     // 后续问题建议（如果有）
  images?: string[];                  // 相关图片URLs（如果请求）
  results: TavilySearchResult[];      // 搜索结果数组
  response_time: number;              // 响应时间（秒）
  metadata?: {                        // 扩展元数据（新增）
    time_range?: string;
    language: string;
    engines_used: string[];
    llm_used?: string;
  }
}
```

### 搜索结果对象

```typescript
{
  title: string;           // 页面标题
  url: string;             // 页面 URL
  content: string;         // 内容摘要
  raw_content?: string;    // 完整原始内容（如果请求）
  score: number;           // 相关性得分 (0-1)
  published_date?: string; // 发布日期
  img_src?: string;        // 图片 URL（新增）
}
```

---

## 🔍 实际返回示例

### 示例 1: 基础搜索

**请求**:
```json
{
  "query": "Python programming",
  "max_results": 3
}
```

**返回**:
```json
{
  "query": "Python programming",
  "results": [
    {
      "title": "Python Programming Language - Official Website",
      "url": "https://www.python.org/",
      "content": "The official home of the Python Programming Language. Python is powerful, fast, plays well with others, runs everywhere...",
      "score": 1.0,
      "published_date": null
    },
    {
      "title": "Learn Python - Free Interactive Python Tutorial",
      "url": "https://www.learnpython.org/",
      "content": "Welcome to the LearnPython.org interactive Python tutorial. Whether you are an experienced programmer or not...",
      "score": 0.95,
      "published_date": null
    },
    {
      "title": "Python Tutorial - W3Schools",
      "url": "https://www.w3schools.com/python/",
      "content": "Well organized and easy to understand Web building tutorials with lots of examples of how to use HTML, CSS...",
      "score": 0.9,
      "published_date": null
    }
  ],
  "response_time": 2.35,
  "metadata": {
    "language": "en",
    "engines_used": ["google", "bing", "duckduckgo"]
  }
}
```

---

### 示例 2: 包含完整内容

**请求**:
```json
{
  "query": "React hooks tutorial",
  "max_results": 2,
  "include_raw_content": true
}
```

**返回**:
```json
{
  "query": "React hooks tutorial",
  "results": [
    {
      "title": "Introducing Hooks – React",
      "url": "https://react.dev/reference/react/hooks",
      "content": "Hooks are a new addition in React 16.8. They let you use state and other React features without writing a class...",
      "raw_content": "Menu React Hooks Hooks let you use different React features from your components. You can either use the built-in Hooks or combine them to build your own. This page lists all built-in Hooks in React.\n\nState Hooks\nState lets a component \"remember\" information like user input. For example, a form component can use state to store the input value, while an image gallery component can use state to store the selected image index.\n\nTo add state to a component, use one of these Hooks:\n\nuseState declares a state variable that you can update directly.\nuseReducer declares a state variable with the update logic inside a reducer function...\n\n[完整内容约 27,000 字符]",
      "score": 1.0,
      "published_date": null
    },
    {
      "title": "React Hooks Tutorial - Step by Step Guide",
      "url": "https://www.example.com/react-hooks",
      "content": "A comprehensive guide to React Hooks including useState, useEffect, useContext, and more...",
      "raw_content": "[完整网页内容 15,000+ 字符]",
      "score": 0.95,
      "published_date": "2025-10-15"
    }
  ],
  "response_time": 65.42,
  "metadata": {
    "language": "en",
    "engines_used": ["google", "bing", "duckduckgo"]
  }
}
```

---

### 示例 3: 时间范围搜索

**请求**:
```json
{
  "query": "AI breakthrough",
  "date_from": "2025-11-01",
  "date_to": "2025-11-17",
  "max_results": 5
}
```

**返回**:
```json
{
  "query": "AI breakthrough",
  "results": [
    {
      "title": "Major AI Breakthrough in Natural Language Processing",
      "url": "https://news.example.com/ai-breakthrough-2025",
      "content": "Researchers announced a significant breakthrough in natural language processing that could revolutionize...",
      "score": 1.0,
      "published_date": "2025-11-15"
    },
    {
      "title": "New AI Model Achieves Human-Level Performance",
      "url": "https://techcrunch.com/ai-news",
      "content": "A new artificial intelligence model has achieved human-level performance on complex reasoning tasks...",
      "score": 0.95,
      "published_date": "2025-11-12"
    }
  ],
  "response_time": 3.21,
  "metadata": {
    "time_range": "2025-11-01 to 2025-11-17",
    "language": "en",
    "engines_used": ["google", "bing", "duckduckgo"]
  }
}
```

---

### 示例 4: 包含 LLM 答案

**请求**:
```json
{
  "query": "What is machine learning?",
  "include_answer": true,
  "llm_provider": "openai",
  "llm_model": "gpt-4",
  "max_results": 5
}
```

**返回**:
```json
{
  "query": "What is machine learning?",
  "answer": "Machine learning is a subset of artificial intelligence (AI) that enables computer systems to learn and improve from experience without being explicitly programmed. It focuses on developing algorithms and statistical models that allow computers to perform specific tasks by analyzing patterns in data rather than following pre-programmed rules.\n\nKey aspects of machine learning include:\n\n1. **Data-Driven Learning**: ML systems learn from large amounts of data, identifying patterns and relationships that humans might miss.\n\n2. **Types of Learning**:\n   - Supervised Learning: Learning from labeled data\n   - Unsupervised Learning: Finding patterns in unlabeled data\n   - Reinforcement Learning: Learning through trial and error\n\n3. **Applications**: Machine learning powers many modern technologies including recommendation systems, image recognition, natural language processing, and autonomous vehicles.\n\nThe field has grown exponentially in recent years due to increased computing power, availability of big data, and advances in algorithms.",
  "follow_up_questions": [
    "What are the main types of machine learning algorithms?",
    "How does deep learning differ from traditional machine learning?",
    "What are some real-world applications of machine learning?"
  ],
  "results": [
    {
      "title": "Machine Learning - Wikipedia",
      "url": "https://en.wikipedia.org/wiki/Machine_learning",
      "content": "Machine learning (ML) is a field of study in artificial intelligence concerned with the development and study of statistical algorithms...",
      "score": 1.0
    },
    {
      "title": "What is Machine Learning? | IBM",
      "url": "https://www.ibm.com/topics/machine-learning",
      "content": "Machine learning is a branch of artificial intelligence (AI) and computer science which focuses on the use of data and algorithms...",
      "score": 0.95
    }
  ],
  "response_time": 8.67,
  "metadata": {
    "language": "en",
    "engines_used": ["google", "bing", "duckduckgo"],
    "llm_used": "openai/gpt-4"
  }
}
```

---

### 示例 5: 包含图片

**请求**:
```json
{
  "query": "Golden Gate Bridge",
  "include_images": true,
  "max_results": 3
}
```

**返回**:
```json
{
  "query": "Golden Gate Bridge",
  "images": [
    "https://example.com/images/golden-gate-1.jpg",
    "https://example.com/images/golden-gate-2.jpg",
    "https://example.com/images/golden-gate-3.jpg",
    "https://example.com/images/golden-gate-4.jpg"
  ],
  "results": [
    {
      "title": "Golden Gate Bridge - Wikipedia",
      "url": "https://en.wikipedia.org/wiki/Golden_Gate_Bridge",
      "content": "The Golden Gate Bridge is a suspension bridge spanning the Golden Gate, the one-mile-wide strait connecting San Francisco Bay...",
      "score": 1.0,
      "img_src": "https://upload.wikimedia.org/wikipedia/commons/golden-gate.jpg"
    },
    {
      "title": "Golden Gate Bridge | History, Construction, & Facts",
      "url": "https://www.britannica.com/topic/Golden-Gate-Bridge",
      "content": "Golden Gate Bridge, suspension bridge spanning the Golden Gate in California to link San Francisco with Marin county to the north...",
      "score": 0.95,
      "img_src": "https://cdn.britannica.com/golden-gate-bridge.jpg"
    }
  ],
  "response_time": 4.12,
  "metadata": {
    "language": "en",
    "engines_used": ["google", "bing", "duckduckgo"]
  }
}
```

---

## 🔄 与 Tavily API 对比

### Tavily API 标准格式

```json
{
  "query": "string",
  "answer": "string",
  "follow_up_questions": ["string"],
  "images": ["string"],
  "results": [
    {
      "title": "string",
      "url": "string",
      "content": "string",
      "raw_content": "string",
      "score": 0.95,
      "published_date": "string"
    }
  ],
  "response_time": 1.23
}
```

### Perplexica API 格式

```json
{
  "query": "string",              // ✅ 相同
  "answer": "string",             // ✅ 相同
  "follow_up_questions": ["string"], // ✅ 相同
  "images": ["string"],           // ✅ 相同
  "results": [                    // ✅ 相同
    {
      "title": "string",          // ✅ 相同
      "url": "string",            // ✅ 相同
      "content": "string",        // ✅ 相同
      "raw_content": "string",    // ✅ 相同
      "score": 0.95,              // ✅ 相同
      "published_date": "string", // ✅ 相同
      "img_src": "string"         // 🆕 新增（可选）
    }
  ],
  "response_time": 1.23,          // ✅ 相同
  "metadata": {                   // 🆕 新增（可选）
    "time_range": "string",
    "language": "string",
    "engines_used": ["string"],
    "llm_used": "string"
  }
}
```

---

## ✅ 兼容性验证

### 核心字段对比

| 字段 | Tavily | Perplexica | 兼容性 | 备注 |
|------|--------|------------|--------|------|
| `query` | ✅ | ✅ | ✅ 100% | 完全相同 |
| `answer` | ✅ | ✅ | ✅ 100% | 完全相同 |
| `follow_up_questions` | ✅ | ✅ | ✅ 100% | 完全相同 |
| `images` | ✅ | ✅ | ✅ 100% | 完全相同 |
| `results` | ✅ | ✅ | ✅ 100% | 完全相同 |
| `response_time` | ✅ | ✅ | ✅ 100% | 完全相同 |
| `metadata` | ❌ | ✅ | ✅ 兼容 | 新增，不影响兼容性 |

### 结果对象字段对比

| 字段 | Tavily | Perplexica | 兼容性 | 备注 |
|------|--------|------------|--------|------|
| `title` | ✅ | ✅ | ✅ 100% | 完全相同 |
| `url` | ✅ | ✅ | ✅ 100% | 完全相同 |
| `content` | ✅ | ✅ | ✅ 100% | 完全相同 |
| `raw_content` | ✅ | ✅ | ✅ 100% | 完全相同 |
| `score` | ✅ | ✅ | ✅ 100% | 完全相同 |
| `published_date` | ✅ | ✅ | ✅ 100% | 完全相同 |
| `img_src` | ❌ | ✅ | ✅ 兼容 | 新增，不影响兼容性 |

---

## 📈 兼容性总结

### ✅ 完全兼容

Perplexica Tavily API 的返回格式与 Tavily API **100% 兼容**：

1. **所有核心字段**: 完全相同的字段名和类型
2. **数据结构**: 完全相同的嵌套结构
3. **数据类型**: 完全相同的类型定义
4. **可选字段**: 遵循相同的可选规则

### 🆕 扩展功能

Perplexica 在保持完全兼容的基础上，增加了以下扩展功能：

1. **`metadata` 对象**: 提供额外的搜索元信息
   - `time_range`: 使用的时间范围
   - `language`: 搜索语言
   - `engines_used`: 使用的搜索引擎
   - `llm_used`: 使用的 LLM 模型

2. **`img_src` 字段**: 每个结果可以包含图片 URL
   - 便于客户端直接显示相关图片
   - 不影响不使用此字段的客户端

### 🔌 Drop-in 替换

由于完全兼容，Perplexica API 可以作为 Tavily API 的 **Drop-in 替换**：

```python
# 原来使用 Tavily
response = requests.post(
    "https://api.tavily.com/search",
    json={"query": "AI trends", "api_key": "..."}
)

# 直接替换为 Perplexica（无需修改代码）
response = requests.post(
    "http://perplexica-service/api/tavily",
    json={"query": "AI trends"}
)

# 返回格式完全相同，现有代码无需修改 ✅
results = response.json()["results"]
```

---

## 📝 字段详细说明

### 1. `query` (string)

- **描述**: 原始搜索查询字符串
- **示例**: `"Python machine learning"`
- **来源**: 请求参数
- **始终存在**: ✅ 是

### 2. `answer` (string, 可选)

- **描述**: LLM 生成的综合答案
- **示例**: `"Python is a high-level programming language..."`
- **存在条件**: 
  - 请求中 `include_answer: true`
  - 配置了 LLM provider 和 model
- **始终存在**: ❌ 否（可选）

### 3. `follow_up_questions` (string[], 可选)

- **描述**: 建议的后续问题
- **示例**: 
  ```json
  [
    "What are the benefits of Python?",
    "How to install Python?",
    "Python vs JavaScript?"
  ]
  ```
- **存在条件**: 生成答案时可能包含
- **始终存在**: ❌ 否（可选）

### 4. `images` (string[], 可选)

- **描述**: 相关图片的 URL 数组
- **示例**: 
  ```json
  [
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg"
  ]
  ```
- **存在条件**: 请求中 `include_images: true`
- **始终存在**: ❌ 否（可选）

### 5. `results` (TavilySearchResult[])

- **描述**: 搜索结果数组
- **数量**: 根据 `max_results` 参数（默认 10）
- **排序**: 按相关性得分降序
- **始终存在**: ✅ 是（至少为空数组）

### 6. `response_time` (number)

- **描述**: 总响应时间（秒）
- **示例**: `2.35`
- **精度**: 小数点后 2 位
- **始终存在**: ✅ 是

### 7. `metadata` (object, 可选) 🆕

- **描述**: 扩展元数据信息
- **字段**: 
  - `time_range`: 使用的时间范围
  - `language`: 搜索语言
  - `engines_used`: 使用的搜索引擎数组
  - `llm_used`: 使用的 LLM（如果有）
- **示例**: 
  ```json
  {
    "time_range": "2025-11-01 to 2025-11-17",
    "language": "en",
    "engines_used": ["google", "bing", "duckduckgo"],
    "llm_used": "openai/gpt-4"
  }
  ```
- **始终存在**: ❌ 否（可选）

---

## 🎯 结果对象字段详解

### 1. `title` (string)

- **描述**: 网页标题
- **示例**: `"Machine Learning - Wikipedia"`
- **来源**: 搜索引擎结果
- **始终存在**: ✅ 是

### 2. `url` (string)

- **描述**: 网页 URL
- **示例**: `"https://en.wikipedia.org/wiki/Machine_learning"`
- **格式**: 完整 URL
- **始终存在**: ✅ 是

### 3. `content` (string)

- **描述**: 内容摘要/片段
- **长度**: 通常 150-300 字符
- **示例**: `"Machine learning (ML) is a field of study in artificial intelligence..."`
- **来源**: 搜索引擎提供
- **始终存在**: ✅ 是

### 4. `raw_content` (string, 可选)

- **描述**: 完整网页内容（纯文本）
- **长度**: 通常 5,000-50,000 字符
- **示例**: `"[完整网页文本内容]"`
- **存在条件**: 请求中 `include_raw_content: true`
- **抓取时间**: 增加 60-300 秒响应时间
- **失败处理**: 如果抓取失败，包含错误信息
- **始终存在**: ❌ 否（可选）

### 5. `score` (number)

- **描述**: 相关性得分
- **范围**: `0.0 - 1.0`（也可能 > 1.0）
- **示例**: `0.95`
- **来源**: 
  - SearXNG 的评分（如果有）
  - 或基于排名计算: `1.0 - index * 0.05`
- **排序**: 结果按此得分降序排列
- **始终存在**: ✅ 是

### 6. `published_date` (string, 可选)

- **描述**: 发布日期
- **格式**: ISO 8601 或其他日期格式
- **示例**: `"2025-11-15"`
- **来源**: 搜索引擎提供（如果有）
- **始终存在**: ❌ 否（很多结果没有日期）

### 7. `img_src` (string, 可选) 🆕

- **描述**: 相关图片 URL
- **示例**: `"https://example.com/thumbnail.jpg"`
- **来源**: 搜索结果的缩略图或图片
- **始终存在**: ❌ 否（可选）

---

## 📊 响应时间分析

### 典型响应时间

| 场景 | 响应时间 | 说明 |
|------|---------|------|
| 基础搜索 | 2-5 秒 | 只返回标题和摘要 |
| 完整内容（5个结果） | 30-60 秒 | 抓取网页内容 |
| 完整内容（10个结果） | 60-120 秒 | 抓取更多网页 |
| 包含 LLM 答案 | +5-15 秒 | LLM 生成时间 |
| 超时 | 300 秒 | 默认超时设置 |

### 响应时间计算

```javascript
response_time = (Date.now() - startTime) / 1000

// 示例
startTime = 1700000000000  // 请求开始
endTime = 1700000002350    // 请求结束
response_time = (2350) / 1000 = 2.35 秒
```

---

## 🚨 错误响应格式

### 400 Bad Request

```json
{
  "error": "Missing required parameter: query",
  "message": "The query parameter is required"
}
```

### 500 Internal Server Error

```json
{
  "error": "Internal server error",
  "message": "An unexpected error occurred during search",
  "details": "Error details..."
}
```

---

## 💡 使用建议

### 1. 解析响应

```python
# Python 示例
response = requests.post(url, json=request_data)
data = response.json()

# 访问字段
query = data["query"]
results = data["results"]
response_time = data["response_time"]

# 可选字段需要检查
if "answer" in data:
    answer = data["answer"]

if "metadata" in data:
    engines = data["metadata"]["engines_used"]
```

### 2. 处理空结果

```python
if len(data["results"]) == 0:
    print("No results found")
else:
    for result in data["results"]:
        print(f"{result['title']}: {result['url']}")
```

### 3. 获取完整内容

```python
for result in data["results"]:
    if "raw_content" in result and result["raw_content"]:
        # 成功获取完整内容
        full_text = result["raw_content"]
    else:
        # 只有摘要
        summary = result["content"]
```

### 4. 使用元数据

```python
if "metadata" in data:
    meta = data["metadata"]
    print(f"Searched in: {meta['language']}")
    print(f"Using engines: {', '.join(meta['engines_used'])}")
    if "time_range" in meta:
        print(f"Time range: {meta['time_range']}")
```

---

## 🎉 总结

### ✅ 兼容性确认

1. **100% Tavily 兼容**: 所有核心字段完全相同
2. **Drop-in 替换**: 可直接替换现有 Tavily API 调用
3. **向后兼容**: 新增字段不影响现有客户端
4. **类型安全**: TypeScript 类型定义确保一致性

### 🆕 扩展优势

1. **更多元数据**: `metadata` 对象提供搜索上下文
2. **图片支持**: `img_src` 字段方便显示图片
3. **灵活配置**: 通过参数控制返回内容
4. **性能信息**: `response_time` 帮助监控性能

### 🔌 集成建议

- **新项目**: 直接使用 Perplexica API，享受扩展功能
- **迁移项目**: 无需修改代码，直接替换 URL
- **客户端库**: 可使用现有 Tavily SDK，只需修改端点

---

**文档版本**: 1.0  
**最后更新**: 2025-11-17  
**API 版本**: Tavily Compatible v1.1  
**兼容性**: ✅ 100% Tavily API 兼容

