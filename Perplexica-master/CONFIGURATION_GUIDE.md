# Perplexica Tavily API 配置指南

## 📍 所有配置参数的位置

---

## 方法 1: API 请求参数 ⭐⭐⭐ (推荐)

### 位置
调用 API 时在 JSON body 中指定

### 配置文件
无需修改代码

### 使用示例

**Python:**
```python
import requests

response = requests.post(
    "http://perplexica-service/api/tavily",
    json={
        "query": "Call of Duty Black Ops 7",
        "max_results": 8,           # 返回结果数
        "timeout": 300,             # 超时时间（秒）
        "include_raw_content": True,# 获取完整内容
        "language": "en",           # 搜索语言
        "engines": ["google", "duckduckgo", "brave"],  # 搜索引擎
        "exclude_domains": [],      # 排除的域名（空=不排除）
        "include_domains": [],      # 只搜索特定域名
        "date_from": "2025-10-01",  # 开始日期
        "date_to": "2025-10-10"     # 结束日期
    }
)
```

**Curl:**
```bash
curl -X POST http://perplexica-service/api/tavily \
  -H "Content-Type: application/json" \
  -d '{
    "query": "your search query",
    "max_results": 8,
    "timeout": 300,
    "include_raw_content": true
  }'
```

### 优缺点
- ✅ **优点**: 灵活，无需重启，每次调用可以不同
- ❌ **缺点**: 每次调用都需要指定

---

## 方法 2: 环境变量 (全局默认)

### 位置
Kubernetes Deployment 配置

### 配置文件
`Perplexica-master/k8s/deployment.yaml`

### 方法 A: 编辑 YAML 文件

在 `deployment.yaml` 中添加环境变量：

```yaml
spec:
  template:
    spec:
      containers:
      - name: perplexica
        image: shankswhite/perplexica:tavily-v1.1
        env:
        - name: PORT
          value: "3000"
        - name: SEARXNG_API_URL
          value: "http://localhost:8080"
        # 添加 Tavily API 配置
        - name: TAVILY_TIMEOUT
          value: "300"              # 默认超时 300 秒
        - name: TAVILY_MAX_RESULTS
          value: "50"               # 最大结果数
        - name: TAVILY_DEFAULT_LANGUAGE
          value: "en"               # 默认语言
```

然后应用更改：
```bash
kubectl apply -f Perplexica-master/k8s/deployment.yaml
kubectl rollout restart deployment/perplexica
```

### 方法 B: 直接使用 kubectl 命令 (更快)

```bash
# 设置环境变量
kubectl set env deployment/perplexica \
  TAVILY_TIMEOUT=300 \
  TAVILY_MAX_RESULTS=50 \
  TAVILY_DEFAULT_LANGUAGE=en

# Pod 会自动重启，等待完成
kubectl rollout status deployment/perplexica

# 验证环境变量
kubectl describe deployment/perplexica | grep -A 10 "Environment:"
```

### 优缺点
- ✅ **优点**: 一次设置，全局生效，不需要每次指定
- ❌ **缺点**: 需要重启 Pod（约 1-2 分钟）

---

## 方法 3: 修改代码默认值 (永久修改)

### 位置
源代码中的配置常量

### 配置文件
`Perplexica-master/src/app/api/tavily/route.ts` (第 18-27 行)

### 修改方法

编辑 `route.ts`：

```typescript
// Configuration (can be overridden by environment variables)
const CONFIG = {
  MAX_RESULTS: parseInt(process.env.TAVILY_MAX_RESULTS || '50'),
  DEFAULT_RESULTS: 10,
  DEFAULT_LANGUAGE: process.env.TAVILY_DEFAULT_LANGUAGE || 'en',
  DEFAULT_SEARCH_DEPTH: 'basic' as 'basic' | 'advanced',
  ANSWER_CONTEXT_SIZE: parseInt(process.env.TAVILY_ANSWER_CONTEXT || '5'),
  DEFAULT_ENGINES: ['google', 'bing', 'duckduckgo'],
  TIMEOUT: parseInt(process.env.TAVILY_TIMEOUT || '300'),  // 👈 改这里，默认 300 秒
};
```

### 重新构建和部署

```bash
cd Perplexica-master

# 1. 构建新镜像
docker buildx build --platform linux/amd64 \
  -t shankswhite/perplexica:tavily-v1.2 . --push

# 2. 更新部署
kubectl set image deployment/perplexica \
  perplexica=shankswhite/perplexica:tavily-v1.2

# 3. 等待更新完成
kubectl rollout status deployment/perplexica

# 4. 验证
kubectl get pods -l app=perplexica
```

### 优缺点
- ✅ **优点**: 永久修改，版本控制，不会忘记
- ❌ **缺点**: 需要重新构建镜像和部署（约 3-5 分钟）

---

## 📊 完整参数配置表

| 参数名 | API 参数 | 环境变量 | 默认值 | 说明 |
|--------|---------|---------|--------|------|
| **超时时间** | `timeout` | `TAVILY_TIMEOUT` | 60 秒 | 内容抓取超时 |
| **最大结果数** | `max_results` | `TAVILY_MAX_RESULTS` | 50 | 单次最多返回结果 |
| **默认结果数** | `max_results` | - | 10 | 未指定时的默认值 |
| **语言** | `language` | `TAVILY_DEFAULT_LANGUAGE` | 'en' | 搜索语言 |
| **搜索引擎** | `engines` | - | `['google', 'bing', 'duckduckgo']` | 使用的搜索引擎 |
| **排除域名** | `exclude_domains` | - | `[]` | 要排除的域名列表 |
| **包含域名** | `include_domains` | - | `[]` | 只搜索这些域名 |
| **开始日期** | `date_from` | - | null | 时间范围起始 (YYYY-MM-DD) |
| **结束日期** | `date_to` | - | null | 时间范围结束 (YYYY-MM-DD) |
| **相对天数** | `days` | - | null | 最近 N 天 |
| **时间范围** | `time_range` | - | 'all' | day/week/month/year/all |
| **安全搜索** | `safesearch` | - | 2 | 0=关闭, 1=中等, 2=严格 |
| **分类** | `categories` | - | `['general']` | 搜索分类 |

---

## 🎯 优先级规则

配置参数的优先级（从高到低）：

```
API 请求参数 > 环境变量 > 代码默认值
```

**示例：**
- 代码默认值: `60` 秒
- 设置环境变量 `TAVILY_TIMEOUT=300` → 实际使用 **300** 秒
- API 请求中指定 `"timeout": 600` → 实际使用 **600** 秒（最高优先级）

---

## 💡 使用场景推荐

### 场景 1: 开发和测试
**推荐**: 方法 1 (API 参数)
- 每次调用时灵活设置
- 无需重启服务
- 方便调试不同配置

### 场景 2: 生产环境 (稳定配置)
**推荐**: 方法 2 (环境变量)
- 一次设置，全局生效
- 不需要在每次调用时重复指定
- 方便统一管理

### 场景 3: 长期部署 (固化配置)
**推荐**: 方法 3 (代码修改)
- 永久修改，不会忘记
- 通过版本控制管理
- 适合有明确需求的长期项目

---

## 🔧 常见配置示例

### 示例 1: 不排除任何网站，增加超时

```python
response = requests.post(
    "http://perplexica-service/api/tavily",
    json={
        "query": "Call of Duty Black Ops 7",
        "max_results": 8,           # 保持并发数
        "timeout": 300,             # 增加到 5 分钟
        "exclude_domains": [],      # 不排除（包括 reddit, wiki）
        "include_raw_content": True
    }
)
```

### 示例 2: 只搜索特定网站

```python
response = requests.post(
    "http://perplexica-service/api/tavily",
    json={
        "query": "player reviews",
        "include_domains": [
            "ign.com",
            "gamespot.com",
            "forbes.com"
        ],
        "timeout": 300,
        "include_raw_content": True
    }
)
```

### 示例 3: 时间范围搜索

```python
response = requests.post(
    "http://perplexica-service/api/tavily",
    json={
        "query": "COD BO7 events",
        "date_from": "2025-10-01",
        "date_to": "2025-10-10",
        "max_results": 20,
        "timeout": 300,
        "include_raw_content": True
    }
)
```

---

## ⚠️ 注意事项

### 超时时间设置

1. **太短**（如 60 秒）：
   - 多个网站并发抓取时容易超时
   - 官方网站、YouTube、Wikipedia 等响应慢
   - 超时后所有结果的 `raw_content` 都为空

2. **合理**（如 300 秒）：
   - 能够处理大部分网站
   - 平衡速度和成功率

3. **太长**（如 600 秒+）：
   - API 响应时间过长
   - 可能被客户端超时中断

### 并发数量 (max_results)

- **8-10个**: 平衡速度和内容量
- **超过 20个**: 可能导致抓取超时
- **建议**: 配合更长的超时时间使用

### 域名过滤

**容易被阻止的网站**:
- `reddit.com` (403 Forbidden)
- `callofduty.com` (强 JS 渲染)
- `youtube.com` (视频网站)
- `wikipedia.org` (需要特殊处理)

**容易成功的网站**:
- 游戏媒体: `ign.com`, `gamespot.com`, `gamesradar.com`
- 新闻媒体: `forbes.com`, `cnet.com`
- 技术媒体: `techradar.com`, `windowscentral.com`

---

## 🐛 故障排查

### 问题 1: 所有结果的 raw_content 都为空

**原因**: 批量抓取超时

**解决**:
```json
{
  "timeout": 300,  // 增加超时时间
  "max_results": 5 // 减少并发数
}
```

### 问题 2: 某些网站始终获取失败

**原因**: 网站有反爬虫保护

**解决**:
```json
{
  "exclude_domains": [
    "reddit.com",
    "youtube.com"
  ]
}
```

### 问题 3: 响应时间太长

**原因**: 请求了太多结果或难爬取的网站

**解决**:
```json
{
  "max_results": 5,              // 减少结果数
  "exclude_domains": [
    "callofduty.com",            // 排除慢响应网站
    "youtube.com"
  ]
}
```

---

## 📚 相关文档

- [API 设计文档](./API_DESIGN_ISSUES.md)
- [完整 API 文档](./TAVILY_API_COMPLETE.md)
- [部署指南](./DEPLOYMENT_GUIDE.md)
- [AKS 内部访问](./AKS_INTERNAL_ACCESS.md)

---

**最后更新**: 2025-11-15  
**版本**: v1.1


