# Perplexica 部署选项 - Tavily API

## 🎯 当前状态

### 已部署
- ✅ Perplexica 官方镜像 (`itzcrazykns1337/perplexica:latest`)
- ✅ Web UI 可访问
- ✅ 内置 SearXNG 正常工作
- ✅ 原生 API 端点: `/api/search`, `/api/images`, `/api/videos`

### 未部署
- ❌ 自定义 Tavily API (`/api/tavily`) - 代码在本地，未打包到镜像

---

## 🚀 方案选择

### 方案 A: 构建并部署自定义镜像（推荐）

**优点**: 
- 完整的 Tavily API 兼容
- 所有自定义功能（时间范围、LLM 控制等）
- 与下游工具无缝集成

**缺点**:
- 需要构建 Docker 镜像（~5-10 分钟）
- 需要推送到 Docker Hub
- 需要重新部署

**步骤**:

```bash
cd /Users/zhaoxiaofeng/SynologyDrive/Drive/Projects/DeepResearch/Perplexica-master

# 1. 构建多平台镜像
docker buildx build --platform linux/amd64 \
  -t shankswhite/perplexica:tavily-v1.0 \
  --push \
  .

# 2. 更新 deployment.yaml
# 修改 image: itzcrazykns1337/perplexica:latest
# 改为: image: shankswhite/perplexica:tavily-v1.0

# 3. 重新部署
kubectl apply -f k8s/deployment.yaml
kubectl rollout restart deployment perplexica

# 4. 等待 Pod 就绪
kubectl wait --for=condition=ready pod -l app=perplexica --timeout=120s

# 5. 测试
kubectl run test-tavily --rm -it --restart=Never --image=curlimages/curl:latest -- sh -c '
  curl -X POST http://perplexica-service/api/tavily \
    -H "Content-Type: application/json" \
    -d "{\"query\":\"test\",\"max_results\":3}" \
    --max-time 60
'
```

---

### 方案 B: 使用现有的 `/api/search` 端点（快速方案）

**优点**:
- 立即可用，无需重新部署
- 官方支持，稳定性好
- 功能类似（搜索 + 答案生成）

**缺点**:
- API 格式不同，需要适配
- 缺少一些 Tavily 特定参数（如 `date_from`/`date_to`）
- 需要提供 LLM 配置

**现有 API 格式**:

```typescript
// POST /api/search
{
  "focusMode": "webSearch",           // 搜索模式
  "query": "your search query",       // 搜索查询
  "optimizationMode": "balanced",     // 'speed' 或 'balanced'
  "chatModel": {                      // 需要配置
    "providerId": "openai",
    "key": "gpt-4o-mini"
  },
  "embeddingModel": {                 // 需要配置
    "providerId": "openai",
    "key": "text-embedding-3-small"
  },
  "history": [],                      // 对话历史
  "systemInstructions": ""            // 可选
}
```

**示例调用**:

```python
import requests

# 使用现有的 /api/search 端点
response = requests.post(
    "http://perplexica-service/api/search",
    json={
        "focusMode": "webSearch",
        "query": "What is artificial intelligence?",
        "optimizationMode": "balanced",
        "chatModel": {
            "providerId": "openai",
            "key": "gpt-4o-mini"
        },
        "embeddingModel": {
            "providerId": "openai",
            "key": "text-embedding-3-small"
        },
        "history": []
    }
)

# 响应格式 (流式)
# 需要处理 SSE (Server-Sent Events) 或设置 stream: false
```

**注意**: 
- `/api/search` 需要提供 LLM 和 Embedding 模型配置
- 默认返回流式响应，需要客户端支持 SSE
- 不支持直接的时间范围参数

---

### 方案 C: 创建适配器层（中间方案）

在你的下游应用中创建适配器，将 Tavily API 格式转换为 Perplexica `/api/search` 格式。

**优点**:
- 无需重新部署 Perplexica
- 下游工具可以继续使用 Tavily API 格式
- 灵活可控

**缺点**:
- 需要在下游应用中实现适配逻辑
- 一些功能可能无法完美映射

**示例适配器**:

```python
# adapter.py - Tavily to Perplexica API Adapter

import requests
from typing import Dict, List, Any

class PerplexicaTavilyAdapter:
    def __init__(
        self, 
        perplexica_url: str = "http://perplexica-service",
        default_llm: Dict = None,
        default_embedding: Dict = None
    ):
        self.perplexica_url = perplexica_url
        self.default_llm = default_llm or {
            "providerId": "openai",
            "key": "gpt-4o-mini"
        }
        self.default_embedding = default_embedding or {
            "providerId": "openai",
            "key": "text-embedding-3-small"
        }
    
    def search(
        self, 
        query: str, 
        max_results: int = 10,
        include_answer: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Tavily API 兼容的搜索方法
        """
        # 转换为 Perplexica API 格式
        perplexica_request = {
            "focusMode": "webSearch",
            "query": query,
            "optimizationMode": "balanced",
            "chatModel": kwargs.get("chat_model", self.default_llm),
            "embeddingModel": kwargs.get("embedding_model", self.default_embedding),
            "history": [],
            "stream": False  # 非流式响应
        }
        
        # 调用 Perplexica API
        response = requests.post(
            f"{self.perplexica_url}/api/search",
            json=perplexica_request,
            timeout=60
        )
        response.raise_for_status()
        
        perplexica_data = response.json()
        
        # 转换为 Tavily API 格式
        tavily_response = {
            "query": query,
            "results": self._extract_results(perplexica_data, max_results),
            "answer": perplexica_data.get("message", "") if include_answer else None,
            "response_time": perplexica_data.get("response_time", 0)
        }
        
        return tavily_response
    
    def _extract_results(self, perplexica_data: Dict, max_results: int) -> List[Dict]:
        """
        从 Perplexica 响应中提取搜索结果
        """
        # 注意: Perplexica 的响应格式可能不同，需要根据实际情况调整
        sources = perplexica_data.get("sources", [])
        results = []
        
        for source in sources[:max_results]:
            results.append({
                "title": source.get("metadata", {}).get("title", ""),
                "url": source.get("metadata", {}).get("url", ""),
                "content": source.get("pageContent", ""),
                "score": 1.0  # Perplexica 可能不提供分数
            })
        
        return results

# 使用示例
adapter = PerplexicaTavilyAdapter(
    perplexica_url="http://perplexica-service",
    default_llm={"providerId": "openai", "key": "gpt-4o-mini"},
    default_embedding={"providerId": "openai", "key": "text-embedding-3-small"}
)

# Tavily API 风格的调用
results = adapter.search(
    query="What is AI?",
    max_results=10,
    include_answer=True
)

print(results)
```

---

## 🎯 推荐方案

| 场景 | 推荐方案 | 理由 |
|------|---------|------|
| **生产环境，需要完整 Tavily 兼容** | 方案 A | 最完整，长期最佳 |
| **快速测试，功能验证** | 方案 B | 立即可用 |
| **已有下游工具，不便修改** | 方案 C | 适配层解耦合 |
| **时间范围控制是核心需求** | 方案 A | 只有自定义镜像支持 |
| **只需基础搜索 + 答案** | 方案 B | 现有 API 足够 |

---

## 📝 方案 A 详细步骤

### 1. 确保 Dockerfile 存在

检查 `Perplexica-master/Dockerfile` 是否存在：

```bash
cd /Users/zhaoxiaofeng/SynologyDrive/Drive/Projects/DeepResearch/Perplexica-master
ls -l Dockerfile
```

如果不存在，需要创建。

### 2. 构建镜像

```bash
# 确保 Docker 正在运行
docker ps

# 构建 AMD64 镜像（适用于 Azure AKS）
docker buildx build --platform linux/amd64 \
  -t shankswhite/perplexica:tavily-v1.0 \
  --push \
  .
```

### 3. 更新 Kubernetes 部署

编辑 `k8s/deployment.yaml`:

```yaml
# 找到这一行:
image: itzcrazykns1337/perplexica:latest

# 改为:
image: shankswhite/perplexica:tavily-v1.0
```

### 4. 重新部署

```bash
# 应用更新的配置
kubectl apply -f k8s/deployment.yaml

# 强制重启以拉取新镜像
kubectl rollout restart deployment perplexica

# 监控部署进度
kubectl rollout status deployment perplexica

# 等待 Pod 就绪
kubectl wait --for=condition=ready pod -l app=perplexica --timeout=180s
```

### 5. 验证部署

```bash
# 检查 Pod 状态
kubectl get pods -l app=perplexica

# 查看 Pod 日志
kubectl logs -l app=perplexica --tail=50

# 测试 Tavily API
kubectl run test-tavily --rm -it --restart=Never --image=curlimages/curl:latest -- sh -c '
  curl -X POST http://perplexica-service/api/tavily \
    -H "Content-Type: application/json" \
    -d "{
      \"query\": \"artificial intelligence\",
      \"max_results\": 5,
      \"date_from\": \"2025-01-01\",
      \"date_to\": \"2025-12-31\"
    }" \
    --max-time 60 -s | head -100
'
```

---

## 🚨 常见问题

### Q1: 构建镜像需要多久？
**A**: 首次构建约 5-10 分钟（取决于网络速度和机器性能）。后续构建会利用缓存，更快。

### Q2: 是否必须推送到 Docker Hub？
**A**: 是的，因为 AKS 需要从公共或私有 registry 拉取镜像。也可以使用 Azure Container Registry (ACR)。

### Q3: 方案 B 的 /api/search 能替代 Tavily API 吗？
**A**: 部分可以，但缺少一些 Tavily 特定功能：
- ❌ 没有 `date_from`/`date_to` 时间范围控制
- ❌ 没有 `include_domains`/`exclude_domains` 域名过滤
- ✅ 有答案生成
- ✅ 有搜索功能

### Q4: 能否同时使用两个镜像？
**A**: 可以，部署两个不同的 Deployment：
- `perplexica-official` (官方镜像) - 用于 Web UI
- `perplexica-tavily` (自定义镜像) - 用于 Tavily API

---

## 📚 相关文档

- `AKS_INTERNAL_ACCESS.md` - AKS 内部访问和配置
- `TAVILY_API_COMPLETE.md` - Tavily API 完整文档
- `MIGRATION_FROM_SEARCRAWL.md` - 从 SearCrawl 迁移指南
- `API_DESIGN_ISSUES.md` - API 设计问题和修复

---

## 🎯 你应该选择哪个方案？

**如果你需要**:
- ✅ 时间范围控制 (`date_from`/`date_to`) → **方案 A**
- ✅ 域名过滤 (`include_domains`) → **方案 A**
- ✅ 完整 Tavily API 兼容 → **方案 A**
- ✅ 只需基础搜索 + 答案 → **方案 B**
- ✅ 快速验证功能 → **方案 B**
- ✅ 下游工具已固定使用 Tavily 格式 → **方案 A 或 C**

**我的建议**: 
1. **短期**：先用方案 B 验证功能
2. **长期**：部署方案 A 获得完整功能

有问题随时问我！🚀


