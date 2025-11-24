# 🚀 Open Deep Research - 使用指南

## 📋 场景示例：COD BO7 舆情分析

**研究目标**: 分析 Call of Duty Black Ops 7 在 2024年11月1日-15日期间的玩家舆情、评价和原因

---

## 🔐 访问方式

当前部署为 **ClusterIP（内部访问）**，有以下 3 种使用方式：

---

## 方式 1: Port-Forward 本地测试 ⭐ 推荐测试用

### 步骤 1: 建立端口转发

```bash
# 转发 ODR 服务到本地 8123 端口
kubectl port-forward -n deep-research svc/open-deep-research-service 8123:8123

# 保持终端运行，服务将在 http://localhost:8123 可访问
```

### 步骤 2: 使用 LangGraph Studio

1. 打开浏览器访问：
```
https://smith.langchain.com/studio/?baseUrl=http://localhost:8123
```

2. 在 Studio 界面输入研究请求：

**输入示例**:
```
Analyze Call of Duty Black Ops 7 player sentiment and feedback from November 1-15, 2024. 
Focus on:
1. Overall player sentiment (positive/negative)
2. Main complaints and issues
3. Praised features and aspects
4. Comparison with community expectations
Include specific examples from Reddit, gaming forums, and reviews.
```

3. 查看生成的深度研究报告

---

## 方式 2: Python API 调用

### 创建测试脚本

```python
#!/usr/bin/env python3
"""
COD BO7 舆情分析 - API 调用示例
"""
import asyncio
from langgraph_sdk import get_client

async def analyze_cod_bo7_sentiment():
    # 连接到 ODR 服务 (需要 port-forward)
    client = get_client(url="http://localhost:8123")
    
    # 研究请求
    research_query = """
    Analyze Call of Duty Black Ops 7 player sentiment and feedback from November 1-15, 2024.
    
    Research Focus:
    1. Overall Sentiment Analysis
       - Positive vs negative player reactions
       - Sentiment trends over the period
    
    2. Main Complaints and Issues
       - Technical problems (bugs, performance)
       - Gameplay balance issues
       - Content criticisms
    
    3. Praised Aspects
       - Popular features
       - Successful game modes
       - Community-appreciated changes
    
    4. Player Expectations vs Reality
       - Pre-launch hype vs actual experience
       - Comparison with previous COD titles
    
    Sources to prioritize:
    - Reddit (r/CallOfDuty, r/blackops6)
    - Gaming forums (IGN, GameFAQs)
    - YouTube comments
    - Steam reviews
    - Twitter/X discussions
    
    Time range: November 1-15, 2024
    """
    
    # 创建研究任务
    thread = await client.threads.create()
    
    # 运行研究
    async for chunk in client.runs.stream(
        thread["thread_id"],
        "agent",  # 使用 agent 工作流
        input={"messages": [{"role": "user", "content": research_query}]},
        stream_mode="updates"
    ):
        print(chunk)
    
    print("\n✅ 研究完成！")

if __name__ == "__main__":
    asyncio.run(analyze_cod_bo7_sentiment())
```

### 运行测试

```bash
# 确保 port-forward 正在运行
# 然后执行脚本
python test_cod_sentiment.py
```

---

## 方式 3: 在 AKS 内创建测试 Pod

### 步骤 1: 创建测试 Pod

```bash
# 创建交互式测试 Pod
kubectl run odr-test -n deep-research \
  --image=python:3.11 \
  --rm -it --restart=Never \
  -- /bin/bash
```

### 步骤 2: 在 Pod 内安装依赖

```bash
# 在 Pod 内执行
pip install langgraph-sdk httpx

# 创建测试脚本
cat > test_research.py << 'EOF'
import asyncio
from langgraph_sdk import get_client

async def main():
    # 使用 AKS 内部服务地址
    client = get_client(
        url="http://open-deep-research-service.deep-research.svc.cluster.local"
    )
    
    research_query = """
    Analyze Call of Duty Black Ops 7 player sentiment from Nov 1-15, 2024.
    Focus on: sentiment trends, main complaints, praised features, player expectations.
    """
    
    thread = await client.threads.create()
    
    async for chunk in client.runs.stream(
        thread["thread_id"],
        "agent",
        input={"messages": [{"role": "user", "content": research_query}]},
        stream_mode="updates"
    ):
        print(chunk)

asyncio.run(main())
EOF

# 运行测试
python test_research.py
```

---

## 🎯 针对你的场景的具体配置

### 为 COD 舆情分析优化 Perplexica 参数

当前 ODR 已配置以下参数（在 ConfigMap 中）：

```yaml
# 时间范围 - 可以调整
PERPLEXICA_TIME_RANGE: "month"  # 覆盖 Nov 1-15

# 域名过滤 - 已排除低质量网站
PERPLEXICA_EXCLUDE_DOMAINS: "pinterest.com,instagram.com,tiktok.com"

# 语言
PERPLEXICA_LANGUAGE: "en"

# 搜索引擎
# 默认使用: google, bing, duckduckgo
```

### 如果需要更精确的时间范围

你可以在查询中明确指定日期：

```python
research_query = """
Analyze Call of Duty Black Ops 7 player sentiment between November 1-15, 2024.

Use search queries like:
- "Call of Duty Black Ops 7 review after:2024-11-01 before:2024-11-16"
- "COD BO7 player feedback site:reddit.com after:2024-11-01"
- "Black Ops 7 complaints November 2024"

Focus on...
"""
```

---

## 📊 期望的报告输出

ODR 将生成包含以下内容的深度研究报告：

### 1. 执行摘要
- 整体舆情概览
- 关键发现
- 主要趋势

### 2. 详细分析

#### 2.1 舆情分析
- 正面评价占比
- 负面评价占比
- 中性评价占比
- 情绪变化趋势（Nov 1-15）

#### 2.2 主要投诉
- 技术问题（bug、性能）
- 游戏平衡性问题
- 内容批评
- 每个问题的具体案例和来源

#### 2.3 受好评方面
- 热门功能
- 成功的游戏模式
- 社区赞赏的改进
- 具体评价引用

#### 2.4 期望 vs 现实
- 发售前炒作 vs 实际体验
- 与前作对比
- 社区期望的满足程度

### 3. 结论和建议
- 关键洞察
- 改进建议
- 未来关注点

### 4. 数据来源
- Reddit 讨论
- 游戏论坛帖子
- YouTube 评论
- Steam 评论
- 社交媒体讨论

---

## 🔄 如果需要公开访问

### 选项 A: 使用 LoadBalancer

```bash
# 修改 Service 类型
kubectl patch svc open-deep-research-service -n deep-research \
  -p '{"spec":{"type":"LoadBalancer"}}'

# 获取外部 IP
kubectl get svc -n deep-research open-deep-research-service
```

### 选项 B: 创建 Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: odr-ingress
  namespace: deep-research
spec:
  rules:
  - host: odr.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: open-deep-research-service
            port:
              number: 80
```

⚠️ **安全提醒**: 如果公开访问，建议配置：
- API Key 认证
- Rate limiting
- IP 白名单

---

## 🧪 快速测试（推荐）

### 一键测试脚本

```bash
#!/bin/bash
# quick_test.sh

echo "🚀 启动 Port-Forward..."
kubectl port-forward -n deep-research svc/open-deep-research-service 8123:80 &
PF_PID=$!

sleep 5

echo "🌐 打开 LangGraph Studio..."
open "https://smith.langchain.com/studio/?baseUrl=http://localhost:8123"

echo ""
echo "✅ Studio 已打开！"
echo ""
echo "📝 在 Studio 中输入研究请求："
echo ""
echo "Analyze Call of Duty Black Ops 7 player sentiment from November 1-15, 2024."
echo "Focus on sentiment trends, complaints, praised features, and player expectations."
echo ""
echo "⏹️  完成后按 Ctrl+C 停止 port-forward"

wait $PF_PID
```

运行：
```bash
chmod +x quick_test.sh
./quick_test.sh
```

---

## 📚 相关文档

- `AKS_DEPLOYMENT_GUIDE.md` - 完整部署指南
- `FULL_PARAMETER_SUPPORT.md` - 全部参数说明
- `PERPLEXICA_INTEGRATION.md` - Perplexica 集成详解

---

## 🆘 常见问题

### Q: 研究需要多长时间？

A: 取决于查询复杂度，通常：
- 简单查询: 2-5 分钟
- 中等复杂度: 5-10 分钟
- 深度研究: 10-20 分钟

### Q: 如何查看进度？

A: 
```bash
# 查看实时日志
kubectl logs -n deep-research -l app=open-deep-research -f
```

### Q: 成本如何？

A: 主要成本来自 OpenAI API 调用：
- GPT-4: 用于研究和报告生成
- GPT-4-mini: 用于总结和压缩
- Perplexica: 免费（自托管）

---

## 🎉 开始研究！

现在你已经知道如何使用 Open Deep Research 了！

推荐流程：
1. ✅ 使用 `kubectl port-forward` 建立连接
2. ✅ 在 LangGraph Studio 中输入研究请求
3. ✅ 等待 5-15 分钟生成报告
4. ✅ 分析结果并导出报告

祝研究顺利！🚀

