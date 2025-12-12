"""
LangGraph State Definition
"""
from typing import TypedDict, List, Optional, Any
from dataclasses import dataclass, field


class WorkflowState(TypedDict, total=False):
    """State that flows through the LangGraph workflow"""
    
    # === Input ===
    question: str                    # User's question
    title: str                       # Game title filter (e.g., "bo6_wz2")
    season: str                      # Season filter (e.g., "Season 3")
    week: int                        # Week number filter
    enable_rag: bool                 # Whether to use RAG
    
    # === Node 1 Output: RAG Analysis ===
    analysis: str                    # LLM's analysis of the question
    key_metrics: List[str]           # Identified key metrics
    key_segments: List[str]          # Identified key segments
    rag_references: List[dict]       # Retrieved document references
    rag_context: str                 # Combined context from RAG
    
    # === Node 2 Output: Chart Decision ===
    chart_type: str                  # "bar", "line", "pie", etc.
    chart_title: str                 # Chart title
    x_axis: str                      # X-axis field
    y_axis: str                      # Y-axis field
    chart_filter: str                # SQL WHERE clause for chart data
    
    # === Node 3 Output: SQL & ECharts ===
    sql_query: str                   # Generated SQL query
    sql_result: List[dict]           # Query results
    echarts_option: dict             # ECharts configuration
    python_code: str                 # Generated Python visualization code
    
    # === Node 4 Output: Final Explanation ===
    final_explanation: str           # Combined explanation
    references: List[str]            # Citation references
    
    # === Error Handling ===
    error: Optional[str]             # Error message if any


@dataclass
class RAGDocument:
    """Retrieved document from RAG"""
    title: str
    season: str
    week: int
    content: str
    source: str  # "report_origin" or "report_deep_research"
    similarity: float


@dataclass
class ChartDecision:
    """Chart decision from Node 2"""
    chart_type: str
    title: str
    x_axis: str
    y_axis: str
    filter_condition: str
    reasoning: str

