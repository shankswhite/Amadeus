# Data Dashboard Architecture with LIDA

## 🎯 Overview

Building an intelligent data dashboard that uses Natural Language to generate SQL queries and visualizations powered by LIDA (NL2Vis).

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface                           │
│                  (React Frontend)                           │
│   ┌─────────────────────────────────────────────────────┐  │
│   │  - Chat Interface                                    │  │
│   │  - Dashboard Display                                 │  │
│   │  - Chart Rendering (Recharts/ECharts)              │  │
│   └─────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/WebSocket
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              LIDA Service (Backend)                         │
│                  (FastAPI/Flask)                            │
│   ┌─────────────────────────────────────────────────────┐  │
│   │  LIDA Core Components:                              │  │
│   │  1. Summarizer (数据分析)                            │  │
│   │  2. Goal Generator (目标生成)                        │  │
│   │  3. VisualizationGenerator (图表生成)               │  │
│   │  4. Executor (SQL执行)                              │  │
│   └─────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ├─── LLM (OpenAI/Claude) ───┐
                       │                            │
                       └─── Database ───────────────┘
                            (PostgreSQL/MySQL)
```

---

## 📦 Components

### 1. Frontend (React + game-dashboard)

**Location**: `frontend/game-dashboard/`

**Features**:
- 💬 **Chat Interface**: Natural language input for queries
- 📊 **Dashboard**: Display multiple charts
- 🎨 **Chart Rendering**: Using Recharts or Apache ECharts
- 📱 **Responsive Design**: Mobile-friendly

**Tech Stack**:
```json
{
  "framework": "React 18",
  "ui": "Material-UI / Ant Design",
  "charts": "Recharts / Apache ECharts / Plotly.js",
  "state": "Redux Toolkit / Zustand",
  "api": "Axios / React Query"
}
```

**Key Components**:
```
src/
├── components/
│   ├── ChatBot/          # Chat interface
│   ├── Dashboard/        # Main dashboard
│   ├── ChartRenderer/    # Dynamic chart rendering
│   └── DataTable/        # Data display
├── services/
│   └── lidaApi.js        # LIDA API client
└── hooks/
    └── useLida.js        # LIDA integration hook
```

---

### 2. LIDA Service (Backend)

**Location**: `backend/lida-service/`

**Purpose**: 
- Convert natural language to SQL
- Generate appropriate visualizations
- Execute queries and return data

**Tech Stack**:
```python
# Core
lida-python==0.0.10  # Main LIDA library
fastapi==0.104.0     # API framework
uvicorn==0.24.0      # ASGI server

# LLM Integration
openai==1.3.0
anthropic==0.7.0

# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9  # PostgreSQL
pymysql==1.1.0          # MySQL

# Data Processing
pandas==2.1.3
numpy==1.26.2

# Visualization
matplotlib==3.8.2
altair==5.1.2
```

**API Endpoints**:
```python
POST /api/summarize      # Analyze dataset
POST /api/query          # Natural language query
POST /api/visualize      # Generate visualization
POST /api/execute        # Execute SQL
GET  /api/goals          # Get visualization goals
```

---

### 3. Database

**Options**:

#### Option A: PostgreSQL (Recommended)
```yaml
Service: Azure Database for PostgreSQL
Features:
  - Full SQL support
  - JSON support for flexible schemas
  - Good performance
  - Built-in backup
```

#### Option B: MySQL
```yaml
Service: Azure Database for MySQL
Features:
  - Wide compatibility
  - Good for relational data
  - Cost-effective
```

#### Option C: Demo/Development
```yaml
Service: SQLite
Features:
  - No setup required
  - File-based
  - Perfect for testing
```

---

## 🚀 Implementation Steps

### Phase 1: Backend Setup (LIDA Service)

#### Step 1: Create LIDA Service Structure
```bash
cd /path/to/Amadeus
mkdir -p backend/lida-service
cd backend/lida-service
```

#### Step 2: Install LIDA
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install LIDA and dependencies
pip install lida-python
pip install fastapi uvicorn
pip install openai anthropic
pip install sqlalchemy psycopg2-binary
pip install pandas numpy matplotlib altair
```

#### Step 3: Create API Service

**File: `backend/lida-service/main.py`**
```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from lida import Manager, TextGenerationConfig
import os

app = FastAPI(title="LIDA NL2Vis Service")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LIDA
lida = Manager(text_gen=TextGenerationConfig(
    model="gpt-4",
    api_key=os.getenv("OPENAI_API_KEY")
))

class QueryRequest(BaseModel):
    query: str
    data_source: str  # Database connection string or file path

class VisualizationRequest(BaseModel):
    summary: dict
    goal: str

@app.post("/api/summarize")
async def summarize_data(request: QueryRequest):
    """Analyze and summarize the dataset"""
    try:
        summary = lida.summarize(request.data_source)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query")
async def natural_language_query(request: QueryRequest):
    """Convert NL query to SQL and visualization"""
    try:
        # 1. Summarize data
        summary = lida.summarize(request.data_source)
        
        # 2. Generate goals (visualization suggestions)
        goals = lida.goals(summary, n=5, persona="data analyst")
        
        # 3. Generate visualization for the query
        charts = lida.visualize(
            summary=summary,
            goal=request.query,
            library="matplotlib"  # or "altair", "seaborn"
        )
        
        return {
            "summary": summary,
            "goals": goals,
            "charts": charts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/visualize")
async def generate_visualization(request: VisualizationRequest):
    """Generate specific visualization"""
    try:
        charts = lida.visualize(
            summary=request.summary,
            goal=request.goal,
            library="altair"
        )
        return {"charts": charts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### Step 4: Database Integration

**File: `backend/lida-service/database.py`**
```python
from sqlalchemy import create_engine, text
import pandas as pd
import os

class DatabaseManager:
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string or os.getenv("DATABASE_URL")
        self.engine = create_engine(self.connection_string)
    
    def execute_query(self, sql: str) -> pd.DataFrame:
        """Execute SQL query and return DataFrame"""
        with self.engine.connect() as conn:
            result = conn.execute(text(sql))
            return pd.DataFrame(result.fetchall())
    
    def get_table_summary(self, table_name: str) -> dict:
        """Get table schema and sample data"""
        schema_query = f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
        """
        schema = self.execute_query(schema_query)
        
        sample_query = f"SELECT * FROM {table_name} LIMIT 5"
        sample = self.execute_query(sample_query)
        
        return {
            "schema": schema.to_dict(),
            "sample": sample.to_dict(),
            "row_count": self.execute_query(
                f"SELECT COUNT(*) FROM {table_name}"
            ).iloc[0, 0]
        }
```

---

### Phase 2: Frontend Integration

#### Step 1: Update React App Structure

```bash
cd frontend/game-dashboard
npm install axios recharts @mui/material @emotion/react @emotion/styled
```

#### Step 2: Create LIDA API Client

**File: `frontend/game-dashboard/src/services/lidaApi.js`**
```javascript
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_LIDA_API_URL || 'http://localhost:8000';

const lidaApi = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const summarizeData = async (dataSource) => {
  const response = await lidaApi.post('/api/summarize', {
    data_source: dataSource,
  });
  return response.data;
};

export const queryData = async (query, dataSource) => {
  const response = await lidaApi.post('/api/query', {
    query,
    data_source: dataSource,
  });
  return response.data;
};

export const generateVisualization = async (summary, goal) => {
  const response = await lidaApi.post('/api/visualize', {
    summary,
    goal,
  });
  return response.data;
};

export default lidaApi;
```

#### Step 3: Create Chat Interface

**File: `frontend/game-dashboard/src/components/ChatBot.jsx`**
```jsx
import React, { useState } from 'react';
import { Box, TextField, Button, Paper, Typography } from '@mui/material';
import { queryData } from '../services/lidaApi';

const ChatBot = ({ dataSource, onVisualizationGenerated }) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setMessages([...messages, { type: 'user', text: query }]);

    try {
      const result = await queryData(query, dataSource);
      setMessages(prev => [...prev, { 
        type: 'assistant', 
        text: 'Generated visualization based on your query',
        data: result 
      }]);
      onVisualizationGenerated(result);
    } catch (error) {
      setMessages(prev => [...prev, { 
        type: 'error', 
        text: 'Failed to process query: ' + error.message 
      }]);
    } finally {
      setLoading(false);
      setQuery('');
    }
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Paper sx={{ flex: 1, overflow: 'auto', p: 2, mb: 2 }}>
        {messages.map((msg, idx) => (
          <Box
            key={idx}
            sx={{
              mb: 2,
              textAlign: msg.type === 'user' ? 'right' : 'left'
            }}
          >
            <Paper
              sx={{
                display: 'inline-block',
                p: 1,
                bgcolor: msg.type === 'user' ? 'primary.light' : 'grey.100'
              }}
            >
              <Typography>{msg.text}</Typography>
            </Paper>
          </Box>
        ))}
      </Paper>
      
      <form onSubmit={handleSubmit}>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            placeholder="Ask a question about your data..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={loading}
          />
          <Button 
            type="submit" 
            variant="contained" 
            disabled={loading}
          >
            {loading ? 'Processing...' : 'Send'}
          </Button>
        </Box>
      </form>
    </Box>
  );
};

export default ChatBot;
```

#### Step 4: Create Chart Renderer

**File: `frontend/game-dashboard/src/components/ChartRenderer.jsx`**
```jsx
import React from 'react';
import { 
  LineChart, Line, BarChart, Bar, PieChart, Pie, 
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, Cell 
} from 'recharts';
import { Paper, Typography } from '@mui/material';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const ChartRenderer = ({ chartSpec, data }) => {
  if (!chartSpec || !data) return null;

  const renderChart = () => {
    switch (chartSpec.mark) {
      case 'line':
        return (
          <LineChart width={600} height={400} data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={chartSpec.encoding.x.field} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line 
              type="monotone" 
              dataKey={chartSpec.encoding.y.field} 
              stroke="#8884d8" 
            />
          </LineChart>
        );
      
      case 'bar':
        return (
          <BarChart width={600} height={400} data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={chartSpec.encoding.x.field} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar 
              dataKey={chartSpec.encoding.y.field} 
              fill="#8884d8" 
            />
          </BarChart>
        );
      
      case 'pie':
        return (
          <PieChart width={600} height={400}>
            <Pie
              data={data}
              cx={300}
              cy={200}
              labelLine={false}
              label
              outerRadius={80}
              fill="#8884d8"
              dataKey={chartSpec.encoding.theta.field}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        );
      
      default:
        return <Typography>Unsupported chart type</Typography>;
    }
  };

  return (
    <Paper sx={{ p: 2, m: 2 }}>
      <Typography variant="h6" gutterBottom>
        {chartSpec.title || 'Chart'}
      </Typography>
      {renderChart()}
    </Paper>
  );
};

export default ChartRenderer;
```

---

### Phase 3: Kubernetes Deployment

#### Step 1: Dockerize LIDA Service

**File: `backend/lida-service/Dockerfile`**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**File: `backend/lida-service/requirements.txt`**
```
lida-python==0.0.10
fastapi==0.104.0
uvicorn==0.24.0
openai==1.3.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pandas==2.1.3
numpy==1.26.2
matplotlib==3.8.2
altair==5.1.2
```

#### Step 2: Kubernetes Deployment

**File: `backend/lida-service/k8s/deployment.yaml`**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lida-service
  namespace: deep-research
spec:
  replicas: 1
  selector:
    matchLabels:
      app: lida-service
  template:
    metadata:
      labels:
        app: lida-service
    spec:
      containers:
      - name: lida-service
        image: youracr.azurecr.io/lida-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: lida-secrets
              key: OPENAI_API_KEY
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: lida-secrets
              key: DATABASE_URL
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: lida-service
  namespace: deep-research
spec:
  selector:
    app: lida-service
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

---

## 📊 Example Usage Flow

### 1. User asks a question:
```
"Show me the top 5 games by revenue in the last month"
```

### 2. LIDA processes:
```python
# Generated SQL
SELECT game_name, SUM(revenue) as total_revenue
FROM game_transactions
WHERE transaction_date >= DATE_SUB(NOW(), INTERVAL 1 MONTH)
GROUP BY game_name
ORDER BY total_revenue DESC
LIMIT 5
```

### 3. LIDA generates visualization spec:
```json
{
  "mark": "bar",
  "encoding": {
    "x": {"field": "game_name", "type": "nominal"},
    "y": {"field": "total_revenue", "type": "quantitative"}
  },
  "title": "Top 5 Games by Revenue (Last Month)"
}
```

### 4. Frontend renders the chart
Using Recharts based on the spec

---

## 🔐 Security Considerations

1. **SQL Injection Prevention**
   - Use parameterized queries
   - Validate generated SQL
   - Whitelist allowed tables/columns

2. **API Authentication**
   - JWT tokens
   - Rate limiting
   - CORS configuration

3. **Data Privacy**
   - Row-level security
   - Data masking for sensitive fields
   - Audit logs

---

## 🚀 Quick Start Commands

```bash
# 1. Start LIDA backend
cd backend/lida-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# 2. Start React frontend
cd frontend/game-dashboard
npm install
npm start

# 3. Access
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## 📈 Roadmap

- [ ] Phase 1: Basic LIDA integration
- [ ] Phase 2: React UI with charts
- [ ] Phase 3: Database connection
- [ ] Phase 4: Kubernetes deployment
- [ ] Phase 5: Advanced features (caching, history, export)

---

## 📚 Resources

- **LIDA Documentation**: https://github.com/microsoft/lida
- **LIDA Paper**: https://arxiv.org/abs/2303.02927
- **Recharts**: https://recharts.org/
- **FastAPI**: https://fastapi.tiangolo.com/

---

**Created**: 2024-11-24  
**Status**: Architecture Planning  
**Next**: Implement Phase 1

