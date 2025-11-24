"""
Custom SearCrawl Client - Tavily API Compatible

This client provides a drop-in replacement for AsyncTavilyClient/AsyncPerplexicaClient,
allowing Open Deep Research to use SearCrawl as the search+crawling backend.
"""
import os
import httpx
from typing import Any, Dict, List, Literal, Optional


class AsyncSearCrawlClient:
    """
    Async SearCrawl client that mimics AsyncTavilyClient interface.
    
    SearCrawl combines search AND crawling in one API call, eliminating
    the need for separate Jina Reader or Crawl4AI integration.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize the SearCrawl client.
        
        Args:
            api_key: API key (optional, currently not used by SearCrawl)
            base_url: Base URL for SearCrawl API (defaults to env var or service URL)
        """
        self.api_key = api_key
        
        # Determine base URL from parameter, env var, or default
        if base_url:
            self.base_url = base_url.rstrip('/')
        else:
            self.base_url = os.getenv(
                "SEARCRAWL_API_URL", 
                "http://searcrawl-service:3000"
            ).rstrip('/')
        
        # Create HTTP client with generous timeout for content fetching + crawling
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=10.0,
                read=180.0,      # 3 minutes for search + crawling
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
        # Time range parameters (not yet supported by SearCrawl)
        time_range: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        days: Optional[int] = None,
        # Domain filtering
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        # Search control
        language: str = "en",
        engines: Optional[List[str]] = None,
        safesearch: Optional[str] = None,
        search_depth: str = "basic",
        # Content control
        include_answer: bool = False,
        include_images: bool = False,
        # Performance control
        timeout: Optional[int] = None,
        api_key: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a search query using SearCrawl (search + crawl in one call).
        
        SearCrawl automatically:
        1. Searches for relevant URLs
        2. Crawls each URL to extract full content
        3. Returns structured results with complete webpage content
        
        This eliminates the need for separate Jina Reader or Crawl4AI calls!
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return (default: 5)
            include_raw_content: Whether to include full webpage content (default: True)
            topic: Topic category - "general", "news", or "finance" (default: "general")
            
            # Other parameters are accepted for compatibility but may not be fully supported yet
            
        Returns:
            Dict containing search results in Tavily-compatible format:
            {
                "query": str,
                "results": [
                    {
                        "title": str,
                        "url": str,
                        "content": str,          # Summary (~500 chars)
                        "raw_content": str,       # Full webpage content (5000+ chars) ✅
                        "score": float,
                    },
                    ...
                ],
                "answer": str (optional, if include_answer=True),
                "images": [] (optional, if include_images=True),
                "follow_up_questions": [] (optional)
            }
            
        Raises:
            httpx.HTTPStatusError: If the API returns an error status
            httpx.TimeoutException: If the request times out
        """
        # Build request payload for SearCrawl API
        payload = {
            "query": query,
            "limit": max_results,  # SearCrawl uses 'limit' instead of 'max_results'
            "include_raw_content": include_raw_content,
            "topic": topic,
        }
        
        # Add supported optional parameters
        if timeout:
            payload["timeout"] = timeout
        
        try:
            # Send POST request to SearCrawl
            response = await self.client.post(
                f"{self.base_url}/search",  # SearCrawl endpoint: /search
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            # Raise exception for error status codes
            response.raise_for_status()
            
            # Parse JSON response
            result = response.json()
            
            # Ensure Tavily-compatible structure
            if "results" not in result:
                result["results"] = []
            if "query" not in result:
                result["query"] = query
            if "answer" not in result:
                result["answer"] = None
            if "images" not in result:
                result["images"] = []
            if "follow_up_questions" not in result:
                result["follow_up_questions"] = None
                
            return result
            
        except httpx.TimeoutException as e:
            # Handle timeout errors gracefully
            return {
                "query": query,
                "results": [],
                "answer": None,
                "images": [],
                "follow_up_questions": None,
                "error": f"Request timeout: {str(e)}",
                "response_time": 180.0
            }
        except httpx.HTTPStatusError as e:
            # Handle HTTP errors gracefully
            return {
                "query": query,
                "results": [],
                "answer": None,
                "images": [],
                "follow_up_questions": None,
                "error": f"HTTP error {e.response.status_code}: {e.response.text}",
                "response_time": 0.0
            }
        except Exception as e:
            # Handle any other unexpected errors
            return {
                "query": query,
                "results": [],
                "answer": None,
                "images": [],
                "follow_up_questions": None,
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
def get_searcrawl_client(api_key: Optional[str] = None, base_url: Optional[str] = None) -> AsyncSearCrawlClient:
    """
    Create and return a SearCrawl client instance.
    
    Args:
        api_key: Optional API key
        base_url: Optional base URL for SearCrawl API
        
    Returns:
        AsyncSearCrawlClient instance
    """
    return AsyncSearCrawlClient(api_key=api_key, base_url=base_url)

