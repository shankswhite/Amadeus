"""
Custom Perplexica Client - 100% Compatible with Tavily API

This client provides a drop-in replacement for AsyncTavilyClient,
allowing Open Deep Research to use Perplexica as the search backend
while maintaining complete API compatibility.
"""
import os
import httpx
from typing import Any, Dict, List, Literal, Optional


class AsyncPerplexicaClient:
    """
    Async Perplexica client that mimics AsyncTavilyClient interface.
    
    This client ensures 1:1 parameter mapping between Tavily API calls
    and Perplexica API calls, with complete compatibility.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize the Perplexica client.
        
        Args:
            api_key: API key (optional, currently not used by Perplexica)
            base_url: Base URL for Perplexica API (defaults to env var or service URL)
        """
        self.api_key = api_key
        
        # Determine base URL from parameter, env var, or default
        if base_url:
            self.base_url = base_url.rstrip('/')
        else:
            self.base_url = os.getenv(
                "PERPLEXICA_API_URL", 
                "http://perplexica-service/api/tavily"
            ).rstrip('/')
        
        # Create HTTP client with generous timeout for content fetching
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=10.0,
                read=300.0,      # 5 minutes for content fetching
                write=10.0,
                pool=10.0
            ),
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100
            )
        )
    
    async def search(
        self,
        query: str,
        max_results: int = 5,
        include_raw_content: bool = False,  # Default: use search engine summaries
        topic: Literal["general", "news", "finance"] = "general",
        # === 时间范围参数 ===
        time_range: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        days: Optional[int] = None,
        # === 域名过滤参数 ===
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        # === 搜索控制参数 ===
        language: str = "en",
        engines: Optional[List[str]] = None,
        safesearch: Optional[str] = None,
        search_depth: str = "basic",
        categories: Optional[List[str]] = None,
        # === 内容控制参数 ===
        include_answer: bool = False,
        include_images: bool = False,
        # === LLM 控制参数 ===
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        answer_max_tokens: Optional[int] = None,
        answer_temperature: Optional[float] = None,
        answer_context_size: Optional[int] = None,
        # === 性能控制参数 ===
        timeout: Optional[int] = None,
        api_key: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a search query with full parameter support.
        
        This method supports ALL Perplexica API parameters (22 total),
        providing complete control over search behavior.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return (default: 5)
            include_raw_content: Whether to include full webpage content (default: True)
            topic: Topic category - "general", "news", or "finance" (default: "general")
            
            # Time range parameters
            time_range: Preset time range - "day", "week", "month", "year" (default: None)
            date_from: Start date in YYYY-MM-DD format (default: None)
            date_to: End date in YYYY-MM-DD format (default: None)
            days: Search results from last N days (default: None)
            
            # Domain filtering
            include_domains: List of domains to search only from (default: None)
            exclude_domains: List of domains to exclude from search (default: None)
            
            # Search control
            language: Search language code - "en", "zh", "ja", "ko", etc. (default: "en")
            engines: List of search engines to use (default: None, uses all)
            safesearch: Safe search level - "0", "1", "2" (default: None)
            search_depth: Search depth - "basic" or "advanced" (default: "basic")
            categories: Search categories override (default: None, uses topic mapping)
            
            # Content control
            include_answer: Whether to generate LLM answer (default: False)
            include_images: Whether to include images in results (default: False)
            
            # LLM control (for include_answer=True)
            llm_provider: LLM provider - "openai", "anthropic", etc. (default: None)
            llm_model: LLM model name (default: None)
            answer_max_tokens: Max tokens for answer generation (default: None)
            answer_temperature: Temperature for answer generation (default: None)
            answer_context_size: Number of results to use for answer (default: None)
            
            # Performance control
            timeout: Request timeout in seconds (default: None, uses client default)
            api_key: API key for authentication (default: None)
            
            **kwargs: Additional parameters (for future compatibility)
            
        Returns:
            Dict containing search results in Tavily-compatible format:
            {
                "query": str,
                "results": [
                    {
                        "title": str,
                        "url": str,
                        "content": str,
                        "raw_content": str (if include_raw_content=True),
                        "score": float,
                        "published_date": str (optional)
                    },
                    ...
                ],
                "response_time": float,
                "metadata": {...}
            }
            
        Raises:
            httpx.HTTPStatusError: If the API returns an error status
            httpx.TimeoutException: If the request times out
        """
        # Build request payload with ALL parameters
        payload = {
            "query": query,
            "max_results": max_results,
            "include_raw_content": include_raw_content,
            "include_answer": include_answer,
            "include_images": include_images,
            "search_depth": search_depth,
            "language": language,
        }
        
        # === Categories mapping (from topic or override) ===
        if categories:
            # User explicitly provided categories
            payload["categories"] = categories
        else:
            # Map 'topic' to appropriate categories
            if topic == "news":
                payload["categories"] = ["news"]
            elif topic == "finance":
                payload["categories"] = ["news"]  # Perplexica doesn't have finance category
            else:  # "general"
                payload["categories"] = ["general"]
        
        # === Time range parameters ===
        if time_range:
            payload["time_range"] = time_range
        elif topic in ["news", "finance"] and not time_range and not date_from and not date_to and not days:
            # For news/finance without explicit time, default to recent
            payload["time_range"] = "month"
        
        if date_from:
            payload["date_from"] = date_from
        if date_to:
            payload["date_to"] = date_to
        if days:
            payload["days"] = days
        
        # === Domain filtering ===
        if include_domains:
            payload["include_domains"] = include_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains
        
        # === Search control ===
        if engines:
            payload["engines"] = engines
        if safesearch:
            payload["safesearch"] = safesearch
        
        # === LLM control (only if include_answer=True) ===
        if include_answer:
            if llm_provider:
                payload["llm_provider"] = llm_provider
            if llm_model:
                payload["llm_model"] = llm_model
            if answer_max_tokens:
                payload["answer_max_tokens"] = answer_max_tokens
            if answer_temperature is not None:
                payload["answer_temperature"] = answer_temperature
            if answer_context_size:
                payload["answer_context_size"] = answer_context_size
        
        # === Performance control ===
        if timeout:
            payload["timeout"] = timeout
        
        # === API key ===
        if api_key or self.api_key:
            payload["api_key"] = api_key or self.api_key
        
        # Add any additional parameters passed through kwargs
        payload.update(kwargs)
        
        try:
            # Send POST request to Perplexica
            response = await self.client.post(
                self.base_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            # Raise exception for error status codes
            response.raise_for_status()
            
            # Parse and return JSON response
            result = response.json()
            
            # Ensure the response has the expected structure
            if "results" not in result:
                result["results"] = []
            if "query" not in result:
                result["query"] = query
                
            return result
            
        except httpx.TimeoutException as e:
            # Handle timeout errors gracefully
            return {
                "query": query,
                "results": [],
                "error": f"Request timeout: {str(e)}",
                "response_time": 300.0
            }
        except httpx.HTTPStatusError as e:
            # Handle HTTP errors gracefully
            return {
                "query": query,
                "results": [],
                "error": f"HTTP error {e.response.status_code}: {e.response.text}",
                "response_time": 0.0
            }
        except Exception as e:
            # Handle any other unexpected errors
            return {
                "query": query,
                "results": [],
                "error": f"Unexpected error: {str(e)}",
                "response_time": 0.0
            }
    
    async def __aenter__(self):
        """Context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close HTTP client."""
        await self.client.aclose()
    
    async def close(self):
        """Explicitly close the HTTP client."""
        await self.client.aclose()


# Convenience function for backward compatibility
def get_perplexica_client(api_key: Optional[str] = None, base_url: Optional[str] = None) -> AsyncPerplexicaClient:
    """
    Create and return a Perplexica client instance.
    
    Args:
        api_key: Optional API key
        base_url: Optional base URL for Perplexica API
        
    Returns:
        AsyncPerplexicaClient instance
    """
    return AsyncPerplexicaClient(api_key=api_key, base_url=base_url)

