"""
LangGraph Workflow Definition
4-node pipeline: RAG Analysis → Chart Decision → SQL Generation → Explanation
"""
from langgraph.graph import StateGraph, END
from state import WorkflowState
from nodes import (
    rag_analysis_node,
    chart_decision_node,
    sql_generation_node,
    explanation_node
)


def create_workflow():
    """Create the LangGraph workflow"""
    
    # Initialize workflow with state type
    workflow = StateGraph(WorkflowState)
    
    # Add nodes
    workflow.add_node("rag_analysis", rag_analysis_node)
    workflow.add_node("chart_decision", chart_decision_node)
    workflow.add_node("sql_generation", sql_generation_node)
    workflow.add_node("explanation", explanation_node)
    
    # Set entry point
    workflow.set_entry_point("rag_analysis")
    
    # Define edges (linear flow)
    workflow.add_edge("rag_analysis", "chart_decision")
    workflow.add_edge("chart_decision", "sql_generation")
    workflow.add_edge("sql_generation", "explanation")
    workflow.add_edge("explanation", END)
    
    # Compile workflow
    app = workflow.compile()
    
    return app


# Create singleton workflow instance
workflow_app = create_workflow()


async def run_workflow(
    question: str,
    title: str = "bo6_wz2",
    season: str = "Season 3",
    week: int = 1,
    enable_rag: bool = True
) -> dict:
    """Run the workflow with given inputs"""
    
    initial_state = {
        "question": question,
        "title": title,
        "season": season,
        "week": week,
        "enable_rag": enable_rag
    }
    
    print(f"\n{'='*60}")
    print(f"🚀 Starting workflow: {question[:50]}...")
    print(f"   Context: {title} {season} Week {week}")
    print(f"   RAG: {'enabled' if enable_rag else 'disabled'}")
    print(f"{'='*60}\n")
    
    # Run workflow
    result = workflow_app.invoke(initial_state)
    
    print(f"\n{'='*60}")
    print("✅ Workflow completed")
    print(f"{'='*60}\n")
    
    return result


# Test function
if __name__ == "__main__":
    import asyncio
    
    async def test():
        result = await run_workflow(
            question="Why did BR hours increase so much this week?",
            title="bo6_wz2",
            season="Season 3",
            week=1,
            enable_rag=True
        )
        
        print("\n📊 Final Explanation:")
        print(result.get("final_explanation", "No explanation generated"))
        
        print("\n📈 ECharts Config:")
        print(result.get("echarts_option", {}))
    
    asyncio.run(test())

