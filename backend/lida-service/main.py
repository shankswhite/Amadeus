"""
LIDA Service - NL2SQL & NL2Vis API
Flow: 
1. Generate SQL
2. LIDA generates matplotlib/seaborn Python code
3. LLM converts Python code to ECharts config
"""

import os
import json
import re
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI

# Initialize FastAPI
app = FastAPI(
    title="LIDA Service",
    description="NL2SQL and NL2Vis API - Python to ECharts",
    version="2.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
MODEL = "o4-mini"

print(f"✅ LIDA Service v2.0 - Python to ECharts")
print(f"✅ Using model: {MODEL}")


# Request Models
class QueryRequest(BaseModel):
    query: str
    include_visualization: bool = True


# Database Schema
DATABASE_SCHEMA = """
Tables:
1. research_reports (thread_id, title, season, week_number, report_content)
2. anomalies (title, season, week_number, metric_name, metric_value, deviation_percentage, severity)
"""

# Mock data
MOCK_DATA = {
    "revenue": [
        {"name": "Call of Duty BO7", "value": 2500000},
        {"name": "FIFA 25", "value": 1800000},
        {"name": "Valorant", "value": 1500000},
        {"name": "Fortnite", "value": 1200000},
        {"name": "Apex Legends", "value": 900000},
    ],
    "trend": [
        {"week": "W43", "revenue": 5200000, "players": 1800000},
        {"week": "W44", "revenue": 5800000, "players": 2000000},
        {"week": "W45", "revenue": 6200000, "players": 2100000},
        {"week": "W46", "revenue": 7100000, "players": 2300000},
        {"week": "W47", "revenue": 7900000, "players": 2400000},
    ],
    "anomalies": [
        {"title": "CoD BO7", "metric": "revenue", "deviation": 45, "severity": "high"},
        {"title": "Valorant", "metric": "players", "deviation": -15, "severity": "medium"},
        {"title": "Fortnite", "metric": "session", "deviation": 20, "severity": "low"},
    ]
}


def call_llm(prompt: str, max_tokens: int = 2000) -> str:
    """Call OpenAI o4-mini model"""
    if not client:
        raise Exception("OpenAI client not initialized")
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=max_tokens
    )
    return response.choices[0].message.content or ""


def get_mock_data(query: str) -> list:
    """Return mock data based on query"""
    query_lower = query.lower()
    if "trend" in query_lower or "weekly" in query_lower:
        return MOCK_DATA["trend"]
    elif "anomal" in query_lower:
        return MOCK_DATA["anomalies"]
    else:
        return MOCK_DATA["revenue"]


@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "LIDA Service",
        "version": "2.0.0",
        "flow": "Python (matplotlib) → ECharts"
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "model": MODEL}


@app.post("/api/query")
async def process_query(request: QueryRequest):
    """
    Main endpoint:
    1. Generate SQL
    2. Generate matplotlib/seaborn Python code (LIDA style)
    3. Convert Python code to ECharts config
    """
    try:
        # === Step 1: Generate SQL ===
        sql_prompt = f"""Convert to PostgreSQL SQL.
Schema: {DATABASE_SCHEMA}
Question: {request.query}
Return ONLY SQL:"""

        print(f"\n🔍 Query: {request.query}")
        sql = call_llm(sql_prompt)
        sql = re.sub(r'```\w*\n?', '', sql.strip()).strip()
        print(f"  ✅ SQL generated")

        # Get mock data (will be replaced with actual DB query)
        data = get_mock_data(request.query)

        # === Step 2: Generate matplotlib/seaborn Python code ===
        python_code = None
        echarts_option = None
        
        if request.include_visualization and data:
            python_prompt = f"""You are a data visualization expert. Generate matplotlib/seaborn Python code to visualize this data.

Query: {request.query}
Data: {json.dumps(data)}

Requirements:
1. Use matplotlib or seaborn
2. Create a clear, professional visualization
3. Add proper labels, title, and styling
4. The code should be complete and runnable

Return ONLY the Python code (no markdown):"""

            print("  🐍 Generating Python code...")
            python_code = call_llm(python_prompt)
            python_code = re.sub(r'```\w*\n?', '', python_code.strip()).strip()
            print(f"  ✅ Python code generated ({len(python_code)} chars)")

            # === Step 3: Convert Python to ECharts ===
            echarts_prompt = f"""Convert this matplotlib/seaborn Python visualization code to an ECharts option configuration.

Python code:
{python_code}

Data to use:
{json.dumps(data)}

Return ONLY a valid JSON object (ECharts option), no markdown, no explanation.
The JSON must include:
- title
- xAxis or equivalent  
- yAxis or equivalent
- series with data
- appropriate chart type (bar, line, pie, scatter, etc.)

ECharts option JSON:"""

            print("  📊 Converting to ECharts...")
            echarts_text = call_llm(echarts_prompt, max_tokens=1500)
            echarts_text = re.sub(r'```\w*\n?', '', echarts_text.strip()).strip()
            
            try:
                echarts_option = json.loads(echarts_text)
                print("  ✅ ECharts config generated")
            except json.JSONDecodeError as e:
                print(f"  ⚠️ JSON parse error: {e}")
                # Fallback: create basic ECharts config
                echarts_option = create_fallback_echarts(data, request.query)

        # === Step 4: Generate explanation ===
        explanation = call_llm(f"Explain in one sentence: {sql}", max_tokens=200).strip()

        return {
            "sql": sql,
            "python_code": python_code,
            "echarts_option": echarts_option,
            "data": data,
            "explanation": explanation,
            "status": "success",
            "model": MODEL
        }

    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def create_fallback_echarts(data: list, query: str) -> dict:
    """Create a basic ECharts config as fallback"""
    if not data:
        return {}
    
    # Detect chart type from query
    query_lower = query.lower()
    
    if "trend" in query_lower or "weekly" in query_lower:
        # Line chart for trends
        x_data = [d.get("week", d.get("name", str(i))) for i, d in enumerate(data)]
        series = []
        for key in data[0].keys():
            if key not in ["week", "name"] and isinstance(data[0][key], (int, float)):
                series.append({
                    "name": key.capitalize(),
                    "type": "line",
                    "data": [d.get(key, 0) for d in data],
                    "smooth": True
                })
        return {
            "title": {"text": "Weekly Trend", "left": "center"},
            "tooltip": {"trigger": "axis"},
            "legend": {"top": 30},
            "xAxis": {"type": "category", "data": x_data},
            "yAxis": {"type": "value"},
            "series": series
        }
    else:
        # Bar chart as default
        x_data = [d.get("name", d.get("title", str(i))) for i, d in enumerate(data)]
        y_data = [d.get("value", d.get("deviation", 0)) for d in data]
        return {
            "title": {"text": "Query Results", "left": "center"},
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": x_data, "axisLabel": {"rotate": 30}},
            "yAxis": {"type": "value"},
            "series": [{
                "type": "bar",
                "data": y_data,
                "itemStyle": {"color": "#e94560"}
            }]
        }


if __name__ == "__main__":
    import uvicorn
    print(f"🚀 Starting LIDA Service v2.0")
    uvicorn.run(app, host="0.0.0.0", port=8080)
