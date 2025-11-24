# 🔐 Perplexica API 访问方式说明

## 当前访问方式

### ✅ 你的理解完全正确！

**当前状态**: 
- ❌ **没有 API Key 验证**
- ❌ **没有公网 IP**
- ✅ **只能从 AKS 内部访问**

---

## 📊 当前配置

### Service 类型

```yaml
apiVersion: v1
kind: Service
metadata:
  name: perplexica-service
spec:
  type: ClusterIP  ← 只有内部 IP，无公网访问
  ports:
  - port: 80
    targetPort: 3000
```

### 访问限制

```
ClusterIP:
  ✅ AKS 集群内部的 Pod 可以访问
  ✅ 同一命名空间的服务可以访问
  ❌ 集群外部无法访问
  ❌ 公网无法访问
```

---

## 🔍 当前的三种访问方式

### 方式 1: AKS 内部的其他服务调用 ⭐ 推荐用于生产

这是最安全的方式，也是你目前唯一的选择。

#### 场景示例

假设你有另一个服务 `my-app` 在同一个 AKS 集群中：

```python
# my-app 的 Python 代码
import requests

# 直接使用 Service 名称访问
response = requests.post(
    "http://perplexica-service/api/tavily",  # 内部 DNS 解析
    json={
        "query": "AI trends",
        "max_results": 10
    }
)

results = response.json()
```

#### 工作原理

```
┌─────────────────────────────────────────────────────┐
│  AKS 集群                                            │
│                                                      │
│  ┌──────────────┐         ┌──────────────────┐    │
│  │  my-app      │         │  perplexica      │    │
│  │  Pod         │ ─────→  │  Service         │    │
│  │              │  HTTP    │  (ClusterIP)     │    │
│  └──────────────┘         └──────────────────┘    │
│                                   │                 │
│                                   ↓                 │
│                            ┌──────────────────┐    │
│                            │  perplexica      │    │
│                            │  Pod             │    │
│                            └──────────────────┘    │
│                                                      │
└─────────────────────────────────────────────────────┘
```

#### DNS 解析

Kubernetes 内部 DNS 自动解析：

```
服务名称: perplexica-service
完整域名: perplexica-service.default.svc.cluster.local

可以使用的 URL:
  ✅ http://perplexica-service/api/tavily
  ✅ http://perplexica-service.default/api/tavily
  ✅ http://perplexica-service.default.svc.cluster.local/api/tavily
```

#### 不同命名空间的访问

如果 `my-app` 在不同的命名空间：

```python
# my-app 在 "production" 命名空间
# perplexica 在 "default" 命名空间

response = requests.post(
    "http://perplexica-service.default/api/tavily",  # 需要指定命名空间
    json={"query": "test"}
)
```

#### 实际部署示例

```yaml
# my-app-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: my-app
        image: my-registry/my-app:latest
        env:
        - name: SEARCH_API_URL
          value: "http://perplexica-service/api/tavily"
```

---

### 方式 2: kubectl port-forward (临时测试/开发)

**用途**: 本地开发和测试

#### 使用步骤

```bash
# 1. 建立端口转发
kubectl port-forward svc/perplexica-service 8080:80

# 输出
Forwarding from 127.0.0.1:8080 -> 3000
Forwarding from [::1]:8080 -> 3000

# 2. 在本地调用（另一个终端）
curl -X POST http://localhost:8080/api/tavily \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

#### 工作原理

```
你的电脑                     AKS 集群
   │                            │
   │  kubectl port-forward      │
   │ ────────────────────────→  │
   │                            │
   │     SSH/K8s Tunnel         │
   │ ←─────────────────────────→│
   │                            │
localhost:8080 ─────────────→ perplexica-service
```

#### 特点

```
✅ 不需要修改配置
✅ 适合本地开发测试
✅ 安全（通过 K8s 认证）
❌ 不适合生产环境
❌ 连接断开需要重新建立
❌ 只能你自己访问
```

---

### 方式 3: kubectl exec 进入 Pod 内部

**用途**: 调试和故障排查

#### 使用步骤

```bash
# 1. 找到任意 Pod
kubectl get pods

# 输出
NAME                          READY   STATUS
perplexica-7d8f9c8b5d-abc12   1/1     Running
my-app-6b8f7c5d4e-xyz89       1/1     Running

# 2. 进入 Pod
kubectl exec -it my-app-6b8f7c5d4e-xyz89 -- /bin/sh

# 3. 在 Pod 内部测试 API
curl -X POST http://perplexica-service/api/tavily \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'

# 4. 退出
exit
```

#### 特点

```
✅ 测试内部网络连接
✅ 验证 DNS 解析
✅ 调试网络问题
❌ 仅用于调试
```

---

## 🌐 如何开放到外部访问？

如果你想让外部（非 AKS 内部）访问，有以下几种方式：

### 选项 1: LoadBalancer (公网 IP)

#### 配置

```yaml
apiVersion: v1
kind: Service
metadata:
  name: perplexica-service
spec:
  type: LoadBalancer  # 改为 LoadBalancer
  ports:
  - port: 80
    targetPort: 3000
```

#### 获取公网 IP

```bash
kubectl apply -f k8s/deployment.yaml
kubectl get svc perplexica-service

# 输出
NAME                 TYPE           EXTERNAL-IP
perplexica-service   LoadBalancer   20.123.45.67  ← 公网 IP
```

#### 访问

```bash
curl -X POST http://20.123.45.67/api/tavily \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

#### 费用

```
Azure LoadBalancer 费用:
  - 基础费用: ~$18.25/月
  - 数据处理费: 按流量计费
```

#### 安全考虑

```
⚠️  公网 IP = 任何人都可以访问！

必须配合:
  ✅ API Key 验证
  ✅ IP 白名单
  ✅ HTTPS
  ✅ 速率限制
```

---

### 选项 2: Ingress (域名访问)

#### 配置

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: perplexica-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: perplexica-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: perplexica-service
            port:
              number: 80
```

#### 访问

```bash
curl -X POST https://api.yourdomain.com/api/tavily \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

#### 优势

```
✅ 自定义域名
✅ 自动 HTTPS
✅ 证书管理
✅ 更专业
```

#### 需要

```
1. 域名
2. Ingress Controller (如 nginx-ingress)
3. cert-manager (可选，用于 SSL)
```

---

### 选项 3: Azure API Management

#### 架构

```
客户端
  ↓
Azure API Management (API Gateway)
  ↓ (内部网络)
Perplexica Service (ClusterIP)
```

#### 优势

```
✅ 保持 ClusterIP (最安全)
✅ API 密钥管理
✅ 速率限制
✅ 分析和监控
✅ 缓存
✅ 转换和路由
```

#### 费用

```
Azure API Management:
  - 开发者层: ~$50/月
  - 标准层: ~$690/月
```

---

## 📊 访问方式对比

| 方式 | 安全性 | 复杂度 | 费用 | 适用场景 |
|------|--------|--------|------|---------|
| **ClusterIP** (当前) | ⭐⭐⭐⭐⭐ | ⭐ | $0 | 内部服务间调用 |
| **LoadBalancer** | ⭐⭐ | ⭐⭐ | ~$18/月 | 简单公网访问 |
| **Ingress** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ~$50/月* | 域名 + HTTPS |
| **API Management** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ~$50+/月 | 企业级 API |
| **port-forward** | ⭐⭐⭐⭐ | ⭐ | $0 | 开发测试 |

*Ingress Controller 费用

---

## 🎯 推荐配置

### 场景 1: 只有内部服务调用 ⭐ 当前

**配置**: ClusterIP (不变)

```yaml
type: ClusterIP
```

**原因**:
- ✅ 最安全
- ✅ 无额外费用
- ✅ 简单直接
- ✅ 符合你的需求

**访问方式**:
```python
# 在 AKS 内部的其他服务中
response = requests.post(
    "http://perplexica-service/api/tavily",
    json={"query": "test"}
)
```

---

### 场景 2: 需要少数外部客户端访问

**配置**: LoadBalancer + API Key

```yaml
type: LoadBalancer
env:
  - name: API_KEYS
    valueFrom:
      secretKeyRef:
        name: api-keys
        key: keys
```

**原因**:
- ✅ 简单配置
- ✅ 成本较低
- ⚠️ 需要实现 API Key 验证

---

### 场景 3: 需要对外提供 API 服务

**配置**: Ingress + HTTPS + API Key

```yaml
type: ClusterIP  # 保持内部
# + Ingress with HTTPS
# + API Key validation
```

**原因**:
- ✅ 专业
- ✅ 安全 (HTTPS)
- ✅ 可以用自己的域名
- ✅ 更好的管理

---

## 💡 实际使用示例

### 内部服务调用示例

#### Python 服务

```python
# app.py
import requests
import os

SEARCH_API_URL = os.getenv(
    'SEARCH_API_URL',
    'http://perplexica-service/api/tavily'
)

def search(query: str, max_results: int = 10):
    """调用搜索 API"""
    response = requests.post(
        SEARCH_API_URL,
        json={
            'query': query,
            'max_results': max_results,
            'include_raw_content': True
        },
        timeout=300
    )
    response.raise_for_status()
    return response.json()

# 使用
if __name__ == '__main__':
    results = search("Python tutorials", max_results=5)
    for result in results['results']:
        print(f"- {result['title']}: {result['url']}")
```

#### Node.js 服务

```javascript
// search-client.js
const axios = require('axios');

const SEARCH_API_URL = process.env.SEARCH_API_URL || 
    'http://perplexica-service/api/tavily';

async function search(query, maxResults = 10) {
    const response = await axios.post(SEARCH_API_URL, {
        query,
        max_results: maxResults,
        include_raw_content: true
    }, {
        timeout: 300000
    });
    
    return response.data;
}

// 使用
(async () => {
    const results = await search('JavaScript frameworks', 5);
    results.results.forEach(result => {
        console.log(`- ${result.title}: ${result.url}`);
    });
})();
```

#### Go 服务

```go
// search_client.go
package main

import (
    "bytes"
    "encoding/json"
    "net/http"
    "os"
    "time"
)

type SearchRequest struct {
    Query              string `json:"query"`
    MaxResults         int    `json:"max_results"`
    IncludeRawContent  bool   `json:"include_raw_content"`
}

func search(query string, maxResults int) (map[string]interface{}, error) {
    apiURL := os.Getenv("SEARCH_API_URL")
    if apiURL == "" {
        apiURL = "http://perplexica-service/api/tavily"
    }
    
    reqBody := SearchRequest{
        Query:             query,
        MaxResults:        maxResults,
        IncludeRawContent: true,
    }
    
    jsonData, _ := json.Marshal(reqBody)
    
    client := &http.Client{Timeout: 300 * time.Second}
    resp, err := client.Post(apiURL, "application/json", bytes.NewBuffer(jsonData))
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    
    var result map[string]interface{}
    json.NewDecoder(resp.Body).Decode(&result)
    
    return result, nil
}
```

---

## 🔒 安全最佳实践

### 当前配置（ClusterIP）

#### 已有的安全措施 ✅

```
1. 网络隔离
   - 只有集群内部可以访问
   - 外部完全无法访问

2. Kubernetes RBAC
   - 基于角色的访问控制
   - Pod 间通信受限

3. 命名空间隔离
   - 可以进一步限制访问范围
```

#### 可选的额外安全措施

```yaml
# NetworkPolicy - 限制只有特定 Pod 可以访问
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: perplexica-access
spec:
  podSelector:
    matchLabels:
      app: perplexica
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          access: perplexica  # 只有这个标签的 Pod 能访问
    ports:
    - protocol: TCP
      port: 3000
```

---

## 📝 总结

### 你的当前状态

```
✅ Service Type: ClusterIP
✅ 访问范围: 仅 AKS 内部
✅ API Key: 未实现（不需要）
✅ 安全性: 高（网络隔离）
✅ 费用: 无额外费用
```

### 适用场景

```
✅ 内部微服务调用
✅ 后端服务集成
✅ 数据处理管道
✅ 定时任务/Cron Jobs
❌ 直接的公网 API
❌ 前端直接调用
❌ 第三方集成（外部）
```

### 如何在内部使用

```python
# 任何在 AKS 集群内的 Pod 都可以这样调用
import requests

response = requests.post(
    "http://perplexica-service/api/tavily",
    json={
        "query": "your search query",
        "max_results": 10
    }
)

results = response.json()
```

### 下一步

如果你需要：

1. ✅ **保持现状** - 不需要改动，当前配置最安全
2. ✅ **开放公网** - 实现 API Key + LoadBalancer
3. ✅ **专业 API** - 配置 Ingress + HTTPS + 域名

告诉我你的选择，我可以帮你实现！🚀

---

**文档更新时间**: 2025-11-17  
**当前配置**: ClusterIP (仅内部访问)

