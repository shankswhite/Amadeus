# 🚀 AKS 集群间迁移指南

## 你的问题

> "如果我后期部署了全套服务（包括前端），想从当前环境迁移到另一个 Azure AKS 容器内，是不是直接打包迁移部署然后就直接能用了？还是说还要手动处理什么？"

---

## 💡 简短回答

**基本可以直接迁移，但有几个地方需要注意处理。**

### ✅ 可以直接迁移的部分（80%）

- Deployment 配置
- Service 配置（ClusterIP）
- ConfigMap
- 应用代码和逻辑
- 服务间调用关系

### ⚠️ 需要手动处理的部分（20%）

- 数据（PVC/数据库）
- 密钥（Secrets）
- 域名/DNS（如果有）
- 外部依赖配置
- Docker 镜像访问权限

---

## 📋 完整迁移流程

### 方案 A: 导出-导入方式（推荐简单场景）

#### 步骤 1: 导出当前配置

```bash
# 连接到源 AKS 集群
az aks get-credentials --resource-group <源资源组> --name <源集群名>

# 导出所有配置到文件
kubectl get deployment perplexica -o yaml > perplexica-deployment.yaml
kubectl get service perplexica-service -o yaml > perplexica-service.yaml
kubectl get service searxng-service -o yaml > searxng-service.yaml
kubectl get deployment searxng -o yaml > searxng-deployment.yaml
kubectl get configmap -o yaml > configmaps.yaml
kubectl get pvc -o yaml > pvcs.yaml

# 如果有 Secrets（需要特别小心）
kubectl get secrets -o yaml > secrets.yaml
```

#### 步骤 2: 清理配置文件

自动生成的配置包含一些不需要的字段：

```bash
# 需要删除的字段（每个 YAML 文件）:
# - metadata.uid
# - metadata.resourceVersion
# - metadata.creationTimestamp
# - metadata.selfLink
# - status (整个 section)
```

或者使用脚本自动清理：

```bash
# clean-yaml.sh
#!/bin/bash
for file in *.yaml; do
    yq eval 'del(.metadata.uid, .metadata.resourceVersion, .metadata.creationTimestamp, .metadata.selfLink, .status)' $file -i
done
```

#### 步骤 3: 迁移数据（如果有）

```bash
# 导出 PVC 数据
kubectl exec -it <pod-name> -- tar czf /tmp/backup.tar.gz /data
kubectl cp <pod-name>:/tmp/backup.tar.gz ./backup.tar.gz
```

#### 步骤 4: 连接到目标集群

```bash
# 切换到目标 AKS 集群
az aks get-credentials --resource-group <目标资源组> --name <目标集群名>

# 验证连接
kubectl get nodes
```

#### 步骤 5: 应用配置

```bash
# 按顺序部署
kubectl apply -f configmaps.yaml
kubectl apply -f secrets.yaml
kubectl apply -f pvcs.yaml
kubectl apply -f searxng-deployment.yaml
kubectl apply -f searxng-service.yaml
kubectl apply -f perplexica-deployment.yaml
kubectl apply -f perplexica-service.yaml

# 验证部署
kubectl get pods
kubectl get svc
```

#### 步骤 6: 恢复数据（如果有）

```bash
# 上传备份
kubectl cp ./backup.tar.gz <new-pod-name>:/tmp/backup.tar.gz

# 恢复数据
kubectl exec -it <new-pod-name> -- tar xzf /tmp/backup.tar.gz -C /
```

---

### 方案 B: GitOps 方式（推荐生产环境）

#### 架构

```
Git Repository
    ↓
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── configmap.yaml
│   └── pvc.yaml
└── README.md

两个 AKS 集群都从同一个 Git 仓库部署
```

#### 优势

```
✅ 配置版本控制
✅ 可重复部署
✅ 审计跟踪
✅ 回滚容易
✅ 多环境管理
```

#### 实现步骤

**1. 将配置提交到 Git**

```bash
# 在你的项目中
cd Perplexica-master
git add k8s/
git commit -m "Add Kubernetes configurations"
git push
```

**2. 在新集群中部署**

```bash
# 连接到新集群
az aks get-credentials --resource-group <新资源组> --name <新集群名>

# 克隆仓库
git clone <your-repo>
cd Perplexica-master

# 部署
kubectl apply -f k8s/
```

---

### 方案 C: Helm Chart（推荐复杂应用）

#### 创建 Helm Chart

```bash
# 创建 Chart
helm create perplexica-stack

# 目录结构
perplexica-stack/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    └── configmap.yaml
```

#### 使用 Helm 部署

```bash
# 源集群导出
helm package perplexica-stack

# 目标集群部署
helm install perplexica ./perplexica-stack-0.1.0.tgz
```

---

## ⚠️ 需要特别处理的部分

### 1. 数据迁移（PVC）

#### 问题

```
PVC 是绑定到特定 AZ (可用区) 的存储
不能直接在集群间迁移
```

#### 解决方案

**方案 A: 备份-恢复**

```bash
# 源集群
kubectl exec -it perplexica-xxx -- tar czf /tmp/data-backup.tar.gz /home/perplexica/data
kubectl cp perplexica-xxx:/tmp/data-backup.tar.gz ./data-backup.tar.gz

kubectl exec -it perplexica-xxx -- tar czf /tmp/uploads-backup.tar.gz /home/perplexica/uploads
kubectl cp perplexica-xxx:/tmp/uploads-backup.tar.gz ./uploads-backup.tar.gz

# 目标集群
kubectl cp ./data-backup.tar.gz perplexica-yyy:/tmp/
kubectl exec -it perplexica-yyy -- tar xzf /tmp/data-backup.tar.gz -C /

kubectl cp ./uploads-backup.tar.gz perplexica-yyy:/tmp/
kubectl exec -it perplexica-yyy -- tar xzf /tmp/uploads-backup.tar.gz -C /
```

**方案 B: Azure Files/Blob（推荐）**

如果数据量大，使用 Azure 存储：

```yaml
# 使用 Azure Files 作为持久存储
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: perplexica-data-pvc
spec:
  accessModes:
    - ReadWriteMany  # 可以在集群间共享
  storageClassName: azurefile
  resources:
    requests:
      storage: 5Gi
```

**方案 C: 初始数据为空**

如果数据不重要（如缓存），可以不迁移：

```yaml
# PVC 会在新集群中自动创建新的空卷
# 应用会重新生成数据
```

---

### 2. Secrets（密钥）

#### 问题

```
Secrets 包含敏感信息（API keys, 密码等）
不应该直接提交到 Git
```

#### 解决方案

**方案 A: 手动重建**

```bash
# 导出（查看内容）
kubectl get secret <secret-name> -o yaml

# 在新集群中创建
kubectl create secret generic <secret-name> \
  --from-literal=key1=value1 \
  --from-literal=key2=value2
```

**方案 B: Azure Key Vault（推荐生产）**

```yaml
# 使用 Azure Key Vault CSI Driver
apiVersion: v1
kind: Secret
metadata:
  name: perplexica-secrets
type: Opaque
data:
  # 从 Key Vault 自动同步
```

**方案 C: Sealed Secrets**

加密后可以安全存储在 Git：

```bash
# 加密 Secret
kubeseal --format yaml < secret.yaml > sealed-secret.yaml

# 提交到 Git
git add sealed-secret.yaml
```

---

### 3. 镜像访问

#### 当前情况

你使用的是 Docker Hub 公开镜像：

```yaml
image: shankswhite/perplexica:tavily-v1.1
image: searxng/searxng:latest
```

#### 迁移处理

**公开镜像**：
```
✅ 无需处理
新集群可以直接拉取
```

**私有镜像**（如果将来使用）：

```bash
# 需要在新集群中配置访问权限
kubectl create secret docker-registry regcred \
  --docker-server=<registry-url> \
  --docker-username=<username> \
  --docker-password=<password>

# 在 Deployment 中引用
spec:
  template:
    spec:
      imagePullSecrets:
      - name: regcred
```

---

### 4. 域名和 DNS

#### 如果使用 LoadBalancer

```bash
# 源集群 IP
kubectl get svc perplexica-service
EXTERNAL-IP: 20.123.45.67

# 新集群会获得不同的 IP
EXTERNAL-IP: 40.234.56.78  # 新 IP

# 需要更新 DNS 记录
api.yourdomain.com → 40.234.56.78
```

#### 如果使用 Ingress

```yaml
# Ingress 配置可以直接迁移
# 但需要更新域名的 A 记录指向新集群的 LoadBalancer IP
```

---

### 5. 环境变量和配置

#### 当前配置

```yaml
env:
  - name: TAVILY_TIMEOUT
    value: "300"
  - name: TAVILY_MAX_RESULTS
    value: "50"
  - name: TAVILY_DEFAULT_LANGUAGE
    value: "en"
```

#### 迁移处理

```
✅ 直接迁移（在 YAML 中）
如果需要不同环境使用不同配置：
  → 使用 ConfigMap
  → 或使用 Helm values
```

---

## 🎯 实际迁移示例

### 场景：你的完整应用栈

假设你的应用包括：

```
┌─────────────────────────────────────────┐
│  前端 (Frontend)                         │
│  - Next.js / React                       │
│  - Deployment + Service (ClusterIP)     │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  后端 API (Backend)                      │
│  - Python / Node.js                      │
│  - Deployment + Service (ClusterIP)     │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  搜索服务 (Perplexica)                    │
│  - Deployment + Service (ClusterIP)     │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  搜索引擎 (SearXNG)                       │
│  - Deployment + Service (ClusterIP)     │
└─────────────────────────────────────────┘
```

### 完整迁移脚本

```bash
#!/bin/bash
# migrate-to-new-cluster.sh

set -e

echo "🚀 开始迁移到新 AKS 集群"

# ===== 步骤 1: 导出源集群配置 =====
echo "📤 导出源集群配置..."
az aks get-credentials --resource-group source-rg --name source-aks

mkdir -p migration-backup
cd migration-backup

# 导出所有配置
kubectl get deployment -o yaml > deployments.yaml
kubectl get service -o yaml > services.yaml
kubectl get configmap -o yaml > configmaps.yaml
kubectl get pvc -o yaml > pvcs.yaml

# 导出镜像列表（用于预拉取）
kubectl get pods -o jsonpath="{.items[*].spec.containers[*].image}" | tr -s '[[:space:]]' '\n' > images.txt

echo "✅ 配置已导出到 migration-backup/"

# ===== 步骤 2: 备份数据 =====
echo "💾 备份持久化数据..."

# 假设你有这些 Pod
PODS=$(kubectl get pods -o name | grep -E "frontend|backend|perplexica")

for pod in $PODS; do
    pod_name=$(echo $pod | cut -d'/' -f2)
    echo "  备份 $pod_name..."
    
    # 检查是否有需要备份的数据
    if kubectl exec $pod -- test -d /data 2>/dev/null; then
        kubectl exec $pod -- tar czf /tmp/${pod_name}-backup.tar.gz /data || true
        kubectl cp $pod:/tmp/${pod_name}-backup.tar.gz ./${pod_name}-backup.tar.gz || true
    fi
done

echo "✅ 数据备份完成"

# ===== 步骤 3: 清理配置文件 =====
echo "🧹 清理配置文件..."

# 删除不需要的字段
for file in *.yaml; do
    # 使用 yq 或 sed 清理
    sed -i.bak '/uid:/d' $file
    sed -i.bak '/resourceVersion:/d' $file
    sed -i.bak '/creationTimestamp:/d' $file
    sed -i.bak '/selfLink:/d' $file
    rm -f ${file}.bak
done

echo "✅ 配置文件已清理"

# ===== 步骤 4: 连接到目标集群 =====
echo "🎯 连接到目标集群..."
az aks get-credentials --resource-group target-rg --name target-aks

# 验证连接
kubectl get nodes
echo "✅ 已连接到目标集群"

# ===== 步骤 5: 预拉取镜像（可选，加速部署）=====
echo "📥 预拉取镜像..."

# 在每个节点上预拉取
while read image; do
    echo "  拉取 $image"
    # 通过 DaemonSet 预拉取
done < images.txt

echo "✅ 镜像预拉取完成"

# ===== 步骤 6: 部署到新集群 =====
echo "🚢 部署到新集群..."

# 按依赖顺序部署
kubectl apply -f configmaps.yaml
kubectl apply -f pvcs.yaml

# 等待 PVC 创建完成
kubectl wait --for=condition=Bound pvc --all --timeout=300s

kubectl apply -f services.yaml
kubectl apply -f deployments.yaml

# 等待所有 Pod 就绪
kubectl wait --for=condition=Ready pods --all --timeout=600s

echo "✅ 部署完成"

# ===== 步骤 7: 恢复数据 =====
echo "📥 恢复数据..."

# 获取新的 Pod 名称
NEW_PODS=$(kubectl get pods -o name | grep -E "frontend|backend|perplexica")

for backup_file in *-backup.tar.gz; do
    if [ -f "$backup_file" ]; then
        pod_prefix=$(echo $backup_file | sed 's/-backup.tar.gz//')
        
        # 找到对应的新 Pod
        new_pod=$(echo "$NEW_PODS" | grep $pod_prefix | head -1 | cut -d'/' -f2)
        
        if [ -n "$new_pod" ]; then
            echo "  恢复 $backup_file 到 $new_pod..."
            kubectl cp $backup_file $new_pod:/tmp/
            kubectl exec $new_pod -- tar xzf /tmp/$(basename $backup_file) -C / || true
        fi
    fi
done

echo "✅ 数据恢复完成"

# ===== 步骤 8: 验证 =====
echo "🔍 验证部署..."

echo "Pod 状态:"
kubectl get pods

echo ""
echo "Service 状态:"
kubectl get svc

echo ""
echo "PVC 状态:"
kubectl get pvc

# ===== 步骤 9: 测试服务 =====
echo "🧪 测试服务..."

# 测试 Perplexica API
kubectl port-forward svc/perplexica-service 8080:80 &
PF_PID=$!
sleep 3

curl -X POST http://localhost:8080/api/tavily \
  -H "Content-Type: application/json" \
  -d '{"query": "test migration"}' \
  && echo "✅ API 测试成功" \
  || echo "❌ API 测试失败"

kill $PF_PID

echo ""
echo "🎉 迁移完成！"
echo ""
echo "📋 后续步骤:"
echo "  1. 验证所有服务功能"
echo "  2. 更新 DNS 记录（如果有）"
echo "  3. 更新监控和日志配置"
echo "  4. 确认后关闭源集群"
```

### 使用方式

```bash
# 1. 赋予执行权限
chmod +x migrate-to-new-cluster.sh

# 2. 运行迁移
./migrate-to-new-cluster.sh

# 3. 根据输出检查结果
```

---

## 📊 迁移检查清单

### 迁移前

```
✅ 导出所有配置文件
✅ 备份持久化数据
✅ 记录当前配置（环境变量、资源限制等）
✅ 确认镜像访问权限
✅ 准备目标集群
✅ 确认资源配额足够
```

### 迁移中

```
✅ 清理配置文件中的集群特定字段
✅ 创建必要的 Secrets
✅ 按正确顺序部署资源
✅ 等待 PVC 绑定完成
✅ 验证 Pod 启动成功
✅ 恢复数据
```

### 迁移后

```
✅ 测试所有服务端点
✅ 验证服务间通信
✅ 检查日志无错误
✅ 验证数据完整性
✅ 更新 DNS/域名（如果有）
✅ 更新监控配置
✅ 更新备份计划
✅ 文档更新
```

---

## ⚡ 快速迁移（最简单方式）

如果你的应用：
- ✅ 使用 Git 管理配置
- ✅ 使用公开镜像
- ✅ 没有重要的持久化数据
- ✅ 所有配置在 YAML 文件中

### 5 步迁移

```bash
# 1. 连接到新集群
az aks get-credentials --resource-group <新RG> --name <新集群>

# 2. 从 Git 克隆
git clone <your-repo>
cd Perplexica-master

# 3. 部署
kubectl apply -f k8s/

# 4. 等待
kubectl wait --for=condition=Ready pods --all

# 5. 验证
kubectl get all
```

**就这么简单！** ✅

---

## 🎯 针对你的场景

### 假设：完整应用栈（前端 + 后端 + Perplexica）

#### 项目结构

```
your-app/
├── frontend/
│   ├── Dockerfile
│   └── k8s/
│       ├── deployment.yaml
│       └── service.yaml
├── backend/
│   ├── Dockerfile
│   └── k8s/
│       ├── deployment.yaml
│       └── service.yaml
└── search-service/  (Perplexica)
    └── k8s/
        ├── deployment.yaml
        └── service.yaml
```

#### 迁移步骤

**源集群** (current-aks):
```bash
# 1. 确保所有配置在 Git 中
git add .
git commit -m "Prepare for migration"
git push
```

**目标集群** (new-aks):
```bash
# 2. 连接到新集群
az aks get-credentials --resource-group new-rg --name new-aks

# 3. 克隆并部署
git clone <your-repo>
cd your-app

# 4. 依次部署（注意顺序）
kubectl apply -f search-service/k8s/  # 先部署底层依赖
kubectl apply -f backend/k8s/          # 然后部署后端
kubectl apply -f frontend/k8s/         # 最后部署前端

# 5. 验证
kubectl get pods --watch
```

### 服务发现（ClusterIP 的优势）

因为你使用 ClusterIP，服务名称在两个集群中完全一样：

```
源集群:
  frontend → http://backend-service
  backend → http://perplexica-service

目标集群:
  frontend → http://backend-service  ✅ 无需修改
  backend → http://perplexica-service  ✅ 无需修改
```

**关键优势**: 使用服务名称（而不是 IP），迁移后自动工作！

---

## 💡 最佳实践建议

### 1. 使用 Git 管理配置

```bash
# 所有 K8s 配置都提交到 Git
your-app/
├── k8s/
│   ├── base/           # 共同配置
│   ├── dev/            # 开发环境
│   └── prod/           # 生产环境
└── README.md
```

### 2. 使用环境变量区分环境

```yaml
env:
  - name: ENVIRONMENT
    value: "production"  # 或 "development"
  - name: API_ENDPOINT
    value: "http://perplexica-service"  # 内部服务名，无需改
```

### 3. 自动化部署

```bash
# 使用 CI/CD
# GitHub Actions / Azure DevOps / GitLab CI

# .github/workflows/deploy.yml
name: Deploy to AKS
on: [push]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: azure/k8s-set-context@v1
        with:
          kubeconfig: ${{ secrets.KUBE_CONFIG }}
      - run: kubectl apply -f k8s/
```

### 4. 使用 namespace 隔离环境

```bash
# 开发环境
kubectl create namespace development
kubectl apply -f k8s/ -n development

# 生产环境
kubectl create namespace production
kubectl apply -f k8s/ -n production
```

---

## 🚨 常见问题和解决方案

### 问题 1: Pod 启动失败（ImagePullBackOff）

**原因**: 新集群无法访问镜像

**解决**:
```bash
# 检查镜像是否可访问
docker pull shankswhite/perplexica:tavily-v1.1

# 如果是私有镜像，配置 imagePullSecrets
kubectl create secret docker-registry regcred --docker-server=... --docker-username=... --docker-password=...
```

### 问题 2: PVC Pending

**原因**: 新集群没有相应的 StorageClass

**解决**:
```bash
# 检查可用的 StorageClass
kubectl get storageclass

# 修改 PVC 配置
storageClassName: managed-premium  # 改为新集群支持的
```

### 问题 3: Service 无法访问

**原因**: DNS 解析问题

**解决**:
```bash
# 测试 DNS
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup perplexica-service

# 检查 Service
kubectl get svc
kubectl describe svc perplexica-service
```

### 问题 4: 数据丢失

**原因**: PVC 没有正确迁移

**解决**:
```bash
# 确保在部署前恢复数据
# 或使用 Azure Files 跨集群共享存储
```

---

## 🎉 总结

### 直接回答你的问题

> "是不是直接打包迁移部署然后就直接能用了？"

**答案**: 
- ✅ **80% 的情况：是的，直接迁移就能用**
- ⚠️ **20% 需要注意：数据、密钥、域名**

### 最简单的迁移路径

```
1. 确保配置在 Git 中
2. 连接到新集群
3. kubectl apply -f k8s/
4. 验证服务正常

完成！ ✅
```

### 需要额外处理的

```
⚠️ 持久化数据（PVC）→ 需要备份恢复
⚠️ Secrets → 需要重新创建
⚠️ 域名/DNS → 需要更新记录（如果有）
```

### 你的配置（ClusterIP）的优势

```
✅ 服务名称不变
✅ 无需修改应用代码
✅ 无需重新配置服务发现
✅ 迁移后自动工作
```

---

**文档更新时间**: 2025-11-17  
**适用场景**: Azure AKS 集群间迁移  
**推荐方式**: Git + kubectl apply

