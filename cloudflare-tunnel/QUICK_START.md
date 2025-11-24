# ⚡ Cloudflare Tunnel 快速开始

3 步完成公网访问配置！

---

## 步骤 1: 获取 Tunnel Token（5 分钟）

1. 访问 https://one.dash.cloudflare.com/
2. 登录/注册 Cloudflare 账号
3. 点击左侧 **Zero Trust** → **Access** → **Tunnels**
4. 点击 **Create a tunnel** → **Cloudflared**
5. 命名: `odr-tunnel`
6. **复制 Token**（看起来像 `eyJhIjoiNzk4O...`）
7. 先别关闭页面！

---

## 步骤 2: 部署到 AKS（2 分钟）

```bash
# 进入目录
cd /Users/zhaoxiaofeng/SynologyDrive/Drive/Projects/DeepResearch/cloudflare-tunnel

# 给脚本执行权限
chmod +x deploy.sh

# 部署（替换为你的 Token）
./deploy.sh "eyJhIjoiNzk4O..."
```

看到 `✅ Cloudflared 部署完成!` 就成功了！

---

## 步骤 3: 配置域名路由（3 分钟）

返回 Cloudflare 控制台（刚才没关的页面）：

1. 找到 **Public Hostname** 标签
2. 点击 **Add a public hostname**
3. 填写:
   ```
   Subdomain: odr-api
   Domain: (选择你的域名，或使用 trycloudflare.com)
   Path: (留空)
   
   Service Type: HTTP
   URL: http://open-deep-research-service.deep-research.svc.cluster.local:8123
   ```
4. 点击 **Save**

---

## 🎉 完成！立即测试

浏览器访问:
```
https://odr-api.yourdomain.com/
```

或者 curl 测试:
```bash
curl https://odr-api.yourdomain.com/
```

看到任何响应（即使是 403）都说明连接成功！

---

## 🔐 添加安全保护（可选但推荐，5 分钟）

在 Cloudflare 控制台:
1. **Access** → **Applications** → **Add an application**
2. 选择 **Self-hosted**
3. Application domain: `odr-api.yourdomain.com`
4. 添加策略:
   - Email 允许列表: `your-email@example.com`
   - 或创建 **Service Token** 用于 API 调用

---

## 📝 快速命令参考

```bash
# 查看 cloudflared 状态
kubectl get pods -n cloudflare-tunnel

# 查看连接日志
kubectl logs -n cloudflare-tunnel -l app=cloudflared -f

# 重启 cloudflared
kubectl rollout restart deployment/cloudflared -n cloudflare-tunnel

# 删除部署
kubectl delete namespace cloudflare-tunnel
```

---

## ❓ 常见问题

**Q: Token 在哪里找？**
A: Cloudflare 控制台 → Zero Trust → Access → Tunnels → 你的 Tunnel → Configure

**Q: 域名怎么设置？**
A: 如果没有自己的域名，选择 "trycloudflare.com" 会自动生成免费域名

**Q: 如何确认部署成功？**
A: 运行 `kubectl logs -n cloudflare-tunnel -l app=cloudflared`，看到 `Registered tunnel connection` 就成功了

**Q: API 如何调用？**
A: 查看完整 README.md 中的 Python 示例

---

## 📚 更多信息

- 完整指南: `README.md`
- 故障排查: `README.md` 中的故障排查章节
- Cloudflare 文档: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/

---

**有问题？** 查看日志:
```bash
kubectl logs -n cloudflare-tunnel -l app=cloudflared --tail=50
```


