# Perplexica 部署到 Azure AKS 指南

## 🎯 概述

本指南将帮助你将 Perplexica 部署到 Azure AKS，并提供 Tavily 兼容的 API 端点。

### 新增功能

✅ **Tavily 兼容 API** - 位于 `/api/tavily`  
✅ **RESTful 接口** - 支持 POST 和 GET 请求  
✅ **完整的搜索功能** - 包括答案生成、图片搜索、内容提取  
✅ **易于集成** - 可作为 Tavily 的直接替代品

---

## 📋 前提条件

1. Azure CLI 已安装并登录
2. kubectl 已安装
3. 已有 AKS 集群（或按步骤创建）
4. Docker（如果需要自定义镜像）

---

## 🚀 部署步骤

### 步骤 1: 清理旧的 SearCrawl 部署

```bash
# 删除 SearCrawl 部署
kubectl delete deployment searcrawl-api
kubectl delete service searcrawl-service

# 删除 SearXNG 部署（如果不再需要）
kubectl delete deployment searxng
kubectl delete service searxng-service

# 可选：删除 ConfigMap 和 Secrets
kubectl delete configmap searxng-settings
```

### 步骤 2: 部署 Perplexica

```bash
cd Perplexica-master

# 部署 Perplexica
kubectl apply -f k8s/deployment.yaml

# 等待 Pod 就绪
kubectl wait --for=condition=ready pod -l app=perplexica --timeout=120s

# 检查状态
kubectl get pods -l app=perplexica
kubectl get svc perplexica-service
```

### 步骤 3: 配置访问

#### 选项 A: Port Forward（测试）

```bash
kubectl port-forward service/perplexica-service 3000:80
```

然后访问：
- Web UI: http://localhost:3000
- Tavily API: http://localhost:3000/api/tavily

#### 选项 B: Ingress（生产环境）

```bash
# 安装 NGINX Ingress Controller（如果还没有）
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# 部署 Ingress
kubectl apply -f k8s/ingress.yaml

# 获取外部 IP
kubectl get ingress perplexica-ingress
```

---

## 🔌 Tavily API 使用说明

### API 端点

```
POST /api/tavily
GET  /api/tavily
```

### 请求格式（POST）

```json
{
  "query": "your search query",
  "search_depth": "basic",          // 可选: "basic" 或 "advanced"
  "include_answer": true,            // 可选: 是否生成答案
  "include_raw_content": true,       // 可选: 是否包含完整内容
  "max_results": 10,                 // 可选: 最大结果数（1-50）
  "include_domains": ["example.com"], // 可选: 限制搜索域名
  "exclude_domains": ["spam.com"],   // 可选: 排除域名
  "include_images": true             // 可选: 包含图片搜索
}
```

### 请求示例（GET）

```bash
curl "http://localhost:3000/api/tavily?query=artificial%20intelligence&include_answer=true&max_results=5"
```

### 响应格式

```json
{
  "query": "artificial intelligence",
  "answer": "AI is...",              // 如果 include_answer=true
  "follow_up_questions": [           // 相关后续问题
    "What is machine learning?",
    "How does AI work?"
  ],
  "images": ["url1", "url2"],        // 如果 include_images=true
  "results": [
    {
      "title": "Article Title",
      "url": "https://example.com",
      "content": "Summary...",
      "raw_content": "Full text...",  // 如果 include_raw_content=true
      "score": 0.95,
      "published_date": "2024-01-01"
    }
  ],
  "response_time": 1.23              // 响应时间（秒）
}
```

---

## 🔧 配置

### 环境变量

在 `k8s/deployment.yaml` 中配置：

```yaml
env:
- name: OPENAI_API_KEY
  value: "your-key-here"
- name: ANTHROPIC_API_KEY
  value: "your-key-here"
```

或使用 Kubernetes Secrets：

```bash
# 创建 Secret
kubectl create secret generic perplexica-secrets \
  --from-literal=openai-api-key=your-key \
  --from-literal=anthropic-api-key=your-key

# 在 deployment.yaml 中引用
env:
- name: OPENAI_API_KEY
  valueFrom:
    secretKeyRef:
      name: perplexica-secrets
      key: openai-api-key
```

### 资源配置

根据负载调整资源：

```yaml
resources:
  requests:
    cpu: "500m"       # 最小 CPU
    memory: "1Gi"     # 最小内存
  limits:
    cpu: "2000m"      # 最大 CPU
    memory: "4Gi"     # 最大内存
```

---

## 🧪 测试 Tavily API

### 基础搜索

```bash
curl -X POST http://localhost:3000/api/tavily \
  -H "Content-Type: application/json" \
  -d '{
    "query": "latest AI breakthroughs 2024",
    "max_results": 5
  }' | jq .
```

### 高级搜索（含答案）

```bash
curl -X POST http://localhost:3000/api/tavily \
  -H "Content-Type: application/json" \
  -d '{
    "query": "how does quantum computing work",
    "search_depth": "advanced",
    "include_answer": true,
    "include_raw_content": true,
    "max_results": 3
  }' | jq .
```

### 限制域名搜索

```bash
curl -X POST http://localhost:3000/api/tavily \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning tutorials",
    "include_domains": ["arxiv.org", "github.com"],
    "max_results": 10
  }' | jq .
```

---

## 📊 监控和日志

### 查看日志

```bash
# 实时日志
kubectl logs -f -l app=perplexica

# 最近的日志
kubectl logs -l app=perplexica --tail=100
```

### 查看资源使用

```bash
kubectl top pods -l app=perplexica
```

### 查看事件

```bash
kubectl get events --sort-by='.lastTimestamp' | grep perplexica
```

---

## 🔄 更新和回滚

### 更新镜像

```bash
# 更新到最新版本
kubectl set image deployment/perplexica perplexica=itzcrazykns1337/perplexica:latest

# 查看更新状态
kubectl rollout status deployment/perplexica
```

### 回滚

```bash
# 查看历史
kubectl rollout history deployment/perplexica

# 回滚到上一个版本
kubectl rollout undo deployment/perplexica

# 回滚到特定版本
kubectl rollout undo deployment/perplexica --to-revision=2
```

---

## 🛠️ 故障排查

### Pod 启动失败

```bash
# 查看详细信息
kubectl describe pod -l app=perplexica

# 查看日志
kubectl logs -l app=perplexica --previous
```

### 服务无法访问

```bash
# 检查服务
kubectl get svc perplexica-service

# 检查端点
kubectl get endpoints perplexica-service

# 测试内部连接
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://perplexica-service/api/tavily?query=test
```

### 性能问题

```bash
# 增加副本数
kubectl scale deployment perplexica --replicas=3

# 查看资源使用
kubectl top pods -l app=perplexica
kubectl top nodes
```

---

## 🔐 安全建议

1. **使用 Secrets 管理敏感信息**
   ```bash
   kubectl create secret generic api-keys \
     --from-literal=openai=your-key \
     --from-literal=anthropic=your-key
   ```

2. **启用 RBAC**
   ```bash
   kubectl create serviceaccount perplexica-sa
   kubectl create rolebinding perplexica-binding \
     --serviceaccount=default:perplexica-sa \
     --clusterrole=view
   ```

3. **配置网络策略**
   - 限制入站流量
   - 只允许必要的出站连接

4. **定期更新镜像**
   ```bash
   kubectl set image deployment/perplexica \
     perplexica=itzcrazykns1337/perplexica:latest
   ```

---

## 📈 扩展性

### 水平扩展

```bash
# 手动扩展
kubectl scale deployment perplexica --replicas=3

# 自动扩展（HPA）
kubectl autoscale deployment perplexica \
  --cpu-percent=70 \
  --min=1 \
  --max=5
```

### 垂直扩展

修改 `k8s/deployment.yaml` 中的资源限制：

```yaml
resources:
  requests:
    cpu: "1000m"
    memory: "2Gi"
  limits:
    cpu: "4000m"
    memory: "8Gi"
```

---

## 🔗 与下游工具集成

### Python 示例

```python
import requests

def search_with_perplexica(query: str, include_answer: bool = False):
    """使用 Perplexica 的 Tavily 兼容 API 搜索"""
    url = "http://perplexica-service/api/tavily"
    
    payload = {
        "query": query,
        "search_depth": "advanced" if include_answer else "basic",
        "include_answer": include_answer,
        "include_raw_content": True,
        "max_results": 10
    }
    
    response = requests.post(url, json=payload)
    return response.json()

# 使用示例
result = search_with_perplexica("AI in healthcare", include_answer=True)
print(result['answer'])
for r in result['results']:
    print(f"- {r['title']}: {r['url']}")
```

### Node.js 示例

```javascript
const axios = require('axios');

async function searchWithPerplexica(query, includeAnswer = false) {
  const response = await axios.post('http://perplexica-service/api/tavily', {
    query,
    search_depth: includeAnswer ? 'advanced' : 'basic',
    include_answer: includeAnswer,
    include_raw_content: true,
    max_results: 10
  });
  
  return response.data;
}

// 使用示例
searchWithPerplexica('AI in healthcare', true)
  .then(result => {
    console.log('Answer:', result.answer);
    result.results.forEach(r => {
      console.log(`- ${r.title}: ${r.url}`);
    });
  });
```

---

## 📝 对比：SearCrawl vs Perplexica

| 特性 | SearCrawl | Perplexica |
|------|-----------|------------|
| Web UI | ❌ 无 | ✅ 完整的聊天界面 |
| LLM 集成 | ❌ 无 | ✅ 多提供商支持 |
| 答案生成 | ❌ 无 | ✅ 自动生成 |
| 图片搜索 | ⚠️  有限 | ✅ 原生支持 |
| 文件上传 | ❌ 无 | ✅ PDF/文档分析 |
| 爬取速度 | ⚠️  慢 (67秒/页) | ✅ 快速 |
| 图片提取 | ❌ 失败 | ✅ 工作正常 |
| API 稳定性 | ⚠️  不稳定 | ✅ 稳定 |
| 社区支持 | ⚠️  有限 | ✅ 活跃 |

---

## ❓ 常见问题

### Q: Tavily API 与原版有何不同？

A: 我们的实现提供了 Tavily 的核心功能：
- ✅ 搜索结果返回
- ✅ 答案生成
- ✅ 相关性评分
- ✅ 原始内容提取
- ⚠️  部分高级功能可能有差异

### Q: 如何配置使用本地 LLM？

A: 修改部署配置，添加 Ollama 支持：

```yaml
env:
- name: OLLAMA_BASE_URL
  value: "http://ollama-service:11434"
```

### Q: 性能如何优化？

A:
1. 增加副本数（水平扩展）
2. 使用更快的 LLM 模型
3. 配置缓存
4. 使用 CDN 加速静态资源

---

## 📚 相关资源

- [Perplexica GitHub](https://github.com/ItzCrazyKns/Perplexica)
- [Tavily API 文档](https://docs.tavily.com/)
- [Azure AKS 文档](https://docs.microsoft.com/azure/aks/)
- [Kubernetes 文档](https://kubernetes.io/docs/)

---

## 🤝 贡献

发现问题或有改进建议？欢迎提交 Issue 或 Pull Request！

---

**部署成功后，你就拥有了一个强大的、Tavily 兼容的 AI 搜索引擎！** 🎉


