#!/bin/bash

##############################################################################
# Perplexica AKS 部署脚本
# 
# 此脚本将：
# 1. 清理旧的 SearCrawl 部署
# 2. 部署 Perplexica 到 AKS
# 3. 验证部署状态
# 4. 测试 Tavily API
##############################################################################

set -e  # Exit on error

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 辅助函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo "================================================================================"
    echo "  $1"
    echo "================================================================================"
    echo ""
}

# 检查依赖
check_dependencies() {
    print_header "检查依赖"
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl 未安装，请先安装 kubectl"
        exit 1
    fi
    log_success "kubectl 已安装"
    
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI 未安装，请先安装 az"
        exit 1
    fi
    log_success "Azure CLI 已安装"
    
    # 检查 kubectl 连接
    if ! kubectl cluster-info &> /dev/null; then
        log_error "无法连接到 Kubernetes 集群，请检查 kubectl 配置"
        exit 1
    fi
    log_success "kubectl 已连接到集群"
}

# 步骤 1: 清理 SearCrawl
cleanup_searcrawl() {
    print_header "步骤 1/4: 清理 SearCrawl 部署"
    
    log_info "删除 SearCrawl 部署..."
    kubectl delete deployment searcrawl-api --ignore-not-found=true
    kubectl delete service searcrawl-service --ignore-not-found=true
    
    log_info "删除 SearXNG 部署..."
    kubectl delete deployment searxng --ignore-not-found=true
    kubectl delete service searxng-service --ignore-not-found=true
    kubectl delete configmap searxng-settings --ignore-not-found=true
    kubectl delete configmap searxng-config --ignore-not-found=true
    
    log_success "清理完成"
}

# 步骤 2: 部署 Perplexica
deploy_perplexica() {
    print_header "步骤 2/4: 部署 Perplexica"
    
    cd "$(dirname "$0")"
    
    if [ ! -f "k8s/deployment.yaml" ]; then
        log_error "找不到 k8s/deployment.yaml 文件"
        exit 1
    fi
    
    log_info "应用 Kubernetes 配置..."
    kubectl apply -f k8s/deployment.yaml
    
    log_info "等待 Pod 就绪（最多 120 秒）..."
    if kubectl wait --for=condition=ready pod -l app=perplexica --timeout=120s; then
        log_success "Pod 已就绪"
    else
        log_error "Pod 启动超时"
        log_info "查看 Pod 状态:"
        kubectl get pods -l app=perplexica
        log_info "查看 Pod 日志:"
        kubectl logs -l app=perplexica --tail=50
        exit 1
    fi
}

# 步骤 3: 验证部署
verify_deployment() {
    print_header "步骤 3/4: 验证部署"
    
    log_info "检查 Pod 状态..."
    kubectl get pods -l app=perplexica
    
    log_info "检查 Service 状态..."
    kubectl get svc perplexica-service
    
    log_info "检查 PVC 状态..."
    kubectl get pvc
    
    # 检查 Pod 健康状态
    POD_NAME=$(kubectl get pods -l app=perplexica -o jsonpath='{.items[0].metadata.name}')
    
    if [ -z "$POD_NAME" ]; then
        log_error "找不到 Perplexica Pod"
        exit 1
    fi
    
    log_info "Pod 名称: $POD_NAME"
    
    # 检查容器状态
    READY=$(kubectl get pod $POD_NAME -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')
    if [ "$READY" = "True" ]; then
        log_success "Pod 健康状态正常"
    else
        log_warning "Pod 可能未完全就绪"
        kubectl describe pod $POD_NAME
    fi
}

# 步骤 4: 测试 API
test_api() {
    print_header "步骤 4/4: 测试 Tavily API"
    
    log_info "设置 port-forward..."
    
    # 停止之前的 port-forward
    pkill -f "kubectl port-forward.*perplexica" || true
    sleep 2
    
    # 启动新的 port-forward（后台）
    kubectl port-forward service/perplexica-service 3000:80 > /tmp/perplexica-port-forward.log 2>&1 &
    PF_PID=$!
    
    # 等待 port-forward 就绪
    log_info "等待 port-forward 就绪..."
    sleep 5
    
    # 测试 Web UI
    log_info "测试 Web UI 连接..."
    if curl -s -f http://localhost:3000 > /dev/null; then
        log_success "Web UI 可访问: http://localhost:3000"
    else
        log_warning "Web UI 暂时无法访问，可能需要更多时间启动"
    fi
    
    # 测试 Tavily API
    log_info "测试 Tavily API..."
    
    TEST_RESPONSE=$(curl -s -X POST http://localhost:3000/api/tavily \
      -H "Content-Type: application/json" \
      -d '{
        "query": "test query",
        "max_results": 3
      }' || echo '{"error": "connection failed"}')
    
    if echo "$TEST_RESPONSE" | grep -q '"query"'; then
        log_success "Tavily API 测试成功"
        echo ""
        echo "API 响应示例:"
        echo "$TEST_RESPONSE" | jq '.' 2>/dev/null || echo "$TEST_RESPONSE"
    else
        log_warning "Tavily API 测试失败，但服务可能仍在启动中"
        echo "响应: $TEST_RESPONSE"
    fi
    
    echo ""
    log_info "Port-forward 进程 PID: $PF_PID"
    log_info "要停止 port-forward，运行: kill $PF_PID"
}

# 清理函数
cleanup_on_exit() {
    log_info "清理临时资源..."
    # Port-forward 会在终端关闭时自动停止
}

trap cleanup_on_exit EXIT

# 主函数
main() {
    print_header "Perplexica 部署到 Azure AKS"
    
    log_info "开始部署流程..."
    
    # 询问是否清理 SearCrawl
    echo ""
    read -p "是否清理旧的 SearCrawl 部署？[Y/n] " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        check_dependencies
        cleanup_searcrawl
    else
        log_info "跳过清理步骤"
        check_dependencies
    fi
    
    deploy_perplexica
    verify_deployment
    test_api
    
    print_header "部署完成！"
    
    cat << EOF
${GREEN}✅ Perplexica 已成功部署到 AKS！${NC}

📝 访问方式:
  - Web UI:    http://localhost:3000
  - Tavily API: http://localhost:3000/api/tavily

📖 API 文档:
  查看 DEPLOYMENT_GUIDE.md 获取详细的 API 使用说明

🔧 管理命令:
  - 查看日志:     kubectl logs -f -l app=perplexica
  - 查看状态:     kubectl get pods -l app=perplexica
  - 重启服务:     kubectl rollout restart deployment/perplexica
  - 停止 port-forward: pkill -f "kubectl port-forward.*perplexica"

🧪 测试命令:
  curl -X POST http://localhost:3000/api/tavily \\
    -H "Content-Type: application/json" \\
    -d '{"query": "AI latest news", "max_results": 5}' | jq .

📚 完整文档: ./DEPLOYMENT_GUIDE.md

${YELLOW}⚠️  注意: Port-forward 在后台运行，关闭终端会自动停止${NC}

EOF
}

# 运行主函数
main "$@"


