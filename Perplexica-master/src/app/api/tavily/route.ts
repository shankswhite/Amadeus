/**
 * Enhanced Tavily API Compatible Endpoint
 * 
 * Fully compatible with Tavily API + Extended features
 * - Time range support (date_from/date_to/days)
 * - Configurable search engines
 * - Custom language support
 * - LLM model selection
 * - No hardcoded parameters
 * 
 * Tavily API Reference: https://docs.tavily.com/docs/tavily-api/rest_api
 */

import { searchSearxng } from '@/lib/searxng';
import ModelRegistry from '@/lib/models/registry';
import { getDocumentsFromLinks } from '@/lib/utils/documents';

// Configuration (can be overridden by environment variables)
const CONFIG = {
  MAX_RESULTS: parseInt(process.env.TAVILY_MAX_RESULTS || '50'),
  DEFAULT_RESULTS: 10,
  DEFAULT_LANGUAGE: process.env.TAVILY_DEFAULT_LANGUAGE || 'en',
  DEFAULT_SEARCH_DEPTH: 'basic' as 'basic' | 'advanced',
  ANSWER_CONTEXT_SIZE: parseInt(process.env.TAVILY_ANSWER_CONTEXT || '5'),
  DEFAULT_ENGINES: ['google', 'bing', 'duckduckgo'],
  TIMEOUT: parseInt(process.env.TAVILY_TIMEOUT || '60'),
};

interface TavilySearchRequest {
  // === Core Parameters ===
  query: string;
  max_results?: number;
  search_depth?: 'basic' | 'advanced';
  
  // === Content Control ===
  include_answer?: boolean;
  include_raw_content?: boolean;
  include_images?: boolean;
  
  // === Domain Filtering ===
  include_domains?: string[];
  exclude_domains?: string[];
  
  // === Time Range (New!) ===
  date_from?: string;              // Start date YYYY-MM-DD
  date_to?: string;                // End date YYYY-MM-DD
  days?: number;                   // Relative days (alternative to date_from/to)
  time_range?: 'day' | 'week' | 'month' | 'year' | 'all'; // SearXNG preset
  
  // === Search Control (New!) ===
  language?: string;               // Search language (default: 'en')
  engines?: string[];              // Custom search engines
  safesearch?: 0 | 1 | 2;         // Safe search level (0=off, 1=moderate, 2=strict)
  categories?: string[];           // Search categories
  
  // === LLM Control (New!) ===
  llm_provider?: string;           // LLM provider for answer generation
  llm_model?: string;              // Specific LLM model
  answer_max_tokens?: number;      // Max tokens for answer
  answer_temperature?: number;     // Temperature for answer generation
  answer_context_size?: number;    // Number of results to use for context
  
  // === Performance (New!) ===
  timeout?: number;                // Request timeout in seconds
  api_key?: string;                // API key (optional authentication)
}

interface TavilySearchResult {
  title: string;
  url: string;
  content: string;
  raw_content?: string;
  score: number;
  published_date?: string;
  img_src?: string;  // Image URL if available
}

interface TavilySearchResponse {
  query: string;
  answer?: string;
  follow_up_questions?: string[];
  images?: string[];
  results: TavilySearchResult[];
  response_time: number;
  // Extended metadata
  metadata?: {
    time_range?: string;
    language: string;
    engines_used: string[];
    llm_used?: string;
  };
}

/**
 * Calculate date range from various time parameters
 */
function calculateTimeRange(
  dateFrom?: string,
  dateTo?: string,
  days?: number,
  timeRange?: string
): { queryModifier: string; searxngTimeRange: string } {
  let queryModifier = '';
  let searxngTimeRange = '';

  // Priority 1: Explicit date_from/date_to
  if (dateFrom || dateTo) {
    if (dateFrom) {
      queryModifier += ` after:${dateFrom}`;
    }
    if (dateTo) {
      queryModifier += ` before:${dateTo}`;
    }
  }
  // Priority 2: Relative days
  else if (days && days > 0) {
    const fromDate = new Date();
    fromDate.setDate(fromDate.getDate() - days);
    const dateStr = fromDate.toISOString().split('T')[0];
    queryModifier = ` after:${dateStr}`;
  }
  // Priority 3: SearXNG time_range
  else if (timeRange && timeRange !== 'all') {
    searxngTimeRange = timeRange;
  }

  return { queryModifier, searxngTimeRange };
}

/**
 * Main POST handler
 */
export const POST = async (req: Request) => {
  const startTime = Date.now();
  
  try {
    const body: TavilySearchRequest = await req.json();

    // Validate required parameters
    if (!body.query) {
      return Response.json(
        { 
          error: 'Missing required parameter: query',
          message: 'The query parameter is required'
        },
        { status: 400 }
      );
    }

    // Extract and validate parameters with defaults
    const searchDepth = body.search_depth || CONFIG.DEFAULT_SEARCH_DEPTH;
    const includeAnswer = body.include_answer ?? false;
    const includeRawContent = body.include_raw_content ?? false;
    const maxResults = Math.min(
      body.max_results || CONFIG.DEFAULT_RESULTS, 
      CONFIG.MAX_RESULTS
    );
    const includeImages = body.include_images ?? false;
    const language = body.language || CONFIG.DEFAULT_LANGUAGE;
    const engines = body.engines || CONFIG.DEFAULT_ENGINES;
    const safesearch = body.safesearch ?? 2;
    const timeout = (body.timeout || CONFIG.TIMEOUT) * 1000; // Convert to ms
    const answerContextSize = body.answer_context_size || CONFIG.ANSWER_CONTEXT_SIZE;

    // Calculate time range
    const { queryModifier, searxngTimeRange } = calculateTimeRange(
      body.date_from,
      body.date_to,
      body.days,
      body.time_range
    );

    // Build search query with domain restrictions and time range
    let searchQuery = body.query + queryModifier;
    
    if (body.include_domains && body.include_domains.length > 0) {
      const siteQuery = body.include_domains
        .map(domain => `site:${domain}`)
        .join(' OR ');
      searchQuery = `${searchQuery} (${siteQuery})`;
    }

    // Log search parameters (for debugging)
    console.log('[Tavily API] Search params:', {
      query: searchQuery,
      language,
      engines,
      time_range: searxngTimeRange,
      safesearch,
      max_results: maxResults
    });

    // Perform search using SearXNG with custom parameters
    const searchResults = await searchSearxng(searchQuery, {
      language,
      engines,
      time_range: searxngTimeRange,
      safesearch: safesearch.toString(),
      categories: body.categories || ['general'],
    });

    // Filter results
    let filteredResults = searchResults.results || [];
    
    // Apply exclude domains filter
    if (body.exclude_domains && body.exclude_domains.length > 0) {
      filteredResults = filteredResults.filter(result => {
        try {
          const url = new URL(result.url);
          return !body.exclude_domains!.some(domain => 
            url.hostname.includes(domain)
          );
        } catch {
          return true; // Keep if URL parsing fails
        }
      });
    }

    // Limit results
    filteredResults = filteredResults.slice(0, maxResults);

    // Extract URLs for content fetching
    const urls = filteredResults.map(r => r.url);

    // Fetch full content if requested (with timeout)
    let documents: any[] = [];
    if (includeRawContent && urls.length > 0) {
      try {
        const fetchPromise = getDocumentsFromLinks({ links: urls });
        const timeoutPromise = new Promise((_, reject) =>
          setTimeout(() => reject(new Error('Content fetch timeout')), timeout)
        );
        documents = await Promise.race([fetchPromise, timeoutPromise]) as any[];
      } catch (error) {
        console.error('[Tavily API] Error fetching documents:', error);
        // Continue without raw content
      }
    }

    // Build Tavily-compatible results
    const results: TavilySearchResult[] = filteredResults.map((result, index) => {
      // Combine all document chunks for this URL to get full content
      const relatedDocs = documents.filter(d => d.metadata.url === result.url);
      const fullContent = relatedDocs.length > 0
        ? relatedDocs.map(d => d.pageContent).join('\n\n')
        : undefined;
      
      return {
        title: result.title || '',
        url: result.url,
        content: result.content || result.title || '',
        raw_content: includeRawContent && fullContent ? fullContent : undefined,
        score: result.score || (1 - index * 0.05), // Generate relevance score
        published_date: result.publishedDate,
        img_src: result.img_src,
      };
    });

    // Generate answer using LLM if requested
    let answer: string | undefined;
    let followUpQuestions: string[] | undefined;
    let llmUsed: string | undefined;

    if (includeAnswer && searchDepth === 'advanced' && results.length > 0) {
      try {
        // Only generate answer if LLM provider and model are explicitly provided
        if (!body.llm_provider || !body.llm_model) {
          console.warn('[Tavily API] Answer generation requested but no LLM provider/model specified. Skipping answer generation.');
        } else {
          const registry = new ModelRegistry();
          let llm;
          
          try {
            llm = await registry.loadChatModel(body.llm_provider, body.llm_model);
            llmUsed = `${body.llm_provider}/${body.llm_model}`;
          } catch (error) {
            console.error('[Tavily API] Failed to load LLM:', error);
            llm = null;
          }

          if (llm) {
          // Create context from search results
          const contextResults = results.slice(0, answerContextSize);
          const context = contextResults
            .map((r, i) => `[${i + 1}] ${r.title}\n${r.content}`)
            .join('\n\n');

          // Configure LLM
          if (body.answer_temperature !== undefined) {
            (llm as any).temperature = body.answer_temperature;
          }

          // Generate answer
          const answerPrompt = `Based on the following search results, provide a concise and accurate answer to the question: "${body.query}"

Search Results:
${context}

Provide a clear, factual answer based solely on the information above. If the information is insufficient, say so. ${body.answer_max_tokens ? `Keep the answer under ${body.answer_max_tokens} tokens.` : ''}`;

          const response = await llm.invoke(answerPrompt);
          answer = response.content.toString();

          // Generate follow-up questions
          const followUpPrompt = `Based on the question "${body.query}" and the answer provided, suggest 3 relevant follow-up questions a user might ask. Return only the questions, one per line, without numbering.`;
          
          const followUpResponse = await llm.invoke(followUpPrompt);
          followUpQuestions = followUpResponse.content
            .toString()
            .split('\n')
            .filter(q => q.trim().length > 0)
            .slice(0, 3);
          }
        }
      } catch (error) {
        console.error('[Tavily API] Error generating answer:', error);
        // Continue without answer if LLM fails
      }
    }

    // Extract images if requested
    let images: string[] | undefined;
    if (includeImages) {
      // Extract image URLs from search results
      images = results
        .map(r => r.img_src)
        .filter((img): img is string => typeof img === 'string' && img.length > 0)
        .slice(0, 10);
    }

    // Build response with metadata
    const response: TavilySearchResponse = {
      query: body.query,
      answer,
      follow_up_questions: followUpQuestions,
      images,
      results,
      response_time: (Date.now() - startTime) / 1000,
      metadata: {
        time_range: body.date_from || body.date_to 
          ? `${body.date_from || 'all'} to ${body.date_to || 'now'}`
          : body.days 
          ? `last ${body.days} days`
          : searxngTimeRange || 'all',
        language,
        engines_used: engines,
        llm_used: llmUsed,
      },
    };

    return Response.json(response, { 
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      }
    });

  } catch (err: any) {
    console.error(`[Tavily API] Error: ${err.message}`);
    console.error(err.stack);
    
    return Response.json(
      { 
        error: 'Internal server error',
        message: err.message,
        response_time: (Date.now() - startTime) / 1000,
      },
      { status: 500 }
    );
  }
};

/**
 * GET handler - supports query parameters
 */
export const GET = async (req: Request) => {
  try {
    const url = new URL(req.url);
    const query = url.searchParams.get('query');
    
    if (!query) {
      return Response.json(
        { 
          error: 'Missing required parameter: query',
          message: 'The query parameter is required'
        },
        { status: 400 }
      );
    }

    // Build request body from query parameters
    const body: TavilySearchRequest = {
      query,
      search_depth: (url.searchParams.get('search_depth') as 'basic' | 'advanced') || 'basic',
      include_answer: url.searchParams.get('include_answer') === 'true',
      include_raw_content: url.searchParams.get('include_raw_content') === 'true',
      include_images: url.searchParams.get('include_images') === 'true',
      max_results: parseInt(url.searchParams.get('max_results') || '10'),
      
      // Time parameters
      date_from: url.searchParams.get('date_from') || undefined,
      date_to: url.searchParams.get('date_to') || undefined,
      days: url.searchParams.get('days') ? parseInt(url.searchParams.get('days')!) : undefined,
      time_range: (url.searchParams.get('time_range') as any) || undefined,
      
      // Search control
      language: url.searchParams.get('language') || undefined,
      engines: url.searchParams.get('engines')?.split(',') || undefined,
    };

    // Convert to POST request
    return POST(
      new Request(req.url, {
        method: 'POST',
        body: JSON.stringify(body),
        headers: { 'Content-Type': 'application/json' },
      })
    );

  } catch (err: any) {
    console.error(`[Tavily API GET] Error: ${err.message}`);
    
    return Response.json(
      { 
        error: 'Internal server error',
        message: err.message,
      },
      { status: 500 }
    );
  }
};
