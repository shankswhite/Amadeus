"""
RAG Service - FastAPI Application
Provides API endpoints for the LangGraph RAG workflow
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn

from workflow import run_workflow
from utils.database import get_available_filters, get_metrics_data

# Initialize FastAPI app
app = FastAPI(
    title="RAG Analysis Service",
    description="LangGraph-based RAG service for game analytics",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class AnalysisRequest(BaseModel):
    question: str
    title: str = "bo6_wz2"
    season: str = "Season 3"
    week: int = 1
    enable_rag: bool = True


class AnalysisResponse(BaseModel):
    success: bool
    question: str
    analysis: str
    chart_type: str
    chart_title: str
    echarts_option: Dict[str, Any]
    sql: str  # Alias for frontend compatibility
    sql_query: str
    data: List[Dict[str, Any]]  # Alias for frontend compatibility
    sql_result: List[Dict[str, Any]]
    python_code: str
    explanation: str  # Alias for frontend compatibility
    final_explanation: str
    references: List[str]
    error: Optional[str] = None


class FiltersResponse(BaseModel):
    titles: List[str]
    seasons: List[str]
    weeks: List[int]


class MetricsRequest(BaseModel):
    title: str
    season: str
    week: Optional[int] = None
    metric_name: Optional[str] = None
    is_outlier: Optional[bool] = None


# Endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "RAG Analysis Service"}


@app.get("/filters", response_model=FiltersResponse)
async def get_filters():
    """Get available filter options for dropdowns"""
    try:
        filters = get_available_filters()
        return FiltersResponse(**filters)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/metrics")
async def get_metrics(request: MetricsRequest):
    """Get metrics data with filters"""
    try:
        data = get_metrics_data(
            title=request.title,
            season=request.season,
            week=request.week,
            metric_name=request.metric_name,
            is_outlier=request.is_outlier
        )
        return {"success": True, "data": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    """Run the full RAG analysis workflow"""
    try:
        result = await run_workflow(
            question=request.question,
            title=request.title,
            season=request.season,
            week=request.week,
            enable_rag=request.enable_rag
        )
        
        sql_query = result.get("sql_query", "")
        sql_result = result.get("sql_result", [])
        final_explanation = result.get("final_explanation", "")
        
        return AnalysisResponse(
            success=True,
            question=request.question,
            analysis=result.get("analysis", ""),
            chart_type=result.get("chart_type", "bar"),
            chart_title=result.get("chart_title", ""),
            echarts_option=result.get("echarts_option", {}),
            sql=sql_query,  # Frontend alias
            sql_query=sql_query,
            data=sql_result,  # Frontend alias
            sql_result=sql_result,
            python_code=result.get("python_code", ""),
            explanation=final_explanation,  # Frontend alias
            final_explanation=final_explanation,
            references=result.get("references", [])
        )
    
    except Exception as e:
        print(f"Error in analyze: {e}")
        import traceback
        traceback.print_exc()
        return AnalysisResponse(
            success=False,
            question=request.question,
            analysis="",
            chart_type="bar",
            chart_title="",
            echarts_option={},
            sql="",
            sql_query="",
            data=[],
            sql_result=[],
            python_code="",
            explanation="",
            final_explanation="",
            references=[],
            error=str(e)
        )


@app.post("/chat")
async def chat(request: AnalysisRequest):
    """Simplified chat endpoint - returns just the explanation and chart"""
    try:
        result = await run_workflow(
            question=request.question,
            title=request.title,
            season=request.season,
            week=request.week,
            enable_rag=request.enable_rag
        )
        
        return {
            "success": True,
            "message": result.get("final_explanation", ""),
            "chart": result.get("echarts_option", {}),
            "sql": result.get("sql_query", ""),
            "references": result.get("references", [])
        }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "chart": {},
            "sql": "",
            "references": []
        }


if __name__ == "__main__":
    print("🚀 Starting RAG Analysis Service...")
    print("📍 API docs: http://localhost:8080/docs")
    uvicorn.run(app, host="0.0.0.0", port=8080)

