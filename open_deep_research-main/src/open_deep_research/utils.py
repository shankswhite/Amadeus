"""Utility functions and helpers for the Deep Research agent."""

import asyncio
import logging
import os
import warnings
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Dict, List, Literal, Optional

import aiohttp

# Initialize logger for this module
logger = logging.getLogger(__name__)
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    MessageLikeRepresentation,
    filter_messages,
)
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import (
    BaseTool,
    InjectedToolArg,
    StructuredTool,
    ToolException,
    tool,
)
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.config import get_store
from mcp import McpError
from tavily import AsyncTavilyClient

from open_deep_research.configuration import Configuration, SearchAPI
from open_deep_research.perplexica_client import AsyncPerplexicaClient
from open_deep_research.prompts import summarize_webpage_prompt
from open_deep_research.state import ResearchComplete, Summary

# Import SearCrawl client (for search + crawling in one call)
try:
    from open_deep_research.searcrawl_client import AsyncSearCrawlClient
except ImportError:
    # If searcrawl_client is not in the package, try local import
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    try:
        from searcrawl_client import AsyncSearCrawlClient
    except ImportError:
        AsyncSearCrawlClient = None  # Will fall back to Perplexica

##########################
# Tavily Search Tool Utils
##########################
TAVILY_SEARCH_DESCRIPTION = (
    "A search engine optimized for comprehensive, accurate, and trusted results. "
    "Useful for when you need to answer questions about current events."
)
@tool(description=TAVILY_SEARCH_DESCRIPTION)
async def tavily_search(
    queries: List[str],
    max_results: Annotated[int, InjectedToolArg] = 5,
    topic: Annotated[Literal["general", "news", "finance"], InjectedToolArg] = "general",
    config: RunnableConfig = None
) -> str:
    """Fetch and summarize search results from Tavily search API.

    Args:
        queries: List of search queries to execute
        max_results: Maximum number of results to return per query
        topic: Topic filter for search results (general, news, or finance)
        config: Runtime configuration for API keys and model settings

    Returns:
        Formatted string containing summarized search results
    """
    # Step 1: Execute search queries asynchronously
    # Note: include_raw_content=False to use search engine summaries directly
    # This avoids AI summarization, reduces cost, and prevents LangGraph bugs
    
    search_results = await tavily_search_async(
        queries,
        max_results=max_results,
        topic=topic,
        include_raw_content=False,  # Use search engine summaries (faster, cheaper)
        config=config
    )
    
    # Step 2: Deduplicate results by URL to avoid processing the same content multiple times
    unique_results = {}
    extracted_images = []  # 收集所有提取的图片
    
    for response in search_results:
        for result in response['results']:
            url = result['url']
            if url not in unique_results:
                unique_results[url] = {**result, "query": response['query']}
                
                # 提取图片：优先使用 Perplexica 返回的 img_src
                if result.get('img_src'):
                    extracted_images.append({
                        'url': result['img_src'],
                        'source': url,
                        'title': result.get('title', '')
                    })
                
                # 从 raw_content 中提取额外的图片（如果有）
                raw_content = result.get('raw_content', '')
                if raw_content:
                    import re
                    # 提取 <img> 标签中的 src
                    img_matches = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', raw_content)
                    for img_url in img_matches[:3]:  # 每个网页最多提取3张图片
                        if img_url.startswith('http'):
                            extracted_images.append({
                                'url': img_url,
                                'source': url,
                                'title': result.get('title', '')
                            })
    
    # Step 2.5: 🆕 使用 Crawl4AI 获取完整网页内容
    # (如果使用SearCrawl，则跳过此步骤，因为内容已在搜索结果中)
    logger = logging.getLogger(__name__)
    
    use_searcrawl = os.getenv("USE_SEARCRAWL", "false").lower() == "true"
    
    if use_searcrawl:
        logger.info("✅ Using SearCrawl - content already crawled during search, skipping Crawl4AI step!")
        logger.info(f"   📊 Already have {len(unique_results)} URLs with full content from SearCrawl")
    elif len(unique_results) == 0:
        logger.warning("unique_results is EMPTY! Skipping content crawling")
    else:
        urls_to_crawl = list(unique_results.keys())
        logger.info(f"📚 Crawling {len(urls_to_crawl)} URLs with Crawl4AI...")
        
        # 🆕 打印所有待爬取的 URL（前10个）
        logger.info("🌐 URLs to crawl:")
        for i, url in enumerate(urls_to_crawl[:10], 1):
            domain = url.split('/')[2] if len(url.split('/')) > 2 else url
            logger.info(f"   {i}. {domain}")
        if len(urls_to_crawl) > 10:
            logger.info(f"   ... and {len(urls_to_crawl) - 10} more")
        
        # Import Crawl4AI modules
        from crawl4ai import (
            AsyncWebCrawler,
            BrowserConfig,
            CrawlerRunConfig,
            CacheMode,
        )
        from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
        from crawl4ai.content_filter_strategy import PruningContentFilter
        
        # 配置浏览器（增加并发）
        browser_config = BrowserConfig(
            headless=True,
            verbose=False,
            # 🆕 增加并发数（使用我们自己的服务，可以更激进）
            browser_type="chromium",
        )
        
        # 配置 Markdown 生成器（保留图片）
        md_generator = DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(
                threshold=float(os.getenv("CRAWL4AI_CONTENT_THRESHOLD", "0.3")),
                threshold_type="fixed"
            ),
            options={
                "ignore_links": True,
                "ignore_images": False,  # 保留图片！
                "escape_html": False,
            },
        )
        
        # 🆕 减少超时时间，加快速度
        timeout_seconds = int(os.getenv("CRAWL4AI_TIMEOUT", "15"))  # 从30秒减少到15秒
        
        # 配置爬取参数
        run_config = CrawlerRunConfig(
            word_count_threshold=10,
            exclude_external_links=True,
            remove_overlay_elements=True,
            excluded_tags=["header", "footer", "iframe", "nav"],
            process_iframes=False,  # 禁用 iframe 处理以提高速度
            markdown_generator=md_generator,
            cache_mode=CacheMode.BYPASS,
            page_timeout=timeout_seconds * 1000,  # 转换为毫秒
            wait_until="domcontentloaded",  # 不等待所有资源，加快速度
        )
        
        logger.info(f"⚙️  Crawl4AI config: timeout={timeout_seconds}s, threshold={os.getenv('CRAWL4AI_CONTENT_THRESHOLD', '0.3')}, concurrent=auto")
        
        try:
            import time
            import asyncio
            start_time = time.time()
            
            # 🆕 并行爬取，每个URL独立超时保护
            async with AsyncWebCrawler(config=browser_config) as crawler:
                logger.info(f"🚀 Starting parallel crawl with timeout protection ({timeout_seconds}s per URL)...")
                logger.info(f"   共 {len(urls_to_crawl)} 个URL")
                
                # 为每个URL创建一个带超时的任务
                async def crawl_with_timeout(url: str, index: int):
                    url_short = url.split('/')[2] if len(url.split('/')) > 2 else url[:50]
                    logger.info(f"[{index+1}/{len(urls_to_crawl)}] 🌐 爬取: {url_short}")
                    
                    try:
                        result = await asyncio.wait_for(
                            crawler.arun(url=url, config=run_config),
                            timeout=timeout_seconds
                        )
                        
                        if result and result.success and result.markdown:
                            content_len = len(result.markdown)
                            logger.info(f"[{index+1}] ✅ {url_short} - {content_len:,} chars")
                        else:
                            logger.warning(f"[{index+1}] ❌ {url_short} - 内容为空")
                        
                        return result
                        
                    except asyncio.TimeoutError:
                        logger.warning(f"[{index+1}] ❌ {url_short} - 超时 ({timeout_seconds}s)")
                        return None
                    except Exception as e:
                        logger.error(f"[{index+1}] ❌ {url_short} - 错误: {str(e)}")
                        return None
                
                # 并行爬取所有URL
                crawl_tasks = [
                    crawl_with_timeout(url, i) 
                    for i, url in enumerate(urls_to_crawl)
                ]
                results = await asyncio.gather(*crawl_tasks, return_exceptions=True)
                
                # 过滤掉None和异常
                results = [r for r in results if r and not isinstance(r, Exception)]
                
                elapsed = time.time() - start_time
                success_count = sum(1 for r in results if r and r.success)
                failed_count = len(urls_to_crawl) - success_count
                
                logger.info(f"⏱️  Crawl completed in {elapsed:.1f}s")
                logger.info(f"📊 Crawl4AI: {success_count} ✅ / {failed_count} ❌ / {len(urls_to_crawl)} total")
                logger.info(f"⚡ Speed: {len(urls_to_crawl)/elapsed:.1f} pages/sec")
                
                # 更新 unique_results 的 raw_content
                updated_count = 0
                failed_count = 0
                
                for result in results:
                    url_short = result.url.split('/')[2] if len(result.url.split('/')) > 2 else result.url[:50]
                    
                    if result.success and result.markdown and result.url in unique_results:
                        content_len = len(result.markdown)
                        unique_results[result.url]['raw_content'] = result.markdown
                        updated_count += 1
                        logger.info(f"   ✅ {url_short} - {content_len:,} 字符")
                        
                        # 从 Markdown 内容中提取图片链接
                        import re
                        img_matches = re.findall(r'!\[.*?\]\((https?://[^\)]+)\)', result.markdown)
                        for img_url in img_matches[:5]:  # 每页最多5张图片
                            extracted_images.append({
                                'url': img_url,
                                'source': result.url,
                                'title': unique_results[result.url].get('title', '')
                            })
                    else:
                        failed_count += 1
                        error_msg = result.error_message if hasattr(result, 'error_message') else "Unknown error"
                        logger.warning(f"   ❌ {url_short} - {error_msg[:50]}")
                
                logger.info(f"✅ Crawl4AI: {updated_count} ✅ / {failed_count} ❌ / {len(urls_to_crawl)} total")
                logger.info(f"🖼️  Total images extracted: {len(extracted_images)}")
                if elapsed > 0:
                    logger.info(f"⚡ Speed: {len(urls_to_crawl) / elapsed:.1f} pages/sec")
        except Exception as e:
            logger.error(f"❌ Crawl4AI failed: {str(e)}")
            import traceback
            logger.error(f"   Traceback: {traceback.format_exc()}")
            # 即使爬取失败，也继续使用 Perplexica 的原始摘要
    
    # Step 3: Set up the summarization model with configuration
    configurable = Configuration.from_runnable_config(config)
    
    # Character limit to stay within model token limits (configurable)
    max_char_to_include = configurable.max_content_length
    
    # Initialize summarization model with retry logic
    model_api_key = get_api_key_for_model(configurable.summarization_model, config)
    summarization_model = init_chat_model(
        model=configurable.summarization_model,
        max_tokens=configurable.summarization_model_max_tokens,
        api_key=model_api_key,
        tags=["langsmith:nostream"]
    ).with_structured_output(Summary).with_retry(
        stop_after_attempt=configurable.max_structured_output_retries
    )
    
    # Step 4: Create summarization tasks (skip empty content)
    async def noop():
        """No-op function for results without raw content."""
        return None
    
    summarization_tasks = [
        noop() if not result.get("raw_content") 
        else summarize_webpage(
            summarization_model, 
            result['raw_content'][:max_char_to_include]
        )
        for result in unique_results.values()
    ]
    
    # Step 5: Execute all summarization tasks in parallel
    summaries = await asyncio.gather(*summarization_tasks)
    
    # Step 6: Combine results with their summaries
    summarized_results = {
        url: {
            'title': result['title'], 
            'content': result['content'] if summary is None else summary
        }
        for url, result, summary in zip(
            unique_results.keys(), 
            unique_results.values(), 
            summaries
        )
    }
    
    # Step 7: Format the final output
    if not summarized_results:
        return "No valid search results found. Please try different search queries or use a different search API."
    
    formatted_output = "Search results: \n\n"
    for i, (url, result) in enumerate(summarized_results.items()):
        formatted_output += f"\n\n--- SOURCE {i+1}: {result['title']} ---\n"
        formatted_output += f"URL: {url}\n\n"
        formatted_output += f"SUMMARY:\n{result['content']}\n\n"
        formatted_output += "\n\n" + "-" * 80 + "\n"
    
    # Step 7.5: 添加提取的图片列表（让LLM知道有哪些图片可用）
    if extracted_images:
        formatted_output += "\n\n=== AVAILABLE IMAGES FROM SEARCH RESULTS ===\n\n"
        formatted_output += f"Found {len(extracted_images)} images from the search results. "
        formatted_output += "Use these images in your report using Markdown format: ![description](url)\n\n"
        
        for i, img in enumerate(extracted_images[:20], 1):  # 最多传递20张图片
            formatted_output += f"{i}. {img['url']}\n"
            formatted_output += f"   Source: {img['title']}\n"
            formatted_output += f"   From: {img['source']}\n\n"
        
        formatted_output += "=== END OF IMAGES ===\n\n"
    
    # Step 8: Append raw search results as JSON for client-side extraction
    # This allows clients to parse and save search logs separately
    import json
    from datetime import datetime
    
    search_log = {
        "timestamp": datetime.now().isoformat(),
        "queries": queries,
        "parameters": {
            "max_results": max_results,
            "topic": topic,
            "include_raw_content": False  # Using search engine summaries directly
        },
        "raw_results": search_results,
        "processed_count": len(summarized_results)
    }
    
    # Append as a special comment block that can be extracted
    formatted_output += "\n\n<!-- SEARCH_LOG_JSON\n"
    formatted_output += json.dumps(search_log, ensure_ascii=False, indent=2)
    formatted_output += "\n-->\n"
    
    return formatted_output

async def tavily_search_async(
    search_queries, 
    max_results: int = 5, 
    topic: Literal["general", "news", "finance"] = "general", 
    include_raw_content: bool = False,  # Default: use search engine summaries (faster)
    config: RunnableConfig = None
):
    """Execute multiple search queries asynchronously with selected backend.
    
    This function automatically selects the search backend based on environment variables:
    - USE_SEARCRAWL=true: Use SearCrawl (search + crawl in one call) ← RECOMMENDED!
    - USE_PERPLEXICA=true (default): Use Perplexica (search only, requires separate crawling)
    - USE_PERPLEXICA=false: Use official Tavily API
    
    Args:
        search_queries: List of search query strings to execute
        max_results: Maximum number of results per query
        topic: Topic category for filtering results ("general", "news", "finance")
        include_raw_content: Whether to include full webpage content
        config: Runtime configuration for API key access
        
    Returns:
        List of search result dictionaries in Tavily-compatible format
        
    Note:
        When using SearCrawl, results will already contain full webpage content (raw_content),
        eliminating the need for separate Jina Reader or Crawl4AI calls!
    """
    # Determine which search backend to use (priority: SearCrawl > Perplexica > Tavily)
    use_searcrawl = os.getenv("USE_SEARCRAWL", "false").lower() == "true"
    use_perplexica = os.getenv("USE_PERPLEXICA", "true").lower() == "true"
    
    if use_searcrawl and AsyncSearCrawlClient:
        # ✨ Use SearCrawl as search+crawl backend (NO separate crawling needed!)
        searcrawl_url = os.getenv("SEARCRAWL_API_URL", "http://searcrawl-service:3000")
        search_client = AsyncSearCrawlClient(
            api_key=None,  # SearCrawl doesn't require API key for internal AKS access
            base_url=searcrawl_url
        )
        
        logger.info(f"🔍 Using SearCrawl backend: {searcrawl_url}")
        logger.info("   ✅ SearCrawl will search AND crawl in one call (no separate crawling needed!)")
        
        # Create search tasks (SearCrawl handles crawling automatically)
        search_tasks = [
            search_client.search(
                query,
                max_results=max_results,
                include_raw_content=include_raw_content,
                topic=topic
            )
            for query in search_queries
        ]
    elif use_perplexica:
        # Use Perplexica as search backend
        perplexica_url = os.getenv("PERPLEXICA_API_URL", "http://perplexica-service/api/tavily")
        search_client = AsyncPerplexicaClient(
            api_key=None,  # Perplexica doesn't require API key for internal AKS access
            base_url=perplexica_url
        )
        
        # === Read advanced parameters from environment variables ===
        # These provide global defaults that can be overridden per-request
        
        # Time range control
        perplexica_time_range = os.getenv("PERPLEXICA_TIME_RANGE")  # "day", "week", "month", "year"
        perplexica_days = os.getenv("PERPLEXICA_DAYS")  # Last N days
        
        # Domain filtering
        perplexica_include_domains = os.getenv("PERPLEXICA_INCLUDE_DOMAINS")  # Comma-separated
        perplexica_exclude_domains = os.getenv("PERPLEXICA_EXCLUDE_DOMAINS", "pinterest.com,instagram.com")  # Default excludes
        
        # Search control
        perplexica_language = os.getenv("PERPLEXICA_LANGUAGE", "en")
        perplexica_engines = os.getenv("PERPLEXICA_ENGINES")  # Comma-separated
        perplexica_safesearch = os.getenv("PERPLEXICA_SAFESEARCH", "2")  # Default: strict
        perplexica_search_depth = os.getenv("PERPLEXICA_SEARCH_DEPTH", "basic")
        
        # Content control
        perplexica_include_answer = os.getenv("PERPLEXICA_INCLUDE_ANSWER", "false").lower() == "true"
        perplexica_include_images = os.getenv("PERPLEXICA_INCLUDE_IMAGES", "false").lower() == "true"
        
        # Performance control
        perplexica_timeout = os.getenv("PERPLEXICA_TIMEOUT", "300")  # Default: 5 minutes
        
        # Parse comma-separated lists
        def parse_list(value: str) -> list:
            return [item.strip() for item in value.split(",")] if value else None
        
        # Prepare advanced parameters
        advanced_params = {
            "language": perplexica_language,
            "search_depth": perplexica_search_depth,
            "safesearch": perplexica_safesearch,
            "timeout": int(perplexica_timeout) if perplexica_timeout else None,
            "include_answer": perplexica_include_answer,
            "include_images": perplexica_include_images,
        }
        
        # Add time range
        if perplexica_time_range:
            advanced_params["time_range"] = perplexica_time_range
        if perplexica_days:
            advanced_params["days"] = int(perplexica_days)
        
        # Add domain filtering
        if perplexica_include_domains:
            advanced_params["include_domains"] = parse_list(perplexica_include_domains)
        if perplexica_exclude_domains:
            advanced_params["exclude_domains"] = parse_list(perplexica_exclude_domains)
        
        # Add search engines
        if perplexica_engines:
            advanced_params["engines"] = parse_list(perplexica_engines)
        
        # Create search tasks with all parameters
        search_tasks = [
            search_client.search(
                query,
                max_results=max_results,
                include_raw_content=include_raw_content,
                topic=topic,
                **advanced_params  # Pass all advanced parameters
            )
            for query in search_queries
        ]
    else:
        # Use official Tavily API (only supports basic parameters)
        search_client = AsyncTavilyClient(api_key=get_tavily_api_key(config))
        
        search_tasks = [
            search_client.search(
                query,
                max_results=max_results,
                include_raw_content=include_raw_content,
                topic=topic
            )
            for query in search_queries
        ]
    
    try:

        search_results = []
        request_delay = float(os.getenv("SEARCH_REQUEST_DELAY", "5.0"))  # 默认5秒延迟
        
        for i, task in enumerate(search_tasks):
            if i > 0: 
                await asyncio.sleep(request_delay)
            
            result = await task
            search_results.append(result)
        
        return search_results
    finally:
        # Clean up client resources if using Perplexica or SearCrawl
        if (use_searcrawl or use_perplexica) and hasattr(search_client, 'close'):
            await search_client.close()

async def summarize_webpage(model: BaseChatModel, webpage_content: str) -> str:
    """Summarize webpage content using AI model with timeout protection.
    
    Args:
        model: The chat model configured for summarization
        webpage_content: Raw webpage content to be summarized
        
    Returns:
        Formatted summary with key excerpts, or original content if summarization fails
    """
    try:
        # Create prompt with current date context
        prompt_content = summarize_webpage_prompt.format(
            webpage_content=webpage_content, 
            date=get_today_str()
        )
        
        # Execute summarization with timeout to prevent hanging
        summary = await asyncio.wait_for(
            model.ainvoke([HumanMessage(content=prompt_content)]),
            timeout=60.0  # 60 second timeout for summarization
        )
        
        # Format the summary with structured sections
        formatted_summary = (
            f"<summary>\n{summary.summary}\n</summary>\n\n"
            f"<key_excerpts>\n{summary.key_excerpts}\n</key_excerpts>"
        )
        
        return formatted_summary
        
    except asyncio.TimeoutError:
        # Timeout during summarization - return original content
        logging.warning("Summarization timed out after 60 seconds, returning original content")
        return webpage_content
    except Exception as e:
        # Other errors during summarization - log and return original content
        logging.warning(f"Summarization failed with error: {str(e)}, returning original content")
        return webpage_content

##########################
# Reflection Tool Utils
##########################

@tool(description="Strategic reflection tool for research planning")
def think_tool(reflection: str) -> str:
    """Tool for strategic reflection on research progress and decision-making.

    Use this tool after each search to analyze results and plan next steps systematically.
    This creates a deliberate pause in the research workflow for quality decision-making.

    When to use:
    - After receiving search results: What key information did I find?
    - Before deciding next steps: Do I have enough to answer comprehensively?
    - When assessing research gaps: What specific information am I still missing?
    - Before concluding research: Can I provide a complete answer now?

    Reflection should address:
    1. Analysis of current findings - What concrete information have I gathered?
    2. Gap assessment - What crucial information is still missing?
    3. Quality evaluation - Do I have sufficient evidence/examples for a good answer?
    4. Strategic decision - Should I continue searching or provide my answer?

    Args:
        reflection: Your detailed reflection on research progress, findings, gaps, and next steps

    Returns:
        Confirmation that reflection was recorded for decision-making
    """
    return f"Reflection recorded: {reflection}"

##########################
# MCP Utils
##########################

async def get_mcp_access_token(
    supabase_token: str,
    base_mcp_url: str,
) -> Optional[Dict[str, Any]]:
    """Exchange Supabase token for MCP access token using OAuth token exchange.
    
    Args:
        supabase_token: Valid Supabase authentication token
        base_mcp_url: Base URL of the MCP server
        
    Returns:
        Token data dictionary if successful, None if failed
    """
    try:
        # Prepare OAuth token exchange request data
        form_data = {
            "client_id": "mcp_default",
            "subject_token": supabase_token,
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "resource": base_mcp_url.rstrip("/") + "/mcp",
            "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
        }
        
        # Execute token exchange request
        async with aiohttp.ClientSession() as session:
            token_url = base_mcp_url.rstrip("/") + "/oauth/token"
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            
            async with session.post(token_url, headers=headers, data=form_data) as response:
                if response.status == 200:
                    # Successfully obtained token
                    token_data = await response.json()
                    return token_data
                else:
                    # Log error details for debugging
                    response_text = await response.text()
                    logging.error(f"Token exchange failed: {response_text}")
                    
    except Exception as e:
        logging.error(f"Error during token exchange: {e}")
    
    return None

async def get_tokens(config: RunnableConfig):
    """Retrieve stored authentication tokens with expiration validation.
    
    Args:
        config: Runtime configuration containing thread and user identifiers
        
    Returns:
        Token dictionary if valid and not expired, None otherwise
    """
    store = get_store()
    
    # Extract required identifiers from config
    thread_id = config.get("configurable", {}).get("thread_id")
    if not thread_id:
        return None
        
    user_id = config.get("metadata", {}).get("owner")
    if not user_id:
        return None
    
    # Retrieve stored tokens
    tokens = await store.aget((user_id, "tokens"), "data")
    if not tokens:
        return None
    
    # Check token expiration
    expires_in = tokens.value.get("expires_in")  # seconds until expiration
    created_at = tokens.created_at  # datetime of token creation
    current_time = datetime.now(timezone.utc)
    expiration_time = created_at + timedelta(seconds=expires_in)
    
    if current_time > expiration_time:
        # Token expired, clean up and return None
        await store.adelete((user_id, "tokens"), "data")
        return None

    return tokens.value

async def set_tokens(config: RunnableConfig, tokens: dict[str, Any]):
    """Store authentication tokens in the configuration store.
    
    Args:
        config: Runtime configuration containing thread and user identifiers
        tokens: Token dictionary to store
    """
    store = get_store()
    
    # Extract required identifiers from config
    thread_id = config.get("configurable", {}).get("thread_id")
    if not thread_id:
        return
        
    user_id = config.get("metadata", {}).get("owner")
    if not user_id:
        return
    
    # Store the tokens
    await store.aput((user_id, "tokens"), "data", tokens)

async def fetch_tokens(config: RunnableConfig) -> dict[str, Any]:
    """Fetch and refresh MCP tokens, obtaining new ones if needed.
    
    Args:
        config: Runtime configuration with authentication details
        
    Returns:
        Valid token dictionary, or None if unable to obtain tokens
    """
    # Try to get existing valid tokens first
    current_tokens = await get_tokens(config)
    if current_tokens:
        return current_tokens
    
    # Extract Supabase token for new token exchange
    supabase_token = config.get("configurable", {}).get("x-supabase-access-token")
    if not supabase_token:
        return None
    
    # Extract MCP configuration
    mcp_config = config.get("configurable", {}).get("mcp_config")
    if not mcp_config or not mcp_config.get("url"):
        return None
    
    # Exchange Supabase token for MCP tokens
    mcp_tokens = await get_mcp_access_token(supabase_token, mcp_config.get("url"))
    if not mcp_tokens:
        return None

    # Store the new tokens and return them
    await set_tokens(config, mcp_tokens)
    return mcp_tokens

def wrap_mcp_authenticate_tool(tool: StructuredTool) -> StructuredTool:
    """Wrap MCP tool with comprehensive authentication and error handling.
    
    Args:
        tool: The MCP structured tool to wrap
        
    Returns:
        Enhanced tool with authentication error handling
    """
    original_coroutine = tool.coroutine
    
    async def authentication_wrapper(**kwargs):
        """Enhanced coroutine with MCP error handling and user-friendly messages."""
        
        def _find_mcp_error_in_exception_chain(exc: BaseException) -> McpError | None:
            """Recursively search for MCP errors in exception chains."""
            if isinstance(exc, McpError):
                return exc
            
            # Handle ExceptionGroup (Python 3.11+) by checking attributes
            if hasattr(exc, 'exceptions'):
                for sub_exception in exc.exceptions:
                    if found_error := _find_mcp_error_in_exception_chain(sub_exception):
                        return found_error
            return None
        
        try:
            # Execute the original tool functionality
            return await original_coroutine(**kwargs)
            
        except BaseException as original_error:
            # Search for MCP-specific errors in the exception chain
            mcp_error = _find_mcp_error_in_exception_chain(original_error)
            if not mcp_error:
                # Not an MCP error, re-raise the original exception
                raise original_error
            
            # Handle MCP-specific error cases
            error_details = mcp_error.error
            error_code = getattr(error_details, "code", None)
            error_data = getattr(error_details, "data", None) or {}
            
            # Check for authentication/interaction required error
            if error_code == -32003:  # Interaction required error code
                message_payload = error_data.get("message", {})
                error_message = "Required interaction"
                
                # Extract user-friendly message if available
                if isinstance(message_payload, dict):
                    error_message = message_payload.get("text") or error_message
                
                # Append URL if provided for user reference
                if url := error_data.get("url"):
                    error_message = f"{error_message} {url}"
                
                raise ToolException(error_message) from original_error
            
            # For other MCP errors, re-raise the original
            raise original_error
    
    # Replace the tool's coroutine with our enhanced version
    tool.coroutine = authentication_wrapper
    return tool

async def load_mcp_tools(
    config: RunnableConfig,
    existing_tool_names: set[str],
) -> list[BaseTool]:
    """Load and configure MCP (Model Context Protocol) tools with authentication.
    
    Args:
        config: Runtime configuration containing MCP server details
        existing_tool_names: Set of tool names already in use to avoid conflicts
        
    Returns:
        List of configured MCP tools ready for use
    """
    configurable = Configuration.from_runnable_config(config)
    
    # Step 1: Handle authentication if required
    if configurable.mcp_config and configurable.mcp_config.auth_required:
        mcp_tokens = await fetch_tokens(config)
    else:
        mcp_tokens = None
    
    # Step 2: Validate configuration requirements
    config_valid = (
        configurable.mcp_config and 
        configurable.mcp_config.url and 
        configurable.mcp_config.tools and 
        (mcp_tokens or not configurable.mcp_config.auth_required)
    )
    
    if not config_valid:
        return []
    
    # Step 3: Set up MCP server connection
    server_url = configurable.mcp_config.url.rstrip("/") + "/mcp"
    
    # Configure authentication headers if tokens are available
    auth_headers = None
    if mcp_tokens:
        auth_headers = {"Authorization": f"Bearer {mcp_tokens['access_token']}"}
    
    mcp_server_config = {
        "server_1": {
            "url": server_url,
            "headers": auth_headers,
            "transport": "streamable_http"
        }
    }
    # TODO: When Multi-MCP Server support is merged in OAP, update this code
    
    # Step 4: Load tools from MCP server
    try:
        client = MultiServerMCPClient(mcp_server_config)
        available_mcp_tools = await client.get_tools()
    except Exception:
        # If MCP server connection fails, return empty list
        return []
    
    # Step 5: Filter and configure tools
    configured_tools = []
    for mcp_tool in available_mcp_tools:
        # Skip tools with conflicting names
        if mcp_tool.name in existing_tool_names:
            warnings.warn(
                f"MCP tool '{mcp_tool.name}' conflicts with existing tool name - skipping"
            )
            continue
        
        # Only include tools specified in configuration
        if mcp_tool.name not in set(configurable.mcp_config.tools):
            continue
        
        # Wrap tool with authentication handling and add to list
        enhanced_tool = wrap_mcp_authenticate_tool(mcp_tool)
        configured_tools.append(enhanced_tool)
    
    return configured_tools


##########################
# Tool Utils
##########################

async def get_search_tool(search_api: SearchAPI):
    """Configure and return search tools based on the specified API provider.
    
    Args:
        search_api: The search API provider to use (Anthropic, OpenAI, Tavily, or None)
        
    Returns:
        List of configured search tool objects for the specified provider
    """
    if search_api == SearchAPI.ANTHROPIC:
        # Anthropic's native web search with usage limits
        return [{
            "type": "web_search_20250305", 
            "name": "web_search", 
            "max_uses": 5
        }]
        
    elif search_api == SearchAPI.OPENAI:
        # OpenAI's web search preview functionality
        return [{"type": "web_search_preview"}]
        
    elif search_api == SearchAPI.TAVILY:
        # Configure Tavily search tool with metadata
        search_tool = tavily_search
        search_tool.metadata = {
            **(search_tool.metadata or {}), 
            "type": "search", 
            "name": "web_search"
        }
        return [search_tool]
        
    elif search_api == SearchAPI.NONE:
        # No search functionality configured
        return []
        
    # Default fallback for unknown search API types
    return []
    
async def get_all_tools(config: RunnableConfig):
    """Assemble complete toolkit including research, search, and MCP tools.
    
    Args:
        config: Runtime configuration specifying search API and MCP settings
        
    Returns:
        List of all configured and available tools for research operations
    """
    # Start with core research tools
    tools = [tool(ResearchComplete), think_tool]
    
    # Add configured search tools
    configurable = Configuration.from_runnable_config(config)
    search_api = SearchAPI(get_config_value(configurable.search_api))
    search_tools = await get_search_tool(search_api)
    tools.extend(search_tools)
    
    # Track existing tool names to prevent conflicts
    existing_tool_names = {
        tool.name if hasattr(tool, "name") else tool.get("name", "web_search") 
        for tool in tools
    }
    
    # Add MCP tools if configured
    mcp_tools = await load_mcp_tools(config, existing_tool_names)
    tools.extend(mcp_tools)
    
    return tools

def get_notes_from_tool_calls(messages: list[MessageLikeRepresentation]):
    """Extract notes from tool call messages."""
    return [tool_msg.content for tool_msg in filter_messages(messages, include_types="tool")]

##########################
# Model Provider Native Websearch Utils
##########################

def anthropic_websearch_called(response):
    """Detect if Anthropic's native web search was used in the response.
    
    Args:
        response: The response object from Anthropic's API
        
    Returns:
        True if web search was called, False otherwise
    """
    try:
        # Navigate through the response metadata structure
        usage = response.response_metadata.get("usage")
        if not usage:
            return False
        
        # Check for server-side tool usage information
        server_tool_use = usage.get("server_tool_use")
        if not server_tool_use:
            return False
        
        # Look for web search request count
        web_search_requests = server_tool_use.get("web_search_requests")
        if web_search_requests is None:
            return False
        
        # Return True if any web search requests were made
        return web_search_requests > 0
        
    except (AttributeError, TypeError):
        # Handle cases where response structure is unexpected
        return False

def openai_websearch_called(response):
    """Detect if OpenAI's web search functionality was used in the response.
    
    Args:
        response: The response object from OpenAI's API
        
    Returns:
        True if web search was called, False otherwise
    """
    # Check for tool outputs in the response metadata
    tool_outputs = response.additional_kwargs.get("tool_outputs")
    if not tool_outputs:
        return False
    
    # Look for web search calls in the tool outputs
    for tool_output in tool_outputs:
        if tool_output.get("type") == "web_search_call":
            return True
    
    return False


##########################
# Token Limit Exceeded Utils
##########################

def is_token_limit_exceeded(exception: Exception, model_name: str = None) -> bool:
    """Determine if an exception indicates a token/context limit was exceeded.
    
    Args:
        exception: The exception to analyze
        model_name: Optional model name to optimize provider detection
        
    Returns:
        True if the exception indicates a token limit was exceeded, False otherwise
    """
    error_str = str(exception).lower()
    
    # Step 1: Determine provider from model name if available
    provider = None
    if model_name:
        model_str = str(model_name).lower()
        if model_str.startswith('openai:'):
            provider = 'openai'
        elif model_str.startswith('anthropic:'):
            provider = 'anthropic'
        elif model_str.startswith('gemini:') or model_str.startswith('google:'):
            provider = 'gemini'
    
    # Step 2: Check provider-specific token limit patterns
    if provider == 'openai':
        return _check_openai_token_limit(exception, error_str)
    elif provider == 'anthropic':
        return _check_anthropic_token_limit(exception, error_str)
    elif provider == 'gemini':
        return _check_gemini_token_limit(exception, error_str)
    
    # Step 3: If provider unknown, check all providers
    return (
        _check_openai_token_limit(exception, error_str) or
        _check_anthropic_token_limit(exception, error_str) or
        _check_gemini_token_limit(exception, error_str)
    )

def _check_openai_token_limit(exception: Exception, error_str: str) -> bool:
    """Check if exception indicates OpenAI token limit exceeded."""
    # Analyze exception metadata
    exception_type = str(type(exception))
    class_name = exception.__class__.__name__
    module_name = getattr(exception.__class__, '__module__', '')
    
    # Check if this is an OpenAI exception
    is_openai_exception = (
        'openai' in exception_type.lower() or 
        'openai' in module_name.lower()
    )
    
    # Check for typical OpenAI token limit error types
    is_request_error = class_name in ['BadRequestError', 'InvalidRequestError']
    
    if is_openai_exception and is_request_error:
        # Look for token-related keywords in error message
        token_keywords = ['token', 'context', 'length', 'maximum context', 'reduce']
        if any(keyword in error_str for keyword in token_keywords):
            return True
    
    # Check for specific OpenAI error codes
    if hasattr(exception, 'code') and hasattr(exception, 'type'):
        error_code = getattr(exception, 'code', '')
        error_type = getattr(exception, 'type', '')
        
        if (error_code == 'context_length_exceeded' or
            error_type == 'invalid_request_error'):
            return True
    
    return False

def _check_anthropic_token_limit(exception: Exception, error_str: str) -> bool:
    """Check if exception indicates Anthropic token limit exceeded."""
    # Analyze exception metadata
    exception_type = str(type(exception))
    class_name = exception.__class__.__name__
    module_name = getattr(exception.__class__, '__module__', '')
    
    # Check if this is an Anthropic exception
    is_anthropic_exception = (
        'anthropic' in exception_type.lower() or 
        'anthropic' in module_name.lower()
    )
    
    # Check for Anthropic-specific error patterns
    is_bad_request = class_name == 'BadRequestError'
    
    if is_anthropic_exception and is_bad_request:
        # Anthropic uses specific error messages for token limits
        if 'prompt is too long' in error_str:
            return True
    
    return False

def _check_gemini_token_limit(exception: Exception, error_str: str) -> bool:
    """Check if exception indicates Google/Gemini token limit exceeded."""
    # Analyze exception metadata
    exception_type = str(type(exception))
    class_name = exception.__class__.__name__
    module_name = getattr(exception.__class__, '__module__', '')
    
    # Check if this is a Google/Gemini exception
    is_google_exception = (
        'google' in exception_type.lower() or 
        'google' in module_name.lower()
    )
    
    # Check for Google-specific resource exhaustion errors
    is_resource_exhausted = class_name in [
        'ResourceExhausted', 
        'GoogleGenerativeAIFetchError'
    ]
    
    if is_google_exception and is_resource_exhausted:
        return True
    
    # Check for specific Google API resource exhaustion patterns
    if 'google.api_core.exceptions.resourceexhausted' in exception_type.lower():
        return True
    
    return False

# NOTE: This may be out of date or not applicable to your models. Please update this as needed.
MODEL_TOKEN_LIMITS = {
    "openai:gpt-4.1-mini": 1047576,
    "openai:gpt-4.1-nano": 1047576,
    "openai:gpt-4.1": 1047576,
    "openai:gpt-4o-mini": 128000,
    "openai:gpt-4o": 128000,
    "openai:o4-mini": 200000,
    "openai:o3-mini": 200000,
    "openai:o3": 200000,
    "openai:o3-pro": 200000,
    "openai:o1": 200000,
    "openai:o1-pro": 200000,
    "anthropic:claude-opus-4": 200000,
    "anthropic:claude-sonnet-4": 200000,
    "anthropic:claude-3-7-sonnet": 200000,
    "anthropic:claude-3-5-sonnet": 200000,
    "anthropic:claude-3-5-haiku": 200000,
    "google:gemini-1.5-pro": 2097152,
    "google:gemini-1.5-flash": 1048576,
    "google:gemini-pro": 32768,
    "cohere:command-r-plus": 128000,
    "cohere:command-r": 128000,
    "cohere:command-light": 4096,
    "cohere:command": 4096,
    "mistral:mistral-large": 32768,
    "mistral:mistral-medium": 32768,
    "mistral:mistral-small": 32768,
    "mistral:mistral-7b-instruct": 32768,
    "ollama:codellama": 16384,
    "ollama:llama2:70b": 4096,
    "ollama:llama2:13b": 4096,
    "ollama:llama2": 4096,
    "ollama:mistral": 32768,
    "bedrock:us.amazon.nova-premier-v1:0": 1000000,
    "bedrock:us.amazon.nova-pro-v1:0": 300000,
    "bedrock:us.amazon.nova-lite-v1:0": 300000,
    "bedrock:us.amazon.nova-micro-v1:0": 128000,
    "bedrock:us.anthropic.claude-3-7-sonnet-20250219-v1:0": 200000,
    "bedrock:us.anthropic.claude-sonnet-4-20250514-v1:0": 200000,
    "bedrock:us.anthropic.claude-opus-4-20250514-v1:0": 200000,
    "anthropic.claude-opus-4-1-20250805-v1:0": 200000,
}

def get_model_token_limit(model_string):
    """Look up the token limit for a specific model.
    
    Args:
        model_string: The model identifier string to look up
        
    Returns:
        Token limit as integer if found, None if model not in lookup table
    """
    # Search through known model token limits
    for model_key, token_limit in MODEL_TOKEN_LIMITS.items():
        if model_key in model_string:
            return token_limit
    
    # Model not found in lookup table
    return None

def remove_up_to_last_ai_message(messages: list[MessageLikeRepresentation]) -> list[MessageLikeRepresentation]:
    """Truncate message history by removing up to the last AI message.
    
    This is useful for handling token limit exceeded errors by removing recent context.
    
    Args:
        messages: List of message objects to truncate
        
    Returns:
        Truncated message list up to (but not including) the last AI message
    """
    # Search backwards through messages to find the last AI message
    for i in range(len(messages) - 1, -1, -1):
        if isinstance(messages[i], AIMessage):
            # Return everything up to (but not including) the last AI message
            return messages[:i]
    
    # No AI messages found, return original list
    return messages

##########################
# Misc Utils
##########################

def get_today_str() -> str:
    """Get current date formatted for display in prompts and outputs.
    
    Returns:
        Human-readable date string in format like 'Mon Jan 15, 2024'
    """
    now = datetime.now()
    return f"{now:%a} {now:%b} {now.day}, {now:%Y}"

def get_config_value(value):
    """Extract value from configuration, handling enums and None values."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    elif isinstance(value, dict):
        return value
    else:
        return value.value

def get_api_key_for_model(model_name: str, config: RunnableConfig):
    """Get API key for a specific model from environment or config."""
    should_get_from_config = os.getenv("GET_API_KEYS_FROM_CONFIG", "false")
    model_name = model_name.lower()
    if should_get_from_config.lower() == "true":
        api_keys = config.get("configurable", {}).get("apiKeys", {})
        if not api_keys:
            return None
        if model_name.startswith("openai:"):
            return api_keys.get("OPENAI_API_KEY")
        elif model_name.startswith("anthropic:"):
            return api_keys.get("ANTHROPIC_API_KEY")
        elif model_name.startswith("google"):
            return api_keys.get("GOOGLE_API_KEY")
        return None
    else:
        if model_name.startswith("openai:"): 
            return os.getenv("OPENAI_API_KEY")
        elif model_name.startswith("anthropic:"):
            return os.getenv("ANTHROPIC_API_KEY")
        elif model_name.startswith("google"):
            return os.getenv("GOOGLE_API_KEY")
        return None

def get_tavily_api_key(config: RunnableConfig):
    """Get Tavily API key from environment or config."""
    should_get_from_config = os.getenv("GET_API_KEYS_FROM_CONFIG", "false")
    if should_get_from_config.lower() == "true":
        api_keys = config.get("configurable", {}).get("apiKeys", {})
        if not api_keys:
            return None
        return api_keys.get("TAVILY_API_KEY")
    else:
        return os.getenv("TAVILY_API_KEY")
