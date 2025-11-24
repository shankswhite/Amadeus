#!/bin/bash

# Cloudflare Tunnel Connection Test Script
# Tests the Open Deep Research API through Cloudflare Tunnel

set -e

DOMAIN="odr-api.aiverse.chat"
FULL_URL="https://${DOMAIN}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Cloudflare Tunnel Connection Test"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 1: DNS Resolution
echo "📡 Test 1: DNS Resolution"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Checking: ${DOMAIN}"
echo ""

if nslookup ${DOMAIN} 1.1.1.1 > /dev/null 2>&1; then
    echo "✅ DNS resolution successful"
    nslookup ${DOMAIN} 1.1.1.1 | grep -A2 "Name:"
else
    echo "❌ DNS resolution failed"
    echo "   Please check:"
    echo "   1. Public Hostname is configured in Zero Trust"
    echo "   2. DNS record exists in Cloudflare DNS"
    echo "   3. Wait a few minutes for DNS propagation"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 Test 2: HTTPS Connection"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Connecting to: ${FULL_URL}"
echo ""

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 10 ${FULL_URL} 2>&1 || echo "000")

if [ "$HTTP_CODE" = "000" ]; then
    echo "❌ Connection failed"
    echo "   Cannot reach ${FULL_URL}"
    echo "   Possible issues:"
    echo "   - Tunnel not connected"
    echo "   - Service not running in AKS"
    echo "   - Firewall blocking connection"
    exit 1
elif [ "$HTTP_CODE" = "404" ] || [ "$HTTP_CODE" = "403" ]; then
    echo "✅ Connection successful (HTTP $HTTP_CODE)"
    echo "   Tunnel is working! (404/403 is expected for root path)"
elif [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Connection successful (HTTP 200)"
    echo "   Service is responding!"
else
    echo "⚠️  Unexpected response: HTTP $HTTP_CODE"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Test 3: Response Headers"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

curl -I -s -m 10 ${FULL_URL} | head -15 || true

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Test 4: SSL Certificate"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo | openssl s_client -connect ${DOMAIN}:443 -servername ${DOMAIN} 2>/dev/null | \
    openssl x509 -noout -subject -issuer -dates 2>/dev/null || \
    echo "⚠️  Could not retrieve SSL certificate info"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 Test 5: LangGraph Studio Access"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "To use LangGraph Studio:"
echo ""
echo "1. Visit: https://smith.langchain.com/studio"
echo "2. Set Base URL: ${FULL_URL}"
echo "3. Create a new thread and test"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Connection Test Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$HTTP_CODE" != "000" ]; then
    echo "✨ Your Open Deep Research API is accessible via:"
    echo "   ${FULL_URL}"
    echo ""
    echo "Next steps:"
    echo "  1. Test with LangGraph Studio"
    echo "  2. Configure your client applications"
    echo "  3. Share the URL with your team"
    echo ""
else
    echo "⚠️  Connection failed. Please check configuration."
    echo ""
    echo "Debugging steps:"
    echo "  1. Check AKS service: kubectl get svc -n deep-research"
    echo "  2. Check cloudflared logs: kubectl logs -n cloudflare-tunnel -l app=cloudflared"
    echo "  3. Verify Public Hostname in Zero Trust console"
    echo ""
fi

