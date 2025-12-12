"""
Node 2: Chart Decision
- Analyze the question and data to decide what chart to show
- Generate chart configuration
"""
from typing import Dict, Any
import json
from state import WorkflowState
from utils.llm import chat_completion


def chart_decision_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Node 2: Chart Decision
    
    Input: analysis, key_metrics, key_segments from Node 1
    Output: chart_type, chart_title, x_axis, y_axis, chart_filter
    """
    print("[Node 2] Deciding chart type...")
    
    question = state.get("question", "")
    analysis = state.get("analysis", "")
    key_metrics = state.get("key_metrics", [])
    key_segments = state.get("key_segments", [])
    title = state.get("title", "bo6_wz2")
    season = state.get("season", "Season 3")
    week = state.get("week", 1)
    
    # Use LLM to decide chart type
    system_prompt = """You are a data visualization expert. Based on the user's question and analysis, decide the best chart type and configuration.

Available chart types:
- bar: For comparing categories (segments, modes)
- line: For trends over time
- pie: For showing proportions
- scatter: For correlations

Available metrics in the database:
- br_hours: BR mode play hours
- dau: Daily Active Users
- mp_hours: Multiplayer hours

Available segments:
- mode_main: BR Main, Resurgence, Plunder
- premium_label: Premium, F2P
- spending_segment: Whales, Dolphins, Minnows

Respond in JSON format:
{
    "chart_type": "bar|line|pie|scatter",
    "chart_title": "Title for the chart",
    "x_axis": "field name for x-axis",
    "y_axis": "field name for y-axis (usually value_current or contribution_value)",
    "filter_sql": "SQL WHERE clause for filtering data (e.g., 'is_outlier = true')",
    "reasoning": "Brief explanation of why this chart"
}"""

    user_content = f"""Question: {question}

Analysis: {analysis}

Key metrics: {key_metrics}
Key segments: {key_segments}

Context: {title} {season} Week {week}

What chart should we show?"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    
    response = chat_completion(messages, temperature=0.3, max_tokens=500)
    
    # Parse response
    try:
        decision = json.loads(response)
    except json.JSONDecodeError:
        # Default to bar chart
        decision = {
            "chart_type": "bar",
            "chart_title": f"Top Contributors - {season} Week {week}",
            "x_axis": "segment_combo",
            "y_axis": "contribution_value",
            "filter_sql": "is_outlier = true",
            "reasoning": "Default: showing top contributing segments"
        }
    
    print(f"[Node 2] Chart decision: {decision.get('chart_type')} - {decision.get('chart_title')}")
    
    return {
        "chart_type": decision.get("chart_type", "bar"),
        "chart_title": decision.get("chart_title", "Chart"),
        "x_axis": decision.get("x_axis", "segment_combo"),
        "y_axis": decision.get("y_axis", "contribution_value"),
        "chart_filter": decision.get("filter_sql", "")
    }

