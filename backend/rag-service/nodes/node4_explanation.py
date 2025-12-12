"""
Node 4: Final Explanation
- Combine analysis, chart data, and RAG context
- Generate comprehensive explanation
"""
from typing import Dict, Any, List
from state import WorkflowState
from utils.llm import chat_completion


def explanation_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Node 4: Final Explanation
    
    Input: All previous node outputs
    Output: final_explanation, references
    """
    print("[Node 4] Generating final explanation...")
    
    question = state.get("question", "")
    analysis = state.get("analysis", "")
    chart_title = state.get("chart_title", "")
    chart_type = state.get("chart_type", "")
    sql_result = state.get("sql_result", [])
    rag_references = state.get("rag_references", [])
    enable_rag = state.get("enable_rag", True)
    title = state.get("title", "")
    season = state.get("season", "")
    week = state.get("week", 0)
    
    # Format chart data summary
    chart_summary = format_chart_summary(sql_result, chart_type)
    
    # Format references only if RAG is enabled
    references = format_references(rag_references) if enable_rag and rag_references else ""
    
    # Generate final explanation
    if enable_rag:
        system_prompt = """You are a game analytics expert presenting insights to stakeholders.

Create a clear, comprehensive explanation that:
1. Directly answers the user's question
2. Explains the chart visualization
3. Cites specific data points from metrics AND reports
4. Provides actionable insights

Structure your response with:
- ## Summary (2-3 sentences)
- ## Key Findings (bullet points with data)
- ## Chart Interpretation (what the visualization shows)
- ## Recommendations (if applicable)

Keep it concise but informative. Use actual numbers from the data and cite report insights."""
    else:
        system_prompt = """You are a game analytics expert presenting insights to stakeholders.

Create a clear, data-driven explanation that:
1. Directly answers the user's question
2. Explains the chart visualization
3. Cites specific data points from metrics ONLY
4. Provides actionable insights

Structure your response with:
- ## Summary (2-3 sentences)
- ## Key Findings (bullet points with data)
- ## Chart Interpretation (what the visualization shows)
- ## Recommendations (if applicable)

Keep it concise but informative. Use actual numbers from the data. Do NOT reference any external reports or documents."""

    # Build user content based on RAG setting
    if enable_rag:
        user_content = f"""Question: {question}

Context: {title} {season} Week {week}

## Analysis
{analysis}

## Chart: {chart_title} ({chart_type})
{chart_summary}

## Report References
{references}

Please provide a comprehensive explanation using both metrics data and report insights."""
    else:
        user_content = f"""Question: {question}

Context: {title} {season} Week {week}

## Analysis
{analysis}

## Chart: {chart_title} ({chart_type})
{chart_summary}

Please provide a data-driven explanation using ONLY the metrics data shown above. Do NOT mention or cite any reports or external documents."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    
    final_explanation = chat_completion(messages, temperature=0.5, max_tokens=1500)
    
    # Format reference list - empty if RAG disabled
    reference_list = []
    if enable_rag and rag_references:
        for ref in rag_references:
            reference_list.append(f"{ref.get('source', 'unknown')} - {ref.get('title', '')} {ref.get('season', '')} Week {ref.get('week', '')}")
    
    print(f"[Node 4] Final explanation generated (RAG: {'enabled' if enable_rag else 'disabled'}, refs: {len(reference_list)})")
    
    return {
        "final_explanation": final_explanation,
        "references": reference_list
    }


def format_chart_summary(sql_result: List[Dict], chart_type: str) -> str:
    """Format chart data as summary text"""
    if not sql_result:
        return "No data available for chart."
    
    lines = []
    for i, row in enumerate(sql_result[:5], 1):
        segment = row.get("segment_combo", "Overall")
        if segment:
            segment = segment.replace("_", " ").replace("=", ": ")
        
        contribution = row.get("contribution_value")
        if contribution:
            contribution = f"{float(contribution) * 100:.1f}%"
        else:
            contribution = "-"
        
        value = row.get("value_current")
        if value:
            value = f"{float(value)/1e6:.1f}M"
        else:
            value = "-"
        
        delta = row.get("value_delta")
        if delta:
            delta = f"{float(delta)/1e6:+.1f}M"
        else:
            delta = "-"
        
        is_outlier = "⚠️" if row.get("is_outlier") else ""
        
        lines.append(f"{i}. {segment}: {contribution} contribution, {value} current ({delta}) {is_outlier}")
    
    return "\n".join(lines)


def format_references(rag_references: List[Dict]) -> str:
    """Format RAG references"""
    if not rag_references:
        return "No references available."
    
    lines = []
    for i, ref in enumerate(rag_references, 1):
        source = ref.get("source", "unknown")
        title = ref.get("title", "")
        season = ref.get("season", "")
        week = ref.get("week", "")
        summary = ref.get("summary", "")[:100]
        
        lines.append(f"[{i}] {source}")
        lines.append(f"    {title} {season} Week {week}")
        if summary:
            lines.append(f"    Summary: {summary}...")
    
    return "\n".join(lines)

