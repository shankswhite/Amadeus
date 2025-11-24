# 🌐 Cloudflare Tunnel 部署指南

让 Open Deep Research 可以通过公网安全访问。

## 📋 部署流程概览

```
第一步: Cloudflare 控制台配置 (10 分钟)
第二步: 部署 cloudflared 到 AKS (5 分钟)
第三步: 配置路由和域名 (5 分钟)
第四步: 配置访问策略 (可选, 5 分钟)
第五步: 测试验证 (5 分钟)
```

---

## 第一步: Cloudflare 控制台配置

### 1.1 注册/登录 Cloudflare

访问: https://dash.cloudflare.com/

### 1.2 进入 Zero Trust 控制台

1. 登录后，点击左侧菜单的 **Zero Trust**
2. 如果是第一次使用，需要设置团队名称（任意名称即可）

### 1.3 创建 Tunnel

1. 导航到 **Access** → **Tunnels**
2. 点击 **Create a tunnel**
3. 选择 **Cloudflared**
4. 给 Tunnel 命名，例如: `odr-research-tunnel`
5. 点击 **Save tunnel**
6. **重要**: 复制显示的 **Tunnel Token**，格式类似:
   ```
   eyJhIjoiNzk4OGYxZjA3YTk1NGJiNGI3NzIyYjZhN2U1NTQwMjAiLCJ0IjoiNWY3...
   ```
7. 保存此 Token，稍后需要使用

---

## 第二步: 部署 cloudflared 到 AKS

### 2.1 进入部署目录

```bash
cd /Users/zhaoxiaofeng/SynologyDrive/Drive/Projects/DeepResearch/cloudflare-tunnel
```

### 2.2 运行部署脚本

```bash
# 给脚本添加执行权限
chmod +x deploy.sh

# 运行部署（替换为你的 Tunnel Token）
./deploy.sh "YOUR_TUNNEL_TOKEN_HERE"
```

### 2.3 验证部署

脚本会自动:
- ✅ 创建 `cloudflare-tunnel` namespace
- ✅ 创建包含 Token 的 Secret
- ✅ 部署 2 个 cloudflared Pod（高可用）
- ✅ 等待 Pods 启动完成
- ✅ 显示连接状态

查看日志确认连接成功:
```bash
kubectl logs -n cloudflare-tunnel -l app=cloudflared -f
```

期望看到类似输出:
```
INF Connection registered connIndex=0 ...
INF Registered tunnel connection ...
```

---

## 第三步: 配置路由和域名

返回 Cloudflare Zero Trust 控制台:

### 3.1 配置 Public Hostname

1. 在 Tunnel 详情页面，找到 **Public Hostname** 标签
2. 点击 **Add a public hostname**
3. 填写配置:
   
   **如果你有自己的域名** (推荐):
   ```
   Subdomain: odr-api  (或任意你喜欢的)
   Domain: yourdomain.com  (你的域名)
   Path: (留空，匹配所有路径)
   
   Service Type: HTTP
   URL: http://open-deep-research-service.deep-research.svc.cluster.local:8123
   ```
   
   **如果使用 Cloudflare 免费域名**:
   ```
   选择 "Use a Cloudflare domain"
   会自动生成类似 https://your-tunnel.trycloudflare.com
   
   Service Type: HTTP
   URL: http://open-deep-research-service.deep-research.svc.cluster.local:8123
   ```

4. 点击 **Save hostname**

### 3.2 测试访问

配置保存后，立即生效！测试访问:

```bash
# 替换为你的实际 URL
curl https://odr-api.yourdomain.com/

# 或者在浏览器中打开
open https://odr-api.yourdomain.com/
```

期望返回 API 响应（可能是 403，这是正常的，因为需要认证）

---

## 第四步: 配置访问策略（推荐）

为了安全，建议配置访问策略限制谁可以访问。

### 4.1 创建 Access Application

1. 在 Cloudflare Zero Trust 控制台
2. 导航到 **Access** → **Applications**
3. 点击 **Add an application**
4. 选择 **Self-hosted**
5. 填写配置:
   ```
   Application name: Open Deep Research API
   Session Duration: 24 hours
   Application domain: odr-api.yourdomain.com
   ```
6. 点击 **Next**

### 4.2 配置访问策略

**选项 A: Email 认证** (简单，适合个人/小团队)
```
Policy name: Email Access
Action: Allow
Include: 
  - Emails: your-email@example.com, team@example.com
```

**选项 B: Service Token** (适合 API 调用)
```
1. 创建 Service Token:
   Access → Service Auth → Service Tokens → Create Service Token
   
2. 保存生成的:
   - Client ID: CF-Access-Client-Id
   - Client Secret: CF-Access-Client-Secret
   
3. 在策略中选择:
   Include: Service Auth → 选择刚创建的 Token
```

**选项 C: 任何人可访问** (不推荐，仅测试用)
```
Include: Everyone
```

7. 点击 **Next** → **Add application**

### 4.3 使用 Service Token 调用 API

如果配置了 Service Token:

```bash
curl -X POST https://odr-api.yourdomain.com/threads \
  -H "CF-Access-Client-Id: YOUR_CLIENT_ID" \
  -H "CF-Access-Client-Secret: YOUR_CLIENT_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "分析 Call of Duty Black Ops 7 的玩家评价"
      }
    ]
  }'
```

---

## 第五步: 测试验证

### 5.1 完整 API 调用测试

**使用 Email 认证**:
```bash
# 1. 在浏览器中访问 API URL
open https://odr-api.yourdomain.com/

# 2. 完成 Email 认证
# 3. 认证成功后，浏览器会保存 Cookie
# 4. 之后的 API 调用会自动携带认证信息
```

**使用 Service Token**:
```bash
# 创建测试脚本
cat > test-odr-api.sh << 'EOF'
#!/bin/bash

CLIENT_ID="your-client-id-here"
CLIENT_SECRET="your-client-secret-here"
API_URL="https://odr-api.yourdomain.com"

curl -X POST "$API_URL/threads" \
  -H "CF-Access-Client-Id: $CLIENT_ID" \
  -H "CF-Access-Client-Secret: $CLIENT_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "agent",
    "metadata": {}
  }'
EOF

chmod +x test-odr-api.sh
./test-odr-api.sh
```

### 5.2 监控和日志

查看 cloudflared 日志:
```bash
# 实时日志
kubectl logs -n cloudflare-tunnel -l app=cloudflared -f

# 最近 100 行
kubectl logs -n cloudflare-tunnel -l app=cloudflared --tail=100
```

查看 ODR 服务日志:
```bash
kubectl logs -n deep-research -l app=open-deep-research -f
```

---

## 🎯 完整的使用示例

### Python 客户端示例

```python
import httpx
import json

# 配置
API_URL = "https://odr-api.yourdomain.com"
CLIENT_ID = "your-client-id"
CLIENT_SECRET = "your-client-secret"

# 创建 HTTP 客户端
client = httpx.Client(
    headers={
        "CF-Access-Client-Id": CLIENT_ID,
        "CF-Access-Client-Secret": CLIENT_SECRET,
        "Content-Type": "application/json"
    },
    timeout=300.0  # 5 分钟超时
)

# 创建研究任务
def create_research(query):
    """创建深度研究任务"""
    response = client.post(
        f"{API_URL}/threads",
        json={
            "assistant_id": "agent",
            "metadata": {}
        }
    )
    thread = response.json()
    thread_id = thread["thread_id"]
    
    # 提交研究问题
    response = client.post(
        f"{API_URL}/threads/{thread_id}/runs/stream",
        json={
            "assistant_id": "agent",
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": query
                    }
                ]
            }
        }
    )
    
    # 流式读取结果
    for line in response.iter_lines():
        if line:
            print(line)
    
    return thread_id

# 示例：创建 COD BO7 舆情分析
query = """
分析 Call of Duty Black Ops 7 在 2024年11月1-15日的玩家舆情:
1. 整体情绪分析
2. 主要抱怨点
3. 受好评特性
4. 改进建议
"""

thread_id = create_research(query)
print(f"研究任务已创建: {thread_id}")
```

---

## 🔧 故障排查

### 问题 1: cloudflared Pods 无法启动

**检查**:
```bash
kubectl get pods -n cloudflare-tunnel
kubectl describe pod -n cloudflare-tunnel -l app=cloudflared
kubectl logs -n cloudflare-tunnel -l app=cloudflared
```

**常见原因**:
- Token 错误或过期
- 网络连接问题
- 资源不足

**解决**:
```bash
# 重新创建 Secret（使用新的 Token）
kubectl delete secret cloudflared-token -n cloudflare-tunnel
kubectl create secret generic cloudflared-token \
  --from-literal=token="NEW_TOKEN" \
  --namespace=cloudflare-tunnel

# 重启 Pods
kubectl rollout restart deployment/cloudflared -n cloudflare-tunnel
```

### 问题 2: 无法访问 ODR 服务

**检查连接**:
```bash
# 1. 验证 cloudflared 是否连接成功
kubectl logs -n cloudflare-tunnel -l app=cloudflared | grep "registered"

# 2. 验证 ODR 服务是否运行
kubectl get pods -n deep-research
kubectl get svc -n deep-research

# 3. 测试内部连通性
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://open-deep-research-service.deep-research.svc.cluster.local:8123/
```

### 问题 3: 403 Forbidden

**原因**: 访问策略配置问题

**解决**:
1. 检查 Cloudflare Access 策略配置
2. 确认 Service Token 正确传递
3. 检查 Email 是否已认证

---

## 📊 成本分析

### Cloudflare 成本

- **Tunnel**: 完全免费 ✅
- **Zero Trust Free Plan**: 
  - 最多 50 个用户
  - 无限 Tunnels
  - 基础访问策略
- **Zero Trust Team Plan** ($7/用户/月):
  - 高级访问策略
  - 更多日志保留
  - 更好的监控

### AKS 成本增加

- cloudflared Pods: ~$5-10/月
- 网络流量: ~$5-20/月（取决于使用量）

**总计**: ~$10-30/月（使用免费 Cloudflare 计划）

---

## 🔐 安全最佳实践

1. ✅ **始终使用 Service Token** 进行 API 调用
2. ✅ **启用 Email 认证** 用于 Web UI 访问
3. ✅ **定期轮换 Service Token**（建议每 90 天）
4. ✅ **监控访问日志**（在 Cloudflare 控制台）
5. ✅ **配置速率限制**（在 Cloudflare 控制台）
6. ✅ **使用 IP 白名单**（如果 IP 固定）

---

## 📝 维护和管理

### 更新 cloudflared

```bash
# 拉取最新镜像并重启
kubectl rollout restart deployment/cloudflared -n cloudflare-tunnel
```

### 查看连接状态

```bash
# 查看 Tunnel 状态
kubectl get pods -n cloudflare-tunnel

# 查看实时日志
kubectl logs -n cloudflare-tunnel -l app=cloudflared -f
```

### 卸载

```bash
# 删除 cloudflared 部署
kubectl delete namespace cloudflare-tunnel

# 在 Cloudflare 控制台删除 Tunnel
```

---

## 🎉 恭喜！

你现在已经成功将 Open Deep Research 通过 Cloudflare Tunnel 暴露到公网，并具备:

- ✅ 自动 HTTPS 加密
- ✅ Zero Trust 访问控制
- ✅ 无需公网 IP 或 LoadBalancer
- ✅ DDoS 防护
- ✅ 全球 CDN 加速
- ✅ 完全免费或低成本

有任何问题，随时查看日志或联系我！😊


