# Azure 企业环境部署指南 - ODR + Perplexica

## 📋 目录

1. [架构概述](#架构概述)
2. [前置准备](#前置准备)
3. [步骤1：创建AKS集群](#步骤1创建aks集群)
4. [步骤2：部署Perplexica](#步骤2部署perplexica)
5. [步骤3：部署ODR](#步骤3部署odr)
6. [步骤4：配置公网访问](#步骤4配置公网访问)
7. [步骤5：配置认证](#步骤5配置认证)
8. [步骤6：测试验证](#步骤6测试验证)
9. [故障排查](#故障排查)
10. [维护和监控](#维护和监控)

---

## 架构概述

### 当前架构（个人环境）
```
Internet
    ↓
Cloudflare Tunnel (不可用于企业环境)
    ↓
AKS Cluster
    ├── ODR (Deep Research)
    └── Perplexica (AI Search)
```

### 企业环境架构（推荐）
```
Internet
    ↓
Azure Application Gateway + WAF (推荐)
或 Azure Front Door (全球加速)
    ↓
AKS Cluster (Private/Public)
    ├── ODR Namespace
    │   └── open-deep-research deployment
    └── Default Namespace
        └── perplexica deployment
```

### Azure服务选择对比

| 功能 | 个人环境 | 企业环境选项1 | 企业环境选项2 | 企业环境选项3 |
|------|---------|--------------|--------------|--------------|
| **入口访问** | Cloudflare Tunnel | Azure Application Gateway | Azure Front Door | AKS Ingress + Public IP |
| **WAF防护** | Cloudflare | Azure WAF (App Gateway) | Azure WAF (Front Door) | 第三方WAF |
| **SSL证书** | Cloudflare自动 | Azure Managed Cert | Let's Encrypt | 企业CA证书 |
| **负载均衡** | Cloudflare | Azure LB (L4/L7) | Front Door | NGINX Ingress |
| **认证** | JWT手动 | Azure AD | Azure AD + OAuth | 企业SSO |
| **成本** | 免费 | ~$150/月 | ~$300/月 | ~$59/月 |

**本文档推荐方案**：
- **测试/开发环境**：AKS Ingress + LoadBalancer（~$59/月）
- **生产环境**：Azure Application Gateway + WAF（~$209/月，含WAF防护）

---

## 前置准备

### 1. Azure订阅权限
```bash
# 需要的权限
- 创建资源组
- 创建AKS集群
- 创建虚拟网络
- 创建Application Gateway
- 创建Managed Identity
- 创建Key Vault（可选）
```

### 2. 本地工具安装

#### Azure CLI
```bash
# macOS
brew install azure-cli

# Windows
winget install Microsoft.AzureCLI

# 登录
az login
az account set --subscription "YOUR_SUBSCRIPTION_ID"
```

#### kubectl
```bash
# macOS
brew install kubectl

# Windows
winget install Kubernetes.kubectl
```

#### Helm（可选）
```bash
# macOS
brew install helm

# Windows
winget install Helm.Helm
```

### 3. 环境变量配置
```bash
# 保存为 azure_env.sh
export RESOURCE_GROUP="rg-odr-prod"
export LOCATION="eastus"  # 或 "southeastasia", "westeurope" 等
export AKS_CLUSTER_NAME="aks-odr-cluster"
export ACR_NAME="acrodrprod"  # 必须全局唯一
export APP_GATEWAY_NAME="appgw-odr"
export VNET_NAME="vnet-odr"
```

### 4. API Keys准备
```bash
# 需要准备的密钥
OPENAI_API_KEY="sk-..."           # OpenAI API密钥
ANTHROPIC_API_KEY="sk-ant-..."    # Anthropic API密钥（可选）
PERPLEXICA_API_KEY="your-key"     # Perplexica自定义密钥
ODR_AUTH_SECRET="random-secret"   # ODR JWT签名密钥（32字符随机字符串）
```

---

## 步骤1：创建AKS集群

### 1.1 创建资源组
```bash
# 加载环境变量
source azure_env.sh

# 创建资源组
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

echo "✅ 资源组创建完成"
```

### 1.2 创建虚拟网络
```bash
# 创建虚拟网络（用于AKS和Application Gateway）
az network vnet create \
  --resource-group $RESOURCE_GROUP \
  --name $VNET_NAME \
  --address-prefixes 10.0.0.0/16 \
  --subnet-name aks-subnet \
  --subnet-prefix 10.0.1.0/24

# 创建Application Gateway子网
az network vnet subnet create \
  --resource-group $RESOURCE_GROUP \
  --vnet-name $VNET_NAME \
  --name appgw-subnet \
  --address-prefix 10.0.2.0/24

echo "✅ 虚拟网络创建完成"
```

### 1.3 创建AKS集群
```bash
# 创建AKS集群（经济优化配置）
# 使用B2s节点：2核4GB，适合轻量级工作负载，成本优化
az aks create \
  --resource-group $RESOURCE_GROUP \
  --name $AKS_CLUSTER_NAME \
  --location $LOCATION \
  --node-count 1 \
  --node-vm-size Standard_B2s \
  --vnet-subnet-id $(az network vnet subnet show --resource-group $RESOURCE_GROUP --vnet-name $VNET_NAME --name aks-subnet --query id -o tsv) \
  --network-plugin azure \
  --enable-managed-identity \
  --enable-addons monitoring \
  --generate-ssh-keys

# 获取集群凭证
az aks get-credentials \
  --resource-group $RESOURCE_GROUP \
  --name $AKS_CLUSTER_NAME \
  --overwrite-existing

# 验证连接
kubectl get nodes

echo "✅ AKS集群创建完成"
echo "💡 使用Standard_B2s (2核4GB)，月成本约$31"
```

### 1.4 准备Docker镜像

**重要**：当前环境使用的是经过优化的自定义镜像，包含rate limiting和Perplexica集成等功能。

#### 方案A：直接使用Docker Hub镜像（推荐）

当前已有的优化镜像在Docker Hub公开可用：
```bash
# ODR镜像（包含rate limiting优化）
ODR_IMAGE="shankswhite/open-deep-research:v1.10-rate-limit"

# Perplexica镜像（包含Tavily API支持）
PERPLEXICA_IMAGE="shankswhite/perplexica:tavily-v1.1"

echo "✅ 使用现有Docker Hub镜像，无需额外配置"
```

**✅ 镜像验证状态（2024-11-24）**：
- ODR镜像：已推送，支持AMD64/ARM64
- Perplexica镜像：已推送，仅支持AMD64（Azure/AWS标准架构）
- AKS集群验证：两个镜像均正常运行
- 镜像ID：
  - ODR: sha256:... (当前版本)
  - Perplexica: sha256:47316c75897f738ba81b15e545a5028a62e8a5439d9b42a9f7c71c9b1cf3d1b6

**注意**：如果在Apple Silicon (ARM64) Mac上测试，Perplexica镜像可能无法本地拉取，但这不影响Azure AMD64环境的部署。

#### 方案B：推送到Azure Container Registry（企业私有）

如果需要使用私有容器镜像：

```bash
# 1. 创建ACR
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Standard

# 2. 登录到ACR
az acr login --name $ACR_NAME

# 3. 从Docker Hub拉取并推送到ACR
docker pull shankswhite/open-deep-research:v1.10-rate-limit
docker pull shankswhite/perplexica:tavily-v1.1

docker tag shankswhite/open-deep-research:v1.10-rate-limit $ACR_NAME.azurecr.io/open-deep-research:v1.10
docker tag shankswhite/perplexica:tavily-v1.1 $ACR_NAME.azurecr.io/perplexica:v1.1

docker push $ACR_NAME.azurecr.io/open-deep-research:v1.10
docker push $ACR_NAME.azurecr.io/perplexica:v1.1

# 4. 将AKS与ACR集成
az aks update \
  --resource-group $RESOURCE_GROUP \
  --name $AKS_CLUSTER_NAME \
  --attach-acr $ACR_NAME

echo "✅ 镜像已推送到ACR"
```

#### 镜像包含的优化

**ODR镜像 (shankswhite/open-deep-research:v1.10-rate-limit)**：
- ✅ Rate limiting配置（避免API限流）
- ✅ Perplexica集成支持
- ✅ 搜索延迟优化（15秒延迟）
- ✅ 并发控制（2个并发研究单元）

**Perplexica镜像 (shankswhite/perplexica:tavily-v1.1)**：
- ✅ Tavily API兼容接口
- ✅ 无需持久化存储
- ✅ 优化的搜索引擎配置

---

## 步骤2：部署Perplexica

### 2.1 创建命名空间和密钥
```bash
# 创建Kubernetes密钥
kubectl create secret generic perplexica-secrets \
  --from-literal=OPENAI_API_KEY="$OPENAI_API_KEY" \
  --from-literal=ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  -n default

echo "✅ Perplexica密钥创建完成"
```

### 2.2 创建Perplexica ConfigMap
```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: perplexica-config
  namespace: default
data:
  # Perplexica配置
  PORT: "3001"
  SIMILARITY_MEASURE: "cosine"
  CHAT_MODEL_PROVIDER: "openai"
  CHAT_MODEL: "gpt-4o-mini"
  EMBEDDING_MODEL_PROVIDER: "openai"
  EMBEDDING_MODEL: "text-embedding-3-small"
EOF

echo "✅ Perplexica ConfigMap创建完成"
```

### 2.3 部署Perplexica
```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: perplexica
  namespace: default
  labels:
    app: perplexica
spec:
  replicas: 1
  selector:
    matchLabels:
      app: perplexica
  template:
    metadata:
      labels:
        app: perplexica
    spec:
      containers:
      - name: perplexica
        image: shankswhite/perplexica:tavily-v1.1
        ports:
        - containerPort: 3001
        env:
        - name: PORT
          valueFrom:
            configMapKeyRef:
              name: perplexica-config
              key: PORT
        - name: SIMILARITY_MEASURE
          valueFrom:
            configMapKeyRef:
              name: perplexica-config
              key: SIMILARITY_MEASURE
        - name: CHAT_MODEL_PROVIDER
          valueFrom:
            configMapKeyRef:
              name: perplexica-config
              key: CHAT_MODEL_PROVIDER
        - name: CHAT_MODEL
          valueFrom:
            configMapKeyRef:
              name: perplexica-config
              key: CHAT_MODEL
        - name: EMBEDDING_MODEL_PROVIDER
          valueFrom:
            configMapKeyRef:
              name: perplexica-config
              key: EMBEDDING_MODEL_PROVIDER
        - name: EMBEDDING_MODEL
          valueFrom:
            configMapKeyRef:
              name: perplexica-config
              key: EMBEDDING_MODEL
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: perplexica-secrets
              key: OPENAI_API_KEY
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: perplexica-secrets
              key: ANTHROPIC_API_KEY
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "250m"
---
apiVersion: v1
kind: Service
metadata:
  name: perplexica-service
  namespace: default
spec:
  selector:
    app: perplexica
  ports:
  - protocol: TCP
    port: 80
    targetPort: 3001
  type: ClusterIP
EOF

# 等待Perplexica就绪
kubectl wait --for=condition=ready pod -l app=perplexica -n default --timeout=300s

echo "✅ Perplexica部署完成"
```

### 2.4 验证Perplexica
```bash
# 测试Perplexica
kubectl run test-perplexica --rm -i --tty --image=curlimages/curl -- sh -c "
curl -X POST http://perplexica-service.default.svc.cluster.local/search \
  -H 'Content-Type: application/json' \
  -d '{
    \"query\": \"test\",
    \"chat_history\": [],
    \"chat_model_provider\": \"openai\",
    \"chat_model\": \"gpt-4o-mini\"
  }'
"

echo "✅ Perplexica测试完成"
```

---

## 步骤3：部署ODR

### 3.1 创建命名空间
```bash
kubectl create namespace deep-research

echo "✅ deep-research命名空间创建完成"
```

### 3.2 创建ODR密钥
```bash
# 生成JWT签名密钥（32字符随机字符串）
export ODR_AUTH_SECRET=$(openssl rand -hex 16)

# 创建Kubernetes密钥
kubectl create secret generic odr-secrets \
  --from-literal=OPENAI_API_KEY="$OPENAI_API_KEY" \
  --from-literal=ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  --from-literal=LANGSMITH_API_KEY="" \
  --from-literal=LANGGRAPH_AUTH_SECRET="$ODR_AUTH_SECRET" \
  -n deep-research

# 保存JWT密钥（重要！用于客户端认证）
echo "ODR_AUTH_SECRET=$ODR_AUTH_SECRET" >> odr_jwt_secret.txt
echo "⚠️  重要：JWT密钥已保存到 odr_jwt_secret.txt，请妥善保管！"

echo "✅ ODR密钥创建完成"
```

### 3.3 创建ODR ConfigMap
```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: open-deep-research-config
  namespace: deep-research
data:
  # Perplexica配置
  USE_PERPLEXICA: "true"
  PERPLEXICA_API_URL: "http://perplexica-service.default.svc.cluster.local"
  
  # 模型配置（使用o4-mini避免rate limit）
  ANTHROPIC_MODEL: "claude-sonnet-4-20250514"
  OPENAI_MODEL: "o4-mini"
  
  # 搜索配置（降低频率避免触发反爬虫）
  MAX_CONCURRENT_RESEARCH_UNITS: "2"
  SEARCH_REQUEST_DELAY: "15.0"
  SEARCH_REQUEST_DELAY_RANDOM: "5.0"
  MAX_RESULTS_PER_QUERY: "3"
  MAX_RESEARCHER_ITERATIONS: "4"
  MAX_REACT_TOOL_CALLS: "8"
  
  # 其他配置
  SEARCH_API: "tavily"
  LOG_LEVEL: "INFO"
EOF

echo "✅ ODR ConfigMap创建完成"
```

### 3.4 部署ODR
```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: open-deep-research
  namespace: deep-research
  labels:
    app: open-deep-research
spec:
  replicas: 1
  selector:
    matchLabels:
      app: open-deep-research
  template:
    metadata:
      labels:
        app: open-deep-research
    spec:
      containers:
      - name: open-deep-research
        image: shankswhite/open-deep-research:v1.10-rate-limit
        ports:
        - containerPort: 8123
        env:
        # API密钥（从Secret）
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: odr-secrets
              key: OPENAI_API_KEY
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: odr-secrets
              key: ANTHROPIC_API_KEY
        - name: LANGSMITH_API_KEY
          valueFrom:
            secretKeyRef:
              name: odr-secrets
              key: LANGSMITH_API_KEY
        - name: LANGGRAPH_AUTH_SECRET
          valueFrom:
            secretKeyRef:
              name: odr-secrets
              key: LANGGRAPH_AUTH_SECRET
        
        # 配置（从ConfigMap）
        - name: USE_PERPLEXICA
          valueFrom:
            configMapKeyRef:
              name: open-deep-research-config
              key: USE_PERPLEXICA
        - name: PERPLEXICA_API_URL
          valueFrom:
            configMapKeyRef:
              name: open-deep-research-config
              key: PERPLEXICA_API_URL
        - name: ANTHROPIC_MODEL
          valueFrom:
            configMapKeyRef:
              name: open-deep-research-config
              key: ANTHROPIC_MODEL
        - name: OPENAI_MODEL
          valueFrom:
            configMapKeyRef:
              name: open-deep-research-config
              key: OPENAI_MODEL
        - name: MAX_CONCURRENT_RESEARCH_UNITS
          valueFrom:
            configMapKeyRef:
              name: open-deep-research-config
              key: MAX_CONCURRENT_RESEARCH_UNITS
        - name: SEARCH_REQUEST_DELAY
          valueFrom:
            configMapKeyRef:
              name: open-deep-research-config
              key: SEARCH_REQUEST_DELAY
        - name: SEARCH_REQUEST_DELAY_RANDOM
          valueFrom:
            configMapKeyRef:
              name: open-deep-research-config
              key: SEARCH_REQUEST_DELAY_RANDOM
        - name: MAX_RESULTS_PER_QUERY
          valueFrom:
            configMapKeyRef:
              name: open-deep-research-config
              key: MAX_RESULTS_PER_QUERY
        - name: MAX_RESEARCHER_ITERATIONS
          valueFrom:
            configMapKeyRef:
              name: open-deep-research-config
              key: MAX_RESEARCHER_ITERATIONS
        - name: MAX_REACT_TOOL_CALLS
          valueFrom:
            configMapKeyRef:
              name: open-deep-research-config
              key: MAX_REACT_TOOL_CALLS
        - name: SEARCH_API
          valueFrom:
            configMapKeyRef:
              name: open-deep-research-config
              key: SEARCH_API
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: open-deep-research-config
              key: LOG_LEVEL
        
        resources:
          requests:
            memory: "512Mi"
            cpu: "200m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        
        livenessProbe:
          httpGet:
            path: /ok
            port: 8123
          initialDelaySeconds: 30
          periodSeconds: 30
        
        readinessProbe:
          httpGet:
            path: /ok
            port: 8123
          initialDelaySeconds: 10
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: open-deep-research-service
  namespace: deep-research
spec:
  selector:
    app: open-deep-research
  ports:
  - protocol: TCP
    port: 8123
    targetPort: 8123
  type: ClusterIP
EOF

# 等待ODR就绪
kubectl wait --for=condition=ready pod -l app=open-deep-research -n deep-research --timeout=300s

echo "✅ ODR部署完成"
```

### 3.5 验证ODR
```bash
# 测试ODR健康检查
kubectl run test-odr --rm -i --tty --image=curlimages/curl -n deep-research -- sh -c "
curl http://open-deep-research-service.deep-research.svc.cluster.local:8123/ok
"

echo "✅ ODR测试完成"
```

---

## 步骤4：配置公网访问

### 方案A：Azure Application Gateway（推荐）

#### 4.1 安装AGIC（Application Gateway Ingress Controller）
```bash
# 创建Public IP
az network public-ip create \
  --resource-group $RESOURCE_GROUP \
  --name pip-appgw-odr \
  --allocation-method Static \
  --sku Standard

# 创建Application Gateway
az network application-gateway create \
  --name $APP_GATEWAY_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_v2 \
  --public-ip-address pip-appgw-odr \
  --vnet-name $VNET_NAME \
  --subnet appgw-subnet \
  --capacity 2 \
  --http-settings-cookie-based-affinity Disabled \
  --frontend-port 80 \
  --http-settings-port 80 \
  --http-settings-protocol Http

# 启用AGIC
az aks enable-addons \
  --resource-group $RESOURCE_GROUP \
  --name $AKS_CLUSTER_NAME \
  --addons ingress-appgw \
  --appgw-id $(az network application-gateway show --resource-group $RESOURCE_GROUP --name $APP_GATEWAY_NAME --query id -o tsv)

echo "✅ Application Gateway配置完成"
```

#### 4.2 创建Ingress资源
```bash
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: odr-ingress
  namespace: deep-research
  annotations:
    kubernetes.io/ingress.class: azure/application-gateway
    appgw.ingress.kubernetes.io/ssl-redirect: "false"
spec:
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: open-deep-research-service
            port:
              number: 8123
EOF

# 获取公网IP
export ODR_PUBLIC_IP=$(az network public-ip show \
  --resource-group $RESOURCE_GROUP \
  --name pip-appgw-odr \
  --query ipAddress -o tsv)

echo "✅ Ingress配置完成"
echo "🌐 ODR公网访问地址: http://$ODR_PUBLIC_IP"
```

#### 4.3 配置HTTPS（可选但推荐）
```bash
# 方法1：使用cert-manager + Let's Encrypt（免费）
# 安装cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# 创建Let's Encrypt ClusterIssuer
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@company.com  # 修改为您的邮箱
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: azure/application-gateway
EOF

# 更新Ingress启用HTTPS
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: odr-ingress
  namespace: deep-research
  annotations:
    kubernetes.io/ingress.class: azure/application-gateway
    cert-manager.io/cluster-issuer: letsencrypt-prod
    appgw.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - odr.your-company.com  # 修改为您的域名
    secretName: odr-tls-cert
  rules:
  - host: odr.your-company.com  # 修改为您的域名
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: open-deep-research-service
            port:
              number: 8123
EOF

echo "✅ HTTPS配置完成"
```

### 方案B：简单LoadBalancer（临时测试用）
```bash
# 将ODR Service改为LoadBalancer类型
kubectl patch service open-deep-research-service -n deep-research -p '{"spec":{"type":"LoadBalancer"}}'

# 等待分配公网IP
kubectl get service open-deep-research-service -n deep-research -w

# 获取公网IP
export ODR_PUBLIC_IP=$(kubectl get service open-deep-research-service -n deep-research -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

echo "✅ LoadBalancer配置完成"
echo "🌐 ODR公网访问地址: http://$ODR_PUBLIC_IP:8123"
```

---

## 步骤5：配置认证

### 5.1 生成JWT Token
```bash
# 下载JWT生成脚本
cat > generate_jwt_token.py << 'EOF'
#!/usr/bin/env python3
import jwt
import sys
from datetime import datetime, timedelta

def generate_jwt_token(secret: str, expires_days: int = 365):
    """生成JWT token"""
    payload = {
        "sub": "enterprise-user",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(days=expires_days)
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 generate_jwt_token.py <SECRET>")
        sys.exit(1)
    
    secret = sys.argv[1]
    token = generate_jwt_token(secret)
    print(token)
EOF

chmod +x generate_jwt_token.py

# 生成Token
export ODR_JWT_TOKEN=$(python3 generate_jwt_token.py "$ODR_AUTH_SECRET")

echo "✅ JWT Token生成完成"
echo "🔑 JWT Token: $ODR_JWT_TOKEN"

# 保存到文件
echo "ODR_JWT_TOKEN=$ODR_JWT_TOKEN" >> odr_jwt_secret.txt
```

### 5.2 配置Azure AD认证（可选，企业推荐）
```bash
# 创建Azure AD应用注册
az ad app create \
  --display-name "ODR Enterprise App" \
  --sign-in-audience AzureADMyOrg

# 获取应用ID
export APP_ID=$(az ad app list --display-name "ODR Enterprise App" --query [0].appId -o tsv)

# 创建Service Principal
az ad sp create --id $APP_ID

# 配置Redirect URI
az ad app update --id $APP_ID \
  --web-redirect-uris "http://$ODR_PUBLIC_IP/auth/callback"

echo "✅ Azure AD应用配置完成"
echo "📝 应用ID: $APP_ID"
```

---

## 步骤6：测试验证

### 6.1 健康检查
```bash
# 测试ODR健康检查
curl http://$ODR_PUBLIC_IP/ok

# 预期输出：ok
```

### 6.2 完整功能测试
```bash
# 下载客户端脚本（从您的项目）
# 假设odr_research_client.py已经存在

# 配置环境变量
export ODR_API_URL="http://$ODR_PUBLIC_IP"  # 或 https://odr.your-company.com
export ODR_JWT_TOKEN="$ODR_JWT_TOKEN"

# 测试研究功能
python3 odr_research_client.py "Test query for Azure deployment"

# 检查生成的报告
ls -lh odr_reports/
```

### 6.3 性能测试
```bash
# 使用Apache Bench测试
ab -n 10 -c 2 -H "Authorization: Bearer $ODR_JWT_TOKEN" http://$ODR_PUBLIC_IP/ok

# 使用hey测试（更现代）
hey -n 10 -c 2 -H "Authorization: Bearer $ODR_JWT_TOKEN" http://$ODR_PUBLIC_IP/ok
```

---

## 故障排查

### 问题1：Pod无法启动
```bash
# 查看Pod状态
kubectl get pods -n deep-research
kubectl get pods -n default

# 查看Pod日志
kubectl logs -f <pod-name> -n deep-research

# 查看Pod事件
kubectl describe pod <pod-name> -n deep-research

# 常见问题：
# - ImagePullBackOff: 镜像拉取失败，检查ACR集成
# - CrashLoopBackOff: 容器崩溃，检查日志和环境变量
# - Pending: 资源不足，检查节点资源
```

### 问题2：无法访问Perplexica
```bash
# 测试Perplexica连通性
kubectl run test-curl --rm -i --tty --image=curlimages/curl -n deep-research -- sh

# 在容器内执行
curl http://perplexica-service.default.svc.cluster.local/search -X POST \
  -H "Content-Type: application/json" \
  -d '{"query":"test"}'

# 检查DNS解析
nslookup perplexica-service.default.svc.cluster.local
```

### 问题3：Application Gateway不工作
```bash
# 查看Ingress状态
kubectl get ingress -n deep-research
kubectl describe ingress odr-ingress -n deep-research

# 查看Application Gateway后端健康状态
az network application-gateway show-backend-health \
  --name $APP_GATEWAY_NAME \
  --resource-group $RESOURCE_GROUP

# 查看AGIC日志
kubectl logs -f deployment/ingress-appgw-deployment -n kube-system
```

### 问题4：认证失败
```bash
# 验证JWT密钥一致性
kubectl get secret odr-secrets -n deep-research -o jsonpath='{.data.LANGGRAPH_AUTH_SECRET}' | base64 -d
echo $ODR_AUTH_SECRET

# 测试带Token的请求
curl -H "Authorization: Bearer $ODR_JWT_TOKEN" http://$ODR_PUBLIC_IP/ok
```

### 问题5：搜索超时
```bash
# 检查ODR日志
kubectl logs -f deployment/open-deep-research -n deep-research

# 调整超时配置
kubectl edit configmap open-deep-research-config -n deep-research
# 增加 SEARCH_REQUEST_DELAY 和减少 MAX_CONCURRENT_RESEARCH_UNITS
```

---

## 维护和监控

### 1. 日志聚合
```bash
# 使用Azure Monitor查看日志
az aks enable-addons \
  --resource-group $RESOURCE_GROUP \
  --name $AKS_CLUSTER_NAME \
  --addons monitoring

# 查询日志
az monitor log-analytics query \
  --workspace <workspace-id> \
  --analytics-query "ContainerLog | where ContainerName == 'open-deep-research' | limit 100"
```

### 2. 监控告警
```bash
# 创建CPU使用率告警
az monitor metrics alert create \
  --name "odr-high-cpu" \
  --resource-group $RESOURCE_GROUP \
  --scopes $(az aks show --resource-group $RESOURCE_GROUP --name $AKS_CLUSTER_NAME --query id -o tsv) \
  --condition "avg Percentage CPU > 80" \
  --window-size 5m \
  --evaluation-frequency 1m

# 创建内存使用率告警
az monitor metrics alert create \
  --name "odr-high-memory" \
  --resource-group $RESOURCE_GROUP \
  --scopes $(az aks show --resource-group $RESOURCE_GROUP --name $AKS_CLUSTER_NAME --query id -o tsv) \
  --condition "avg memoryWorkingSetBytes > 1.5GB" \
  --window-size 5m \
  --evaluation-frequency 1m
```

### 3. 自动扩展
```bash
# 启用集群自动扩展
az aks update \
  --resource-group $RESOURCE_GROUP \
  --name $AKS_CLUSTER_NAME \
  --enable-cluster-autoscaler \
  --min-count 2 \
  --max-count 5

# 配置HPA（Horizontal Pod Autoscaler）
cat <<EOF | kubectl apply -f -
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: odr-hpa
  namespace: deep-research
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: open-deep-research
  minReplicas: 1
  maxReplicas: 5
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
EOF
```

### 4. 备份和恢复
```bash
# 备份所有配置
kubectl get all,configmap,secret -n deep-research -o yaml > odr-backup.yaml
kubectl get all,configmap,secret -n default -o yaml > perplexica-backup.yaml

# 恢复配置
kubectl apply -f odr-backup.yaml
kubectl apply -f perplexica-backup.yaml
```

### 5. 版本升级
```bash
# 升级ODR镜像
kubectl set image deployment/open-deep-research \
  open-deep-research=langchain/open-deep-research:new-version \
  -n deep-research

# 滚动更新
kubectl rollout status deployment/open-deep-research -n deep-research

# 回滚
kubectl rollout undo deployment/open-deep-research -n deep-research
```

---

## 成本估算

### Azure资源月成本（美国东部）

| 资源 | 规格 | 月成本（USD） | 说明 |
|------|------|---------------|------|
| AKS管理费 | 免费 | $0 | Azure免费提供 |
| **虚拟机** | 1x Standard_B2s (2核4GB) | **~$31** | 可突发型，适合轻量负载 |
| Application Gateway | Standard_v2 (2 units) | ~$150 | 可选，或使用LoadBalancer |
| Public IP | Standard | ~$4 | 必需 |
| Azure Monitor | 基础监控 | ~$20 | 可选 |
| 出站流量 | ~50GB | ~$4 | 估算 |
| **总计（含App Gateway）** | | **~$209/月** | 企业推荐配置 |
| **总计（仅LoadBalancer）** | | **~$59/月** | 简化配置 |

### 成本优化方案对比

| 方案 | 节点类型 | 入口方式 | 月成本 | 适用场景 |
|------|----------|----------|--------|----------|
| **经济型** | 1x B2s | LoadBalancer | **$59** | 测试/开发环境 |
| **标准型** | 1x B2ms (2核8GB) | LoadBalancer | **$99** | 小规模生产 |
| **企业型** | 1x B2s | App Gateway + WAF | **$209** | 需要WAF防护 |
| **高可用型** | 2x B2s | App Gateway + WAF | **$240** | 高可用需求 |

### 优化建议

1. **选择合适的节点类型**：
   - B系列：成本低，适合大部分场景（推荐）
   - D系列：性能稳定，但成本高3-4倍
   
2. **使用Reserved Instances**：
   - 1年预留：节省~30%
   - 3年预留：节省~50%
   
3. **选择合适的入口方式**：
   - LoadBalancer：简单便宜（$4/月）
   - Application Gateway：功能丰富但贵（$150/月）
   
4. **优化出站流量**：
   - 使用Azure内部服务减少公网流量
   - 配置CDN缓存静态资源
   
5. **关闭开发环境**：
   - 非工作时间关闭dev环境
   - 使用Azure Automation自动开关机

### 💡 推荐配置

**对于大多数企业场景，我们推荐"经济型"方案：**
- 节点：1x Standard_B2s (2核4GB)
- 入口：LoadBalancer
- 月成本：~$59
- 优势：成本低、配置简单、满足基本需求

---

## 安全最佳实践

### 1. 网络安全
```bash
# 配置Network Policy
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: odr-network-policy
  namespace: deep-research
spec:
  podSelector:
    matchLabels:
      app: open-deep-research
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 8123
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: default
    ports:
    - protocol: TCP
      port: 80
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: TCP
      port: 53
EOF
```

### 2. 密钥管理（使用Azure Key Vault）
```bash
# 创建Key Vault
az keyvault create \
  --name "kv-odr-prod" \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# 存储密钥
az keyvault secret set \
  --vault-name "kv-odr-prod" \
  --name "OpenAIApiKey" \
  --value "$OPENAI_API_KEY"

# 配置AKS访问Key Vault
az aks enable-addons \
  --resource-group $RESOURCE_GROUP \
  --name $AKS_CLUSTER_NAME \
  --addons azure-keyvault-secrets-provider
```

### 3. RBAC配置
```bash
# 创建只读用户角色
cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: odr-viewer
  namespace: deep-research
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: odr-viewer-binding
  namespace: deep-research
subjects:
- kind: User
  name: "viewer@company.com"
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: odr-viewer
  apiGroup: rbac.authorization.k8s.io
EOF
```

---

## 附录

### A. 完整部署脚本
```bash
# 保存为 deploy_all.sh
#!/bin/bash
set -e

# 加载环境变量
source azure_env.sh
source odr_jwt_secret.txt

echo "🚀 开始部署ODR到Azure..."

# 1. 创建资源组和网络
echo "📦 创建资源组..."
az group create --name $RESOURCE_GROUP --location $LOCATION

echo "🌐 创建虚拟网络..."
az network vnet create --resource-group $RESOURCE_GROUP --name $VNET_NAME --address-prefixes 10.0.0.0/16 --subnet-name aks-subnet --subnet-prefix 10.0.1.0/24
az network vnet subnet create --resource-group $RESOURCE_GROUP --vnet-name $VNET_NAME --name appgw-subnet --address-prefix 10.0.2.0/24

# 2. 创建AKS
echo "☸️  创建AKS集群..."
az aks create --resource-group $RESOURCE_GROUP --name $AKS_CLUSTER_NAME --location $LOCATION --node-count 1 --node-vm-size Standard_B2s --vnet-subnet-id $(az network vnet subnet show --resource-group $RESOURCE_GROUP --vnet-name $VNET_NAME --name aks-subnet --query id -o tsv) --network-plugin azure --enable-managed-identity --enable-addons monitoring --generate-ssh-keys
az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_CLUSTER_NAME --overwrite-existing

# 3. 部署Perplexica（使用优化镜像）
echo "🔍 部署Perplexica..."
kubectl create secret generic perplexica-secrets --from-literal=OPENAI_API_KEY="$OPENAI_API_KEY" --from-literal=ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" -n default --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f perplexica-configmap.yaml
kubectl apply -f perplexica-deployment.yaml
kubectl wait --for=condition=ready pod -l app=perplexica -n default --timeout=300s
echo "💡 使用镜像: shankswhite/perplexica:tavily-v1.1"

# 4. 部署ODR（使用优化镜像）
echo "📚 部署ODR..."
kubectl create namespace deep-research --dry-run=client -o yaml | kubectl apply -f -
kubectl create secret generic odr-secrets --from-literal=OPENAI_API_KEY="$OPENAI_API_KEY" --from-literal=ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" --from-literal=LANGSMITH_API_KEY="" --from-literal=LANGGRAPH_AUTH_SECRET="$ODR_AUTH_SECRET" -n deep-research --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f odr-configmap.yaml
kubectl apply -f odr-deployment.yaml
kubectl wait --for=condition=ready pod -l app=open-deep-research -n deep-research --timeout=300s
echo "💡 使用镜像: shankswhite/open-deep-research:v1.10-rate-limit"

# 5. 配置Application Gateway
echo "🌐 配置Application Gateway..."
az network public-ip create --resource-group $RESOURCE_GROUP --name pip-appgw-odr --allocation-method Static --sku Standard
az network application-gateway create --name $APP_GATEWAY_NAME --resource-group $RESOURCE_GROUP --location $LOCATION --sku Standard_v2 --public-ip-address pip-appgw-odr --vnet-name $VNET_NAME --subnet appgw-subnet --capacity 2
az aks enable-addons --resource-group $RESOURCE_GROUP --name $AKS_CLUSTER_NAME --addons ingress-appgw --appgw-id $(az network application-gateway show --resource-group $RESOURCE_GROUP --name $APP_GATEWAY_NAME --query id -o tsv)
kubectl apply -f odr-ingress.yaml

# 6. 获取访问信息
export ODR_PUBLIC_IP=$(az network public-ip show --resource-group $RESOURCE_GROUP --name pip-appgw-odr --query ipAddress -o tsv)
export ODR_JWT_TOKEN=$(python3 generate_jwt_token.py "$ODR_AUTH_SECRET")

echo ""
echo "✅ 部署完成！"
echo "======================================================================"
echo "🌐 ODR访问地址: http://$ODR_PUBLIC_IP"
echo "🔑 JWT Token: $ODR_JWT_TOKEN"
echo "======================================================================"
echo ""
echo "测试命令:"
echo "curl -H \"Authorization: Bearer $ODR_JWT_TOKEN\" http://$ODR_PUBLIC_IP/ok"
echo ""
```

### B. 快速清理脚本
```bash
# 保存为 cleanup_all.sh
#!/bin/bash
set -e

source azure_env.sh

echo "🗑️  开始清理Azure资源..."

# 删除整个资源组（包含所有资源）
az group delete --name $RESOURCE_GROUP --yes --no-wait

echo "✅ 清理命令已提交（后台执行）"
echo "📝 可以通过以下命令检查删除进度:"
echo "az group show --name $RESOURCE_GROUP"
```

---

## 总结

本文档提供了将ODR + Perplexica从个人Cloudflare环境迁移到Azure企业环境的完整步骤。

**关键要点**：
1. ✅ 使用Azure Application Gateway替代Cloudflare Tunnel
2. ✅ 配置企业级安全（Network Policy, RBAC, Key Vault）
3. ✅ 实施监控和告警
4. ✅ 配置自动扩展和高可用性
5. ✅ 优化成本

**下一步**：
- 配置自定义域名和SSL证书
- 集成Azure AD进行企业认证
- 设置CI/CD管道自动部署
- 配置灾难恢复方案

**支持**：
如有问题，请参考故障排查章节或联系Azure支持。

---

**文档版本**：1.0  
**最后更新**：2024-11-24  
**作者**：AI Assistant

