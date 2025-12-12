"""
Node 3: SQL Generation + ECharts Configuration
- Generate SQL query based on chart decision
- Execute query and get data
- Generate ECharts configuration
- Generate Python visualization code
"""
from typing import Dict, Any, List
import json
from state import WorkflowState
from utils.database import execute_sql
from utils.llm import chat_completion


def sql_generation_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Node 3: SQL Generation + ECharts
    
    Input: chart_type, chart_title, x_axis, y_axis, chart_filter from Node 2
    Output: sql_query, sql_result, echarts_option, python_code
    """
    print("[Node 3] Generating SQL and charts...")
    
    title = state.get("title", "bo6_wz2")
    season = state.get("season", "Season 3")
    week = state.get("week", 1)
    chart_type = state.get("chart_type", "bar")
    chart_title = state.get("chart_title", "Chart")
    x_axis = state.get("x_axis", "segment_combo")
    y_axis = state.get("y_axis", "contribution_value")
    chart_filter = state.get("chart_filter", "")
    
    # Step 1: Generate SQL
    sql_query = generate_sql(title, season, week, x_axis, y_axis, chart_filter)
    print(f"[Node 3] SQL: {sql_query[:100]}...")
    
    # Step 2: Execute SQL
    try:
        sql_result = execute_sql(sql_query)
        print(f"[Node 3] Got {len(sql_result)} rows")
    except Exception as e:
        print(f"[Node 3] SQL error: {e}")
        sql_result = []
    
    # Step 3: Generate ECharts configuration
    echarts_option = generate_echarts(sql_result, chart_type, chart_title, x_axis, y_axis)
    
    # Step 4: Generate Python visualization code
    python_code = generate_python_code(sql_query, chart_type, chart_title, x_axis, y_axis)
    
    return {
        "sql_query": sql_query,
        "sql_result": sql_result,
        "echarts_option": echarts_option,
        "python_code": python_code
    }


def generate_sql(
    title: str,
    season: str,
    week: int,
    x_axis: str,
    y_axis: str,
    chart_filter: str
) -> str:
    """Generate SQL query for chart data"""
    
    # Build WHERE clause
    conditions = [
        f"title = '{title}'",
        f"season = '{season}'",
        f"week_number = {week}"
    ]
    
    if chart_filter:
        conditions.append(chart_filter)
    
    # Handle different x_axis fields
    if x_axis == "segment_combo":
        conditions.append("segment_combo IS NOT NULL")
    
    where_clause = " AND ".join(conditions)
    
    # Select appropriate fields
    sql = f"""
SELECT 
    {x_axis},
    metric_name,
    {y_axis},
    value_current,
    value_previous,
    value_delta,
    is_outlier,
    outlier_type
FROM metrics_data
WHERE {where_clause}
ORDER BY {y_axis} DESC NULLS LAST
LIMIT 10
"""
    return sql.strip()


def generate_echarts(
    data: List[Dict],
    chart_type: str,
    chart_title: str,
    x_axis: str,
    y_axis: str
) -> Dict[str, Any]:
    """Generate ECharts configuration"""
    
    if not data:
        return {
            "title": {"text": chart_title},
            "xAxis": {"type": "category", "data": []},
            "yAxis": {"type": "value"},
            "series": [{"type": chart_type, "data": []}]
        }
    
    # Extract data for chart
    x_data = []
    y_data = []
    
    for row in data:
        x_val = row.get(x_axis, "Unknown")
        if x_val and isinstance(x_val, str):
            # Clean up segment names
            x_val = x_val.replace("_", " ").replace("=", ": ")
        x_data.append(x_val or "Unknown")
        
        y_val = row.get(y_axis, 0)
        if y_val is None:
            y_val = 0
        # Convert to percentage if contribution_value
        if y_axis == "contribution_value" and isinstance(y_val, (int, float)):
            y_val = round(float(y_val) * 100, 1)
        y_data.append(y_val)
    
    # Base configuration
    echarts_option = {
        "title": {
            "text": chart_title,
            "left": "center"
        },
        "tooltip": {
            "trigger": "axis" if chart_type in ["bar", "line"] else "item"
        },
        "grid": {
            "left": "3%",
            "right": "4%",
            "bottom": "15%",
            "containLabel": True
        }
    }
    
    if chart_type == "bar":
        echarts_option.update({
            "xAxis": {
                "type": "category",
                "data": x_data,
                "axisLabel": {
                    "rotate": 45,
                    "interval": 0
                }
            },
            "yAxis": {
                "type": "value",
                "name": "Contribution %" if y_axis == "contribution_value" else y_axis
            },
            "series": [{
                "type": "bar",
                "data": y_data,
                "itemStyle": {
                    "color": {
                        "type": "linear",
                        "x": 0, "y": 0, "x2": 0, "y2": 1,
                        "colorStops": [
                            {"offset": 0, "color": "#83bff6"},
                            {"offset": 1, "color": "#188df0"}
                        ]
                    }
                },
                "label": {
                    "show": True,
                    "position": "top",
                    "formatter": "{c}%"
                }
            }]
        })
    
    elif chart_type == "pie":
        pie_data = [{"value": y, "name": x} for x, y in zip(x_data, y_data)]
        echarts_option.update({
            "series": [{
                "type": "pie",
                "radius": ["40%", "70%"],
                "data": pie_data,
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowOffsetX": 0,
                        "shadowColor": "rgba(0, 0, 0, 0.5)"
                    }
                },
                "label": {
                    "formatter": "{b}: {d}%"
                }
            }]
        })
    
    elif chart_type == "line":
        echarts_option.update({
            "xAxis": {
                "type": "category",
                "data": x_data
            },
            "yAxis": {
                "type": "value"
            },
            "series": [{
                "type": "line",
                "data": y_data,
                "smooth": True
            }]
        })
    
    return echarts_option


def generate_python_code(
    sql_query: str,
    chart_type: str,
    chart_title: str,
    x_axis: str,
    y_axis: str
) -> str:
    """Generate Python visualization code using matplotlib/seaborn"""
    
    code = f'''import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# SQL Query
sql = """
{sql_query}
"""

# Execute query and load data
# df = pd.read_sql(sql, connection)

# Sample data (replace with actual query result)
df = pd.DataFrame(data)  # data from SQL result

# Create visualization
plt.figure(figsize=(12, 6))
'''
    
    if chart_type == "bar":
        code += f'''
# Bar chart
sns.barplot(data=df, x='{x_axis}', y='{y_axis}', palette='Blues_d')
plt.title('{chart_title}')
plt.xlabel('{x_axis.replace("_", " ").title()}')
plt.ylabel('{y_axis.replace("_", " ").title()}')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
'''
    elif chart_type == "pie":
        code += f'''
# Pie chart
plt.pie(df['{y_axis}'], labels=df['{x_axis}'], autopct='%1.1f%%')
plt.title('{chart_title}')
'''
    elif chart_type == "line":
        code += f'''
# Line chart
plt.plot(df['{x_axis}'], df['{y_axis}'], marker='o')
plt.title('{chart_title}')
plt.xlabel('{x_axis.replace("_", " ").title()}')
plt.ylabel('{y_axis.replace("_", " ").title()}')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
'''
    
    code += '''
plt.savefig('chart.png', dpi=150, bbox_inches='tight')
plt.show()
'''
    
    return code

