# Data Dashboard Architecture V2 - Integrated System

## 🎯 Overview

An intelligent data dashboard that integrates:
- **Supabase**: Database + Backend + Auth
- **ODR (Open Deep Research)**: AI Research Reports
- **Perplexica**: Search Engine
- **LIDA**: Natural Language to Visualization
- **Databricks**: Weekly Data Pipeline
- **React**: Frontend Dashboard

---

## 🏗️ Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Databricks Pipeline                          │
│              (Weekly Anomaly Detection)                         │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  1. Detect anomalies                                     │  │
│   │  2. Trigger ODR research                                 │  │
│   │  3. Store to Supabase                                    │  │
│   └──────────────────┬──────────────────────────────────────┘  │
└────────────────────────┼──────────────────────────────────────┘
                         │ Weekly ETL
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Supabase                                   │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  Tables:                                                 │  │
│   │  • anomalies (title, season, week, date, metrics)      │  │
│   │  • research_reports (title, season, week, content)     │  │
│   │  • visualizations (chart_specs, data)                  │  │
│   └─────────────────────────────────────────────────────────┘  │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  Edge Functions:                                         │  │
│   │  • query-handler (NL → SQL via LIDA)                    │  │
│   │  • report-retriever (Get research reports)              │  │
│   │  • chart-generator (Generate visualizations)            │  │
│   └─────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │ REST API
                         │
┌────────────────────────▼────────────────────────────────────────┐
│              Backend Integration Layer                          │
│                   (FastAPI Service)                             │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  Services:                                               │  │
│   │  • LIDA Service (NL2SQL + NL2Vis)                       │  │
│   │  • ODR Client (Trigger research)                        │  │
│   │  • Perplexica Client (Search context)                   │  │
│   │  • Supabase Client (Data access)                        │  │
│   └─────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/WebSocket
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                  React Frontend                                 │
│               (game-dashboard)                                  │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  Components:                                             │  │
│   │  • Dashboard (Default: Latest week data)                │  │
│   │  • ChatBot (NL queries)                                  │  │
│   │  • ChartRenderer (Dynamic charts)                       │  │
│   │  • ReportViewer (Research reports)                      │  │
│   │  • AnomalyExplorer (Browse anomalies)                   │  │
│   └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Schema (Supabase)

### Table 1: `anomalies`

```sql
CREATE TABLE anomalies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    season TEXT NOT NULL,
    week INTEGER NOT NULL,
    date DATE NOT NULL,
    
    -- Game metrics
    game_name TEXT,
    metric_name TEXT NOT NULL,
    metric_value NUMERIC,
    expected_value NUMERIC,
    deviation_percentage NUMERIC,
    
    -- Anomaly details
    anomaly_type TEXT, -- 'spike', 'drop', 'trend'
    severity TEXT,     -- 'critical', 'high', 'medium', 'low'
    
    -- Metadata
    databricks_job_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Indexes
    CONSTRAINT unique_anomaly UNIQUE (title, season, week, metric_name)
);

CREATE INDEX idx_anomalies_date ON anomalies(date DESC);
CREATE INDEX idx_anomalies_title_season_week ON anomalies(title, season, week);
```

### Table 2: `research_reports`

```sql
CREATE TABLE research_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Report identifiers
    title TEXT NOT NULL,
    season TEXT NOT NULL,
    week INTEGER NOT NULL,
    date DATE NOT NULL,
    
    -- Report content
    report_content TEXT NOT NULL,  -- Markdown format from ODR
    report_summary TEXT,
    
    -- Research metadata
    odr_thread_id TEXT,
    search_queries TEXT[],
    sources JSONB,  -- URLs and citations
    
    -- Images
    images JSONB,  -- [{url, caption, source}]
    
    -- Status
    status TEXT DEFAULT 'completed',
    generation_time_seconds INTEGER,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_report UNIQUE (title, season, week)
);

CREATE INDEX idx_reports_date ON research_reports(date DESC);
CREATE INDEX idx_reports_title_season_week ON research_reports(title, season, week);
```

### Table 3: `visualizations`

```sql
CREATE TABLE visualizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Link to report/anomaly
    anomaly_id UUID REFERENCES anomalies(id),
    report_id UUID REFERENCES research_reports(id),
    
    -- Chart specification (LIDA format)
    chart_spec JSONB NOT NULL,
    
    -- Data for the chart
    chart_data JSONB NOT NULL,
    
    -- Metadata
    chart_type TEXT,  -- 'line', 'bar', 'pie', etc.
    title TEXT,
    description TEXT,
    
    -- User query that generated this
    user_query TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_visualizations_anomaly ON visualizations(anomaly_id);
CREATE INDEX idx_visualizations_report ON visualizations(report_id);
```

### Table 4: `chat_history`

```sql
CREATE TABLE chat_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- User session
    session_id UUID NOT NULL,
    user_id UUID,  -- If auth enabled
    
    -- Chat message
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    
    -- Generated artifacts
    sql_query TEXT,
    chart_id UUID REFERENCES visualizations(id),
    
    -- Context
    title TEXT,
    season TEXT,
    week INTEGER,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chat_session ON chat_history(session_id, created_at);
```

---

## 🔄 Databricks → Supabase Pipeline

### Weekly ETL Flow

```python
# Databricks Notebook: weekly_anomaly_pipeline.py

from datetime import datetime, timedelta
import requests
from supabase import create_client

# Initialize clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
odr_api = "https://your-odr-endpoint.com"

def detect_anomalies(df):
    """Your existing anomaly detection logic"""
    # Returns list of anomalies
    pass

def trigger_odr_research(anomaly):
    """Trigger ODR to research the anomaly"""
    query = f"""
    Research the following game anomaly:
    Title: {anomaly['title']}
    Season: {anomaly['season']}
    Week: {anomaly['week']}
    Metric: {anomaly['metric_name']}
    Issue: {anomaly['metric_name']} showed a {anomaly['deviation_percentage']}% 
    {anomaly['anomaly_type']} compared to expected value.
    
    Please analyze:
    1. What caused this anomaly?
    2. Is this a positive or negative trend?
    3. What actions should be taken?
    4. Include relevant data visualizations and comparisons.
    """
    
    response = requests.post(
        f"{odr_api}/threads/create",
        headers={"Authorization": f"Bearer {ODR_TOKEN}"},
        json={
            "assistant_id": "Deep Researcher",
            "input": {"query": query}
        }
    )
    
    thread_id = response.json()["thread_id"]
    
    # Wait for completion and get report
    report = wait_for_odr_report(thread_id)
    
    return report

def store_to_supabase(anomaly, report):
    """Store anomaly and report to Supabase"""
    
    # 1. Insert anomaly
    anomaly_result = supabase.table("anomalies").insert({
        "title": anomaly["title"],
        "season": anomaly["season"],
        "week": anomaly["week"],
        "date": anomaly["date"],
        "game_name": anomaly.get("game_name"),
        "metric_name": anomaly["metric_name"],
        "metric_value": anomaly["metric_value"],
        "expected_value": anomaly["expected_value"],
        "deviation_percentage": anomaly["deviation_percentage"],
        "anomaly_type": anomaly["anomaly_type"],
        "severity": anomaly["severity"],
        "databricks_job_id": dbutils.notebook.entry_point.getDbutils().notebook().getContext().jobId().get()
    }).execute()
    
    anomaly_id = anomaly_result.data[0]["id"]
    
    # 2. Insert research report
    report_result = supabase.table("research_reports").insert({
        "title": anomaly["title"],
        "season": anomaly["season"],
        "week": anomaly["week"],
        "date": anomaly["date"],
        "report_content": report["content"],
        "report_summary": report.get("summary"),
        "odr_thread_id": report["thread_id"],
        "search_queries": report.get("queries", []),
        "sources": report.get("sources", []),
        "images": report.get("images", []),
        "generation_time_seconds": report.get("duration")
    }).execute()
    
    return anomaly_id, report_result.data[0]["id"]

# Main pipeline
def main():
    # 1. Get current week data
    current_week = datetime.now().isocalendar()[1]
    df = spark.table("game_metrics").filter(f"week = {current_week}")
    
    # 2. Detect anomalies
    anomalies = detect_anomalies(df)
    
    # 3. For each anomaly, trigger ODR research and store
    for anomaly in anomalies:
        print(f"Processing anomaly: {anomaly['title']} - {anomaly['metric_name']}")
        
        # Trigger ODR research
        report = trigger_odr_research(anomaly)
        
        # Store to Supabase
        anomaly_id, report_id = store_to_supabase(anomaly, report)
        
        print(f"Stored: anomaly_id={anomaly_id}, report_id={report_id}")
    
    print(f"Pipeline completed: {len(anomalies)} anomalies processed")

# Schedule: Run every Monday at 2 AM
main()
```

---

## 🔧 Backend Service (FastAPI)

### File: `backend/lida-service/main.py`

```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
from datetime import datetime, timedelta

from supabase import create_client, Client
from lida import Manager, TextGenerationConfig
import requests

app = FastAPI(title="Integrated Dashboard API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

lida = Manager(text_gen=TextGenerationConfig(
    model="gpt-4",
    api_key=os.getenv("OPENAI_API_KEY")
))

odr_api = os.getenv("ODR_API_URL", "http://open-deep-research-service:8000")
perplexica_api = os.getenv("PERPLEXICA_API_URL", "http://perplexica-service/api/tavily")

# ============================================
# Models
# ============================================

class DashboardQuery(BaseModel):
    title: Optional[str] = None
    season: Optional[str] = None
    week: Optional[int] = None
    date: Optional[str] = None

class ChatQuery(BaseModel):
    message: str
    session_id: str
    context: Optional[DashboardQuery] = None

class VisualizationRequest(BaseModel):
    query: str
    title: str
    season: str
    week: int

# ============================================
# Helper Functions
# ============================================

def get_latest_week():
    """Get the latest week with data"""
    result = supabase.table("anomalies")\
        .select("date, week")\
        .order("date", desc=True)\
        .limit(1)\
        .execute()
    
    if result.data:
        return result.data[0]
    return None

def get_anomalies(title: str = None, season: str = None, week: int = None):
    """Get anomalies with optional filters"""
    query = supabase.table("anomalies").select("*")
    
    if title:
        query = query.eq("title", title)
    if season:
        query = query.eq("season", season)
    if week:
        query = query.eq("week", week)
    
    result = query.order("date", desc=True).execute()
    return result.data

def get_research_report(title: str, season: str, week: int):
    """Get research report for specific context"""
    result = supabase.table("research_reports")\
        .select("*")\
        .eq("title", title)\
        .eq("season", season)\
        .eq("week", week)\
        .single()\
        .execute()
    
    return result.data if result.data else None

def natural_language_to_sql(query: str, context: dict) -> str:
    """Convert natural language to SQL using LIDA"""
    
    # Get table schema
    schema_info = """
    Table: anomalies
    Columns: title, season, week, date, game_name, metric_name, 
             metric_value, expected_value, deviation_percentage, 
             anomaly_type, severity
    
    Example query context:
    - title: {title}
    - season: {season}
    - week: {week}
    """.format(**context)
    
    # Use LIDA to generate SQL
    # (In practice, you might use a custom prompt with GPT-4)
    prompt = f"""
    Given this database schema:
    {schema_info}
    
    Convert this natural language query to SQL:
    "{query}"
    
    Return only the SQL query, no explanations.
    """
    
    # Use OpenAI directly for SQL generation
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY")
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a SQL expert. Generate PostgreSQL queries."},
            {"role": "user", "content": prompt}
        ]
    )
    
    sql = response.choices[0].message.content.strip()
    # Clean up markdown code blocks if present
    sql = sql.replace("```sql", "").replace("```", "").strip()
    
    return sql

# ============================================
# API Endpoints
# ============================================

@app.get("/api/dashboard/latest")
async def get_latest_dashboard():
    """Get latest week's dashboard data"""
    
    latest = get_latest_week()
    if not latest:
        raise HTTPException(status_code=404, detail="No data found")
    
    # Get anomalies for latest week
    anomalies = get_anomalies(week=latest["week"])
    
    # Get unique titles from anomalies
    titles = list(set([a["title"] for a in anomalies]))
    
    # Get research reports for each title
    reports = []
    for title in titles:
        # Assuming anomalies have same season
        season = anomalies[0]["season"]
        report = get_research_report(title, season, latest["week"])
        if report:
            reports.append(report)
    
    return {
        "week": latest["week"],
        "date": latest["date"],
        "anomalies": anomalies,
        "reports": reports
    }

@app.post("/api/dashboard/query")
async def query_dashboard(query: DashboardQuery):
    """Query dashboard with filters"""
    
    # If no filters, return latest
    if not any([query.title, query.season, query.week, query.date]):
        return await get_latest_dashboard()
    
    # Get anomalies
    anomalies = get_anomalies(
        title=query.title,
        season=query.season,
        week=query.week
    )
    
    # Get reports
    reports = []
    if query.title and query.season and query.week:
        report = get_research_report(query.title, query.season, query.week)
        if report:
            reports.append(report)
    
    return {
        "anomalies": anomalies,
        "reports": reports
    }

@app.post("/api/chat/query")
async def chat_query(chat: ChatQuery):
    """Handle natural language chat query"""
    
    try:
        # 1. Determine context (default to latest if not provided)
        context = chat.context
        if not context or not all([context.title, context.season, context.week]):
            latest = get_latest_week()
            if latest:
                # Get first anomaly to extract context
                anomalies = get_anomalies(week=latest["week"])
                if anomalies:
                    context = DashboardQuery(
                        title=anomalies[0]["title"],
                        season=anomalies[0]["season"],
                        week=latest["week"]
                    )
        
        if not context:
            raise HTTPException(status_code=400, detail="No context available")
        
        # 2. Convert NL to SQL
        sql = natural_language_to_sql(
            chat.message,
            {
                "title": context.title,
                "season": context.season,
                "week": context.week
            }
        )
        
        # 3. Execute SQL
        result = supabase.rpc("execute_sql", {"query": sql}).execute()
        data = result.data
        
        # 4. Get research report for context
        report = get_research_report(context.title, context.season, context.week)
        
        # 5. Generate visualization using LIDA
        # Create a temporary CSV from data
        import pandas as pd
        import tempfile
        
        df = pd.DataFrame(data)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            temp_file = f.name
        
        # Use LIDA to generate visualization
        summary = lida.summarize(temp_file)
        charts = lida.visualize(
            summary=summary,
            goal=chat.message,
            library="altair"
        )
        
        # Clean up temp file
        os.unlink(temp_file)
        
        # 6. Generate response combining data + report insights
        response_text = generate_response_with_report(
            query=chat.message,
            data=data,
            report=report,
            sql=sql
        )
        
        # 7. Store chat history
        supabase.table("chat_history").insert({
            "session_id": chat.session_id,
            "message": chat.message,
            "response": response_text,
            "sql_query": sql,
            "title": context.title,
            "season": context.season,
            "week": context.week
        }).execute()
        
        return {
            "response": response_text,
            "sql": sql,
            "data": data,
            "charts": charts,
            "report_summary": report.get("report_summary") if report else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def generate_response_with_report(query: str, data: list, report: dict, sql: str):
    """Generate natural language response combining query results and report"""
    
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY")
    
    prompt = f"""
    User asked: "{query}"
    
    SQL Query executed:
    {sql}
    
    Query results:
    {data[:5]}  # First 5 rows
    
    Research Report Context:
    {report.get('report_summary', 'No report available') if report else 'No report available'}
    
    Generate a clear, concise answer to the user's question, incorporating:
    1. Key insights from the data
    2. Relevant context from the research report
    3. Actionable recommendations if applicable
    
    Keep it under 200 words.
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a data analyst providing insights."},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content

@app.post("/api/research/trigger")
async def trigger_research(title: str, season: str, week: int):
    """Manually trigger ODR research for a specific anomaly"""
    
    # Get anomaly data
    anomalies = get_anomalies(title=title, season=season, week=week)
    if not anomalies:
        raise HTTPException(status_code=404, detail="No anomaly found")
    
    # Trigger ODR
    query = f"""
    Research anomalies for:
    Title: {title}
    Season: {season}
    Week: {week}
    
    Anomalies detected:
    {anomalies}
    
    Provide comprehensive analysis.
    """
    
    response = requests.post(
        f"{odr_api}/threads/create",
        headers={"Authorization": f"Bearer {os.getenv('ODR_TOKEN')}"},
        json={
            "assistant_id": "Deep Researcher",
            "input": {"query": query}
        }
    )
    
    return {"thread_id": response.json()["thread_id"]}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

---

## 🎨 Frontend Components

### 1. Main Dashboard

**File: `frontend/game-dashboard/src/pages/Dashboard.jsx`**

```jsx
import React, { useState, useEffect } from 'react';
import { Box, Grid, Card, CardContent, Typography, CircularProgress } from '@mui/material';
import ChatBot from '../components/ChatBot';
import AnomalyCard from '../components/AnomalyCard';
import ReportViewer from '../components/ReportViewer';
import ChartRenderer from '../components/ChartRenderer';
import { getDashboardData } from '../services/api';

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);
  const [selectedContext, setSelectedContext] = useState(null);

  useEffect(() => {
    loadLatestDashboard();
  }, []);

  const loadLatestDashboard = async () => {
    try {
      setLoading(true);
      const data = await getDashboardData();
      setDashboardData(data);
      
      // Set default context from first anomaly
      if (data.anomalies && data.anomalies.length > 0) {
        const first = data.anomalies[0];
        setSelectedContext({
          title: first.title,
          season: first.season,
          week: first.week
        });
      }
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Typography variant="h4" gutterBottom>
        Game Analytics Dashboard
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Week {dashboardData?.week} - {dashboardData?.date}
      </Typography>

      <Grid container spacing={3}>
        {/* Left: Anomalies */}
        <Grid item xs={12} md={4}>
          <Typography variant="h6" gutterBottom>
            Detected Anomalies ({dashboardData?.anomalies?.length || 0})
          </Typography>
          {dashboardData?.anomalies?.map((anomaly) => (
            <AnomalyCard
              key={anomaly.id}
              anomaly={anomaly}
              onClick={() => setSelectedContext({
                title: anomaly.title,
                season: anomaly.season,
                week: anomaly.week
              })}
            />
          ))}
        </Grid>

        {/* Middle: Research Reports */}
        <Grid item xs={12} md={4}>
          <Typography variant="h6" gutterBottom>
            Research Reports
          </Typography>
          {dashboardData?.reports?.map((report) => (
            <ReportViewer key={report.id} report={report} />
          ))}
        </Grid>

        {/* Right: ChatBot */}
        <Grid item xs={12} md={4}>
          <ChatBot
            context={selectedContext}
            onVisualizationGenerated={(viz) => {
              // Handle visualization
            }}
          />
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
```

### 2. ChatBot Component

**File: `frontend/game-dashboard/src/components/ChatBot.jsx`**

```jsx
import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Paper,
  Typography,
  Avatar,
  Divider
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import PersonIcon from '@mui/icons-material/Person';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import { chatQuery } from '../services/api';
import ChartRenderer from './ChartRenderer';

const ChatBot = ({ context }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => crypto.randomUUID());

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { type: 'user', text: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const result = await chatQuery({
        message: input,
        session_id: sessionId,
        context: context
      });

      const botMessage = {
        type: 'bot',
        text: result.response,
        sql: result.sql,
        data: result.data,
        charts: result.charts,
        report_summary: result.report_summary
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      const errorMessage = {
        type: 'error',
        text: 'Sorry, I encountered an error: ' + error.message
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper sx={{ height: '80vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ p: 2, bgcolor: 'primary.main', color: 'white' }}>
        <Typography variant="h6">AI Assistant</Typography>
        <Typography variant="caption">
          Ask questions about {context?.title} (Week {context?.week})
        </Typography>
      </Box>

      {/* Messages */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        {messages.length === 0 && (
          <Box sx={{ textAlign: 'center', color: 'text.secondary', mt: 4 }}>
            <SmartToyIcon sx={{ fontSize: 60, mb: 2 }} />
            <Typography>
              Ask me anything about the data!
            </Typography>
            <Typography variant="caption" sx={{ display: 'block', mt: 1 }}>
              Examples:
            </Typography>
            <Typography variant="caption" sx={{ display: 'block' }}>
              • "Show me the top 3 anomalies by severity"
            </Typography>
            <Typography variant="caption" sx={{ display: 'block' }}>
              • "What caused the revenue drop?"
            </Typography>
            <Typography variant="caption" sx={{ display: 'block' }}>
              • "Compare this week vs last week"
            </Typography>
          </Box>
        )}

        {messages.map((msg, idx) => (
          <Box key={idx} sx={{ mb: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
              <Avatar sx={{ bgcolor: msg.type === 'user' ? 'primary.main' : 'secondary.main' }}>
                {msg.type === 'user' ? <PersonIcon /> : <SmartToyIcon />}
              </Avatar>
              <Box sx={{ flex: 1 }}>
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                  {msg.text}
                </Typography>

                {/* Show SQL if available */}
                {msg.sql && (
                  <Paper sx={{ mt: 1, p: 1, bgcolor: 'grey.100' }}>
                    <Typography variant="caption" color="text.secondary">
                      SQL Query:
                    </Typography>
                    <Typography variant="body2" component="pre" sx={{ fontSize: '0.75rem' }}>
                      {msg.sql}
                    </Typography>
                  </Paper>
                )}

                {/* Show charts if available */}
                {msg.charts && msg.charts.length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    {msg.charts.map((chart, i) => (
                      <ChartRenderer
                        key={i}
                        chartSpec={chart.spec}
                        data={msg.data}
                      />
                    ))}
                  </Box>
                )}
              </Box>
            </Box>
            {idx < messages.length - 1 && <Divider sx={{ mt: 2 }} />}
          </Box>
        ))}

        {loading && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Avatar sx={{ bgcolor: 'secondary.main' }}>
              <SmartToyIcon />
            </Avatar>
            <Typography variant="body2" color="text.secondary">
              Thinking...
            </Typography>
          </Box>
        )}
      </Box>

      {/* Input */}
      <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            placeholder="Ask a question..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            disabled={loading}
            multiline
            maxRows={3}
          />
          <Button
            variant="contained"
            onClick={handleSend}
            disabled={loading || !input.trim()}
            endIcon={<SendIcon />}
          >
            Send
          </Button>
        </Box>
      </Box>
    </Paper>
  );
};

export default ChatBot;
```

---

## 🚀 Deployment Steps

### 1. Supabase Setup

```sql
-- Run these SQL commands in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tables (use schemas above)
-- ...

-- Create RPC function for executing custom SQL
CREATE OR REPLACE FUNCTION execute_sql(query TEXT)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  result JSON;
BEGIN
  EXECUTE query INTO result;
  RETURN result;
END;
$$;

-- Row Level Security (Optional)
ALTER TABLE anomalies ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_reports ENABLE ROW LEVEL SECURITY;
```

### 2. Environment Variables

**File: `backend/lida-service/.env`**
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
OPENAI_API_KEY=sk-...
ODR_API_URL=http://open-deep-research-service:8000
ODR_TOKEN=your-odr-jwt-token
PERPLEXICA_API_URL=http://perplexica-service/api/tavily
```

### 3. Docker Compose (Local Development)

**File: `docker-compose.yml`**
```yaml
version: '3.8'

services:
  backend:
    build: ./backend/lida-service
    ports:
      - "8000:8000"
    env_file:
      - ./backend/lida-service/.env
    depends_on:
      - odr
      - perplexica

  frontend:
    build: ./frontend/game-dashboard
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000

  # ODR and Perplexica services (already configured)
  odr:
    image: shankswhite/open-deep-research:v1.10-rate-limit
    # ...existing config...

  perplexica:
    image: shankswhite/perplexica:tavily-v1.1
    # ...existing config...
```

---

## 📊 Example Usage Scenarios

### Scenario 1: View Latest Anomalies

User opens dashboard → Sees latest week's anomalies → Clicks on an anomaly → Views research report

### Scenario 2: Ask About Specific Metric

```
User: "Show me revenue trends for the last 3 weeks"

Bot generates SQL:
SELECT week, SUM(metric_value) as total_revenue
FROM anomalies
WHERE metric_name = 'revenue'
  AND week >= CURRENT_WEEK - 3
GROUP BY week
ORDER BY week

Bot generates line chart and explains the trend
```

### Scenario 3: Deep Dive into Anomaly

```
User: "Why did player retention drop in week 42?"

Bot:
1. Queries anomaly data
2. References research report
3. Shows visualization
4. Provides insights from ODR research
```

---

## 🎯 Next Steps

1. ✅ Set up Supabase database
2. ✅ Configure Databricks pipeline
3. ✅ Deploy backend service
4. ✅ Update React frontend
5. ✅ Test end-to-end flow
6. ✅ Deploy to production

---

**Status**: Ready for Implementation  
**Created**: 2024-11-24  
**Version**: 2.0 (Integrated)

