"""
Node 1: RAG Retrieval + Analysis
- Retrieve relevant document chunks from pgvector using vector similarity search (LlamaIndex style)
- Get metrics data
- Analyze the question with LLM
"""
from typing import Dict, Any
from state import WorkflowState
from utils.database import (
    get_metrics_data,
    get_report_metadata,
    get_report_content_from_storage,
    vector_search_chunks
)
from utils.llm import get_embedding, chat_completion, analyze_question
from config import config


def rag_analysis_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Node 1: RAG Retrieval + Analysis (with Chunk-based Vector Search)
    
    Uses LlamaIndex-style document chunking for better retrieval.
    
    Input: question, title, season, week, enable_rag
    Output: analysis, key_metrics, key_segments, rag_references, rag_context
    """
    print(f"[Node 1] Starting RAG analysis for: {state.get('question', '')[:50]}...")
    
    question = state.get("question", "")
    title = state.get("title", "bo6_wz2")
    season = state.get("season", "Season 3")
    week = state.get("week", 1)
    enable_rag = state.get("enable_rag", True)
    
    # Step 1: Get metrics data
    print(f"[Node 1] Fetching metrics for {title} {season} Week {week}...")
    metrics = get_metrics_data(title, season, week)
    
    # Format metrics as context
    metrics_context = format_metrics_context(metrics)
    
    # Step 2: Get relevant chunks using RAG (Chunk-based Vector Search)
    rag_context = ""
    rag_references = []
    
    if enable_rag:
        print("[Node 1] RAG enabled, performing chunk-based vector search...")
        
        # Generate embedding for the question
        question_embedding = get_embedding(question)
        print(f"[Node 1] Question embedding generated ({len(question_embedding)} dims)")
        
        # Vector search for similar chunks
        similar_chunks = vector_search_chunks(
            query_embedding=question_embedding,
            title=title,
            season=season,
            top_k=config.TOP_K_RESULTS * 2  # Get more chunks since they're smaller
        )
        
        print(f"[Node 1] Found {len(similar_chunks)} similar chunks via vector search")
        
        # Build context from chunks
        seen_docs = set()  # Track unique documents
        
        for chunk in similar_chunks:
            similarity = chunk.get("similarity", 0)
            doc_key = f"{chunk.get('source')}_{chunk.get('title')}_{chunk.get('season')}_{chunk.get('week')}"
            
            print(f"[Node 1]   → [{chunk.get('source')}] {chunk.get('title')} {chunk.get('season')} W{chunk.get('week')} chunk#{chunk.get('chunk_index')} (sim: {similarity:.3f})")
            
            # Add chunk content to context
            content = chunk.get("content", "")
            if content:
                rag_context += f"\n\n--- [{chunk.get('source')}] {chunk.get('title')} {chunk.get('season')} Week {chunk.get('week')} (chunk {chunk.get('chunk_index')}/{chunk.get('total_chunks')}, similarity: {similarity:.2f}) ---\n{content}"
            
            # Track unique documents for references
            if doc_key not in seen_docs:
                seen_docs.add(doc_key)
                rag_references.append({
                    "source": chunk.get("source", "unknown"),
                    "title": chunk.get("title", ""),
                    "season": chunk.get("season", ""),
                    "week": chunk.get("week", 0),
                    "similarity": similarity,
                    "chunks_used": 1
                })
            else:
                # Update chunks_used count
                for ref in rag_references:
                    if f"{ref['source']}_{ref['title']}_{ref['season']}_{ref['week']}" == doc_key:
                        ref["chunks_used"] = ref.get("chunks_used", 0) + 1
                        break
        
        print(f"[Node 1] Retrieved {len(rag_references)} unique documents ({len(similar_chunks)} chunks) with RAG")
    
    # Step 3: Analyze question with LLM
    print("[Node 1] Analyzing question with LLM...")
    
    full_context = f"""
## Metrics Data
{metrics_context}

## Report Context
{rag_context if enable_rag else "(RAG disabled)"}
"""
    
    analysis_result = analyze_question(question, full_context)
    
    # Step 4: Generate detailed analysis
    analysis = generate_analysis(question, metrics_context, rag_context, enable_rag)
    
    return {
        "analysis": analysis,
        "key_metrics": analysis_result.get("key_metrics", []),
        "key_segments": analysis_result.get("key_segments", []),
        "rag_references": rag_references,
        "rag_context": rag_context
    }


def format_metrics_context(metrics: list) -> str:
    """Format metrics data as readable context"""
    if not metrics:
        return "No metrics data available."
    
    lines = ["| Metric | Segment | Current | Previous | Delta | Outlier |"]
    lines.append("|--------|---------|---------|----------|-------|---------|")
    
    for m in metrics[:20]:  # Limit to top 20
        segment = m.get("segment_combo") or "Overall"
        current = f"{m.get('value_current', 0)/1e6:.1f}M" if m.get('value_current') else "-"
        previous = f"{m.get('value_previous', 0)/1e6:.1f}M" if m.get('value_previous') else "-"
        delta = f"{m.get('value_delta', 0)/1e6:+.1f}M" if m.get('value_delta') else "-"
        outlier = "✓" if m.get("is_outlier") else ""
        
        lines.append(f"| {m.get('metric_name', '-')} | {segment} | {current} | {previous} | {delta} | {outlier} |")
    
    return "\n".join(lines)


def generate_analysis(question: str, metrics_context: str, rag_context: str, enable_rag: bool) -> str:
    """Generate analysis using LLM"""
    system_prompt = """You are a game analytics expert. Analyze the user's question using the provided data and reports.

Provide a clear, structured analysis that:
1. Directly answers the question
2. Cites specific data points from the metrics
3. References report insights (if RAG is enabled)
4. Identifies key drivers and patterns

Keep the response concise but comprehensive."""

    user_content = f"""Question: {question}

## Metrics Data
{metrics_context}

## Report Context
{rag_context if enable_rag else "(RAG disabled - using only metrics data)"}

Please analyze and answer the question."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    
    return chat_completion(messages, temperature=0.5, max_tokens=1500)

