#!/bin/bash

# ====================================================================
# Cloudflare Tunnel + ODR API 测试脚本
# ====================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                                           ║${NC}"
echo -e "${BLUE}║              🧪 Open Deep Research API 测试脚本                           ║${NC}"
echo -e "${BLUE}║                                                                           ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 配置
API_URL="${API_URL:-https://odr-api.yourdomain.com}"
CLIENT_ID="${CF_CLIENT_ID:-}"
CLIENT_SECRET="${CF_CLIENT_SECRET:-}"

echo -e "${YELLOW}当前配置:${NC}"
echo "  API URL: $API_URL"
echo "  Client ID: ${CLIENT_ID:-(未设置)}"
echo "  Client Secret: ${CLIENT_SECRET:+(已设置)}"
echo ""

# 选择认证方式
if [ -z "$CLIENT_ID" ] || [ -z "$CLIENT_SECRET" ]; then
    echo -e "${YELLOW}⚠️  未检测到 Service Token 配置${NC}"
    echo ""
    echo "请选择测试方式:"
    echo "  1) 不使用认证（Public Access）"
    echo "  2) 输入 Service Token"
    echo "  3) 退出"
    echo ""
    read -p "选择 [1-3]: " choice
    
    case $choice in
        1)
            echo -e "${GREEN}使用公开访问模式${NC}"
            AUTH_HEADERS=""
            ;;
        2)
            read -p "CF-Access-Client-Id: " CLIENT_ID
            read -sp "CF-Access-Client-Secret: " CLIENT_SECRET
            echo ""
            AUTH_HEADERS="-H 'CF-Access-Client-Id: $CLIENT_ID' -H 'CF-Access-Client-Secret: $CLIENT_SECRET'"
            ;;
        3)
            echo "退出"
            exit 0
            ;;
        *)
            echo -e "${RED}无效选择${NC}"
            exit 1
            ;;
    esac
else
    AUTH_HEADERS="-H 'CF-Access-Client-Id: $CLIENT_ID' -H 'CF-Access-Client-Secret: $CLIENT_SECRET'"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}测试 1: 基础连接测试${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "测试 API 根路径..."
if [ -z "$AUTH_HEADERS" ]; then
    RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/" || echo "000")
else
    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -H "CF-Access-Client-Id: $CLIENT_ID" \
        -H "CF-Access-Client-Secret: $CLIENT_SECRET" \
        "$API_URL/" || echo "000")
fi

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" -eq "200" ] || [ "$HTTP_CODE" -eq "403" ] || [ "$HTTP_CODE" -eq "404" ]; then
    echo -e "${GREEN}✅ 连接成功 (HTTP $HTTP_CODE)${NC}"
    if [ ! -z "$BODY" ]; then
        echo "响应: $BODY"
    fi
else
    echo -e "${RED}❌ 连接失败 (HTTP $HTTP_CODE)${NC}"
    if [ ! -z "$BODY" ]; then
        echo "错误: $BODY"
    fi
    exit 1
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}测试 2: 创建研究线程${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "创建新的研究线程..."
if [ -z "$AUTH_HEADERS" ]; then
    THREAD_RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X POST "$API_URL/threads" \
        -H "Content-Type: application/json" \
        -d '{"assistant_id":"agent","metadata":{}}' || echo '{"error":"request failed"}\n000')
else
    THREAD_RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X POST "$API_URL/threads" \
        -H "CF-Access-Client-Id: $CLIENT_ID" \
        -H "CF-Access-Client-Secret: $CLIENT_SECRET" \
        -H "Content-Type: application/json" \
        -d '{"assistant_id":"agent","metadata":{}}' || echo '{"error":"request failed"}\n000')
fi

THREAD_HTTP_CODE=$(echo "$THREAD_RESPONSE" | tail -n1)
THREAD_BODY=$(echo "$THREAD_RESPONSE" | head -n-1)

if [ "$THREAD_HTTP_CODE" -eq "200" ] || [ "$THREAD_HTTP_CODE" -eq "201" ]; then
    echo -e "${GREEN}✅ 线程创建成功 (HTTP $THREAD_HTTP_CODE)${NC}"
    echo "响应: $THREAD_BODY"
    
    # 尝试提取 thread_id
    THREAD_ID=$(echo "$THREAD_BODY" | grep -o '"thread_id":"[^"]*"' | cut -d'"' -f4 || echo "")
    if [ ! -z "$THREAD_ID" ]; then
        echo -e "${GREEN}Thread ID: $THREAD_ID${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  线程创建失败或需要认证 (HTTP $THREAD_HTTP_CODE)${NC}"
    echo "响应: $THREAD_BODY"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}测试总结${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ "$HTTP_CODE" -eq "200" ] || [ "$HTTP_CODE" -eq "403" ] || [ "$HTTP_CODE" -eq "404" ]; then
    echo -e "${GREEN}✅ Cloudflare Tunnel 连接正常${NC}"
    echo -e "${GREEN}✅ ODR 服务可达${NC}"
else
    echo -e "${RED}❌ 连接异常，请检查配置${NC}"
fi

echo ""
echo -e "${YELLOW}💡 下一步:${NC}"
echo "  1. 如果看到 403，需要配置 Cloudflare Access 策略"
echo "  2. 如果测试成功，可以开始使用 API 进行研究"
echo "  3. 查看完整 API 文档: README.md"
echo ""

echo -e "${BLUE}📝 环境变量配置（可选）:${NC}"
echo "  export API_URL='https://odr-api.yourdomain.com'"
echo "  export CF_CLIENT_ID='your-client-id'"
echo "  export CF_CLIENT_SECRET='your-client-secret'"
echo "  ./test-api.sh"
echo ""


