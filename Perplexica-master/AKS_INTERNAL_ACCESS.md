# Perplexica AKS 内部访问和配置指南

## 🎯 当前状态

✅ **部署位置**: Azure AKS (ai-analyst-aks)  
✅ **访问类型**: ClusterIP（仅集群内部访问）  
✅ **服务地址**: `perplexica-service.default.svc.cluster.local:80`  
✅ **SearXNG**: 已内置并正常运行

---

## 📍 从 AKS 内部访问

### 同一命名空间（default）内的服务

如果你的服务也在 `default` 命名空间，直接使用短名称：

```bash
# 服务名
http://perplexica-service

# 或完整域名
http://perplexica-service.default.svc.cluster.local
```

### 不同命名空间的服务

如果你的服务在其他命名空间（如 `my-app`）：

```bash
http://perplexica-service.default.svc.cluster.local
```

### 访问端点

```bash
# Web UI
http://perplexica-service/

# Tavily API（POST）
http://perplexica-service/api/tavily

# Tavily API（GET）
http://perplexica-service/api/tavily?query=test&max_results=5
```

---

## 🔑 API Keys 配置需求

### 基础搜索功能（✅ 不需要任何 API Key）

以下功能**无需配置任何 API Key**，开箱即用：

```bash
# 基础搜索 - 使用内置 SearXNG
curl -X POST http://perplexica-service/api/tavily \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence",
    "max_results": 10,
    "include_images": true
  }'
```

✅ **可用功能（无需 API Key）**:
- 基础搜索（`query`）
- 结果数量控制（`max_results`）
- 域名限制（`include_domains`, `exclude_domains`）
- 时间范围（`date_from`, `date_to`, `days`, `time_range`）
- 图片搜索（`include_images`）
- 搜索引擎选择（`engines`）
- 语言控制（`language`）

### 答案生成功能（⚠️ 需要 LLM API Key）

**仅当使用以下功能时**才需要配置 LLM API Key：

```bash
# 答案生成 - 需要 OpenAI/Anthropic 等 API Key
curl -X POST http://perplexica-service/api/tavily \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is artificial intelligence?",
    "include_answer": true,        # ⚠️ 需要 LLM API Key
    "llm_provider": "openai",       # 可选：指定 LLM 提供商
    "llm_model": "gpt-4o-mini"      # 可选：指定模型
  }'
```

⚠️ **需要 API Key 的功能**:
- 答案生成（`include_answer: true`）
- 后续问题生成（`follow_up_questions`）

---

## 🔧 如何配置 API Keys

### 方法 1: 使用 Kubernetes Secrets（推荐）

#### 步骤 1: 创建 Secret

```bash
# 创建包含 OpenAI API Key 的 Secret
kubectl create secret generic perplexica-secrets \
  --from-literal=openai-api-key=your-openai-api-key-here \
  --namespace=default

# 或者同时配置多个 LLM 提供商
kubectl create secret generic perplexica-secrets \
  --from-literal=openai-api-key=sk-xxxx \
  --from-literal=anthropic-api-key=sk-ant-xxxx \
  --from-literal=groq-api-key=gsk-xxxx \
  --namespace=default
```

#### 步骤 2: 更新 Deployment 配置

编辑 `k8s/deployment.yaml`，在 `env` 部分添加：

```yaml
env:
- name: NODE_ENV
  value: "production"
# 添加以下内容：
- name: OPENAI_API_KEY
  valueFrom:
    secretKeyRef:
      name: perplexica-secrets
      key: openai-api-key
- name: ANTHROPIC_API_KEY
  valueFrom:
    secretKeyRef:
      name: perplexica-secrets
      key: anthropic-api-key
  optional: true  # 可选配置
- name: GROQ_API_KEY
  valueFrom:
    secretKeyRef:
      name: perplexica-secrets
      key: groq-api-key
  optional: true  # 可选配置
```

#### 步骤 3: 应用更新

```bash
kubectl apply -f k8s/deployment.yaml
kubectl rollout restart deployment perplexica
```

### 方法 2: 直接在 Deployment 中配置（不推荐）

```yaml
env:
- name: NODE_ENV
  value: "production"
- name: OPENAI_API_KEY
  value: "sk-your-api-key-here"  # ⚠️ 不安全，不推荐
```

### 方法 3: 通过 ConfigMap（不推荐用于敏感信息）

```bash
kubectl create configmap perplexica-keys \
  --from-literal=openai-api-key=your-key \
  --namespace=default
```

---

## 🧪 测试连接

### 1. 从 Pod 内部测试（调试用）

```bash
# 进入任意 Pod
kubectl run test-pod --rm -it --image=curlimages/curl -- sh

# 在 Pod 内执行
curl -X POST http://perplexica-service/api/tavily \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "max_results": 3}'
```

### 2. 从你的应用代码中调用

#### Python 示例

```python
import requests

# Tavily API 端点（AKS 内部）
TAVILY_API_URL = "http://perplexica-service/api/tavily"

def search_with_perplexica(query: str, max_results: int = 10):
    """基础搜索 - 不需要 API Key"""
    response = requests.post(
        TAVILY_API_URL,
        json={
            "query": query,
            "max_results": max_results,
            "include_images": True,
            "date_from": "2025-01-01",  # 可选
            "date_to": "2025-12-31"     # 可选
        },
        timeout=60
    )
    return response.json()

def search_with_answer(query: str):
    """搜索并生成答案 - 需要配置 LLM API Key"""
    response = requests.post(
        TAVILY_API_URL,
        json={
            "query": query,
            "max_results": 10,
            "include_answer": True,      # 需要 LLM API Key
            "llm_provider": "openai",    # 可选
            "llm_model": "gpt-4o-mini"   # 可选
        },
        timeout=60
    )
    return response.json()

# 使用示例
results = search_with_perplexica("artificial intelligence", max_results=5)
print(f"找到 {len(results['results'])} 个结果")

# 如果配置了 LLM API Key，可以生成答案
answer_results = search_with_answer("What is AI?")
if 'answer' in answer_results:
    print(f"答案: {answer_results['answer']}")
```

#### Node.js/TypeScript 示例

```typescript
import axios from 'axios';

const TAVILY_API_URL = 'http://perplexica-service/api/tavily';

interface TavilyRequest {
  query: string;
  max_results?: number;
  include_answer?: boolean;
  include_images?: boolean;
  date_from?: string;
  date_to?: string;
  llm_provider?: string;
  llm_model?: string;
}

async function searchWithPerplexica(params: TavilyRequest) {
  try {
    const response = await axios.post(TAVILY_API_URL, params, {
      timeout: 60000,
      headers: { 'Content-Type': 'application/json' }
    });
    return response.data;
  } catch (error) {
    console.error('Perplexica search failed:', error);
    throw error;
  }
}

// 基础搜索示例（无需 API Key）
const basicResults = await searchWithPerplexica({
  query: 'artificial intelligence',
  max_results: 10,
  include_images: true
});

// 答案生成示例（需要 API Key）
const answerResults = await searchWithPerplexica({
  query: 'What is quantum computing?',
  include_answer: true,  // 需要配置 LLM API Key
  llm_model: 'gpt-4o-mini'
});
```

#### cURL 示例

```bash
# 基础搜索（无需 API Key）
curl -X POST http://perplexica-service/api/tavily \
  -H "Content-Type: application/json" \
  -d '{
    "query": "COD BO6 events",
    "max_results": 20,
    "date_from": "2025-10-01",
    "date_to": "2025-10-10",
    "language": "en",
    "engines": ["google", "duckduckgo", "brave"]
  }'

# 答案生成（需要 API Key）
curl -X POST http://perplexica-service/api/tavily \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is artificial intelligence?",
    "include_answer": true,
    "max_results": 5,
    "llm_provider": "openai",
    "llm_model": "gpt-4o-mini"
  }'
```

---

## 📊 监控和调试

### 查看 Pod 状态

```bash
kubectl get pods -l app=perplexica
kubectl describe pod -l app=perplexica
```

### 查看日志

```bash
# 实时日志
kubectl logs -f -l app=perplexica

# 查看最近 100 行
kubectl logs -l app=perplexica --tail=100

# 查看 SearXNG 相关日志
kubectl logs -l app=perplexica | grep -i searxng
```

### 检查 Service

```bash
# 查看 Service 详情
kubectl get svc perplexica-service
kubectl describe svc perplexica-service

# 测试 DNS 解析
kubectl run test-dns --rm -it --image=busybox -- nslookup perplexica-service
```

### 检查配置的 Secrets

```bash
# 列出所有 Secrets
kubectl get secrets

# 查看 Secret 详情（不显示实际值）
kubectl describe secret perplexica-secrets

# 查看 Secret 实际值（Base64 编码）
kubectl get secret perplexica-secrets -o yaml

# 解码 Secret 值
kubectl get secret perplexica-secrets -o jsonpath='{.data.openai-api-key}' | base64 --decode
```

---

## 🔒 安全建议

1. **使用 Secrets 管理 API Keys**
   - ✅ 使用 Kubernetes Secrets 而不是明文配置
   - ✅ 限制 Secret 访问权限（使用 RBAC）

2. **网络隔离**
   - ✅ 已配置为 ClusterIP（仅内部访问）
   - ⚠️ 如需外部访问，使用 Ingress + TLS

3. **资源限制**
   - ✅ 已配置 CPU/Memory limits
   - 根据实际使用情况调整

4. **日志审计**
   - 定期检查访问日志
   - 监控异常请求

---

## 📈 性能优化

### 当前资源配置

```yaml
resources:
  requests:
    cpu: "500m"
    memory: "1Gi"
  limits:
    cpu: "2000m"
    memory: "4Gi"
```

### 根据负载调整

```bash
# 查看实际资源使用
kubectl top pods -l app=perplexica

# 如果资源不足，调整 deployment.yaml 并重新部署
kubectl apply -f k8s/deployment.yaml
```

### 水平扩展

```bash
# 增加副本数
kubectl scale deployment perplexica --replicas=3

# 配置自动扩展（需要 metrics-server）
kubectl autoscale deployment perplexica --cpu-percent=70 --min=1 --max=5
```

---

## 🎯 总结

### ✅ 无需配置（开箱即用）

- **基础搜索功能** - SearXNG 已内置
- **时间范围控制** - `date_from`, `date_to`, `days`
- **图片搜索** - `include_images`
- **域名过滤** - `include_domains`, `exclude_domains`
- **语言和引擎选择** - `language`, `engines`

### ⚠️ 需要配置 API Key

- **答案生成** - `include_answer: true`（需要 OpenAI/Anthropic 等）
- **LLM 控制** - `llm_provider`, `llm_model`

### 🔌 访问地址

```bash
# 从 AKS 内部访问
http://perplexica-service/api/tavily
```

### 📚 完整文档

- API 参数详解: `TAVILY_API_COMPLETE.md`
- 迁移指南: `MIGRATION_FROM_SEARCRAWL.md`
- 部署指南: `DEPLOYMENT_GUIDE.md`

---

**需要帮助？** 查看日志或联系管理员！


