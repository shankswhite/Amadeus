"""
LlamaIndex RAG Implementation
- Document chunking
- Embedding with Cohere
- Vector search with pgvector
- Query with Azure OpenAI
"""
import os
from typing import List, Optional
from pathlib import Path

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Document,
    Settings,
    StorageContext
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import TextNode
from llama_index.embeddings.cohere import CohereEmbedding
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.vector_stores.postgres import PGVectorStore

from config import config


def setup_llama_index():
    """Configure LlamaIndex with Cohere embedding and Azure OpenAI"""
    
    # Setup Cohere Embedding
    # Note: Cohere embedding via Azure AI needs custom implementation
    # Using direct HTTP calls instead of llama-index-embeddings-cohere
    
    # Setup Azure OpenAI LLM
    Settings.llm = AzureOpenAI(
        deployment_name=config.AZURE_OPENAI_DEPLOYMENT,
        azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
        api_key=config.AZURE_OPENAI_API_KEY,
        api_version=config.AZURE_OPENAI_API_VERSION,
    )
    
    # Setup text splitter for chunking
    Settings.text_splitter = SentenceSplitter(
        chunk_size=512,
        chunk_overlap=50
    )
    
    print("✅ LlamaIndex configured")


class CohereAzureEmbedding:
    """Custom Cohere Embedding via Azure AI Services"""
    
    def __init__(self):
        self.endpoint = config.AZURE_AI_ENDPOINT
        self.api_key = config.AZURE_AI_API_KEY
        self.model = config.EMBEDDING_MODEL
        self.embed_dim = config.EMBEDDING_DIMENSION
    
    def get_text_embedding(self, text: str) -> List[float]:
        """Get embedding for single text"""
        import httpx
        
        url = f"{self.endpoint}/openai/v1/embeddings"
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }
        data = {
            "input": [text],
            "model": self.model
        }
        
        response = httpx.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result["data"][0]["embedding"]
    
    def get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts (batch)"""
        import httpx
        
        url = f"{self.endpoint}/openai/v1/embeddings"
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }
        data = {
            "input": texts,
            "model": self.model
        }
        
        response = httpx.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        return [item["embedding"] for item in result["data"]]


# Global embedding model
embed_model = CohereAzureEmbedding()


def chunk_document(content: str, metadata: dict = None) -> List[TextNode]:
    """
    Chunk a document into smaller pieces using LlamaIndex's SentenceSplitter
    
    Args:
        content: Full document text
        metadata: Document metadata (title, season, week, etc.)
    
    Returns:
        List of TextNode objects with embeddings
    """
    # Create splitter
    splitter = SentenceSplitter(
        chunk_size=512,      # Characters per chunk
        chunk_overlap=50,    # Overlap between chunks
    )
    
    # Split text into chunks
    chunks = splitter.split_text(content)
    
    print(f"  📄 Split into {len(chunks)} chunks")
    
    # Create TextNodes with metadata
    nodes = []
    for i, chunk in enumerate(chunks):
        node = TextNode(
            text=chunk,
            metadata={
                **(metadata or {}),
                "chunk_index": i,
                "total_chunks": len(chunks)
            }
        )
        nodes.append(node)
    
    return nodes


def generate_node_embeddings(nodes: List[TextNode]) -> List[TextNode]:
    """Generate embeddings for all nodes"""
    texts = [node.text for node in nodes]
    
    # Batch embedding
    embeddings = embed_model.get_text_embeddings(texts)
    
    # Assign embeddings to nodes
    for node, embedding in zip(nodes, embeddings):
        node.embedding = embedding
    
    return nodes


class RAGService:
    """
    RAG Service using LlamaIndex
    """
    
    def __init__(self):
        setup_llama_index()
        self.embed_model = embed_model
        self.nodes_cache = {}  # Cache for document nodes
    
    def load_documents_from_db(self, title: str = None, season: str = None):
        """Load and chunk documents from database"""
        from utils.database import execute_sql_json, get_report_content_from_storage
        
        # Build query
        conditions = []
        if title:
            conditions.append(f"title = '{title}'")
        if season:
            conditions.append(f"season = '{season}'")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # Get reports from both tables
        sql = f"""
            SELECT 'origin' as source, id, title, season, week, storage_path, summary
            FROM report_origin WHERE {where_clause}
            UNION ALL
            SELECT 'deep' as source, id, title, season, week, storage_path, summary
            FROM report_deep_research WHERE {where_clause}
        """
        
        reports = execute_sql_json(sql)
        print(f"📚 Loading {len(reports)} reports...")
        
        all_nodes = []
        
        for report in reports:
            # Get content
            content = None
            if report.get("storage_path"):
                content = get_report_content_from_storage(report["storage_path"])
            
            if not content:
                content = report.get("summary", "")
            
            if not content:
                continue
            
            # Chunk document
            metadata = {
                "source": report.get("source"),
                "title": report.get("title"),
                "season": report.get("season"),
                "week": report.get("week"),
                "storage_path": report.get("storage_path", "")
            }
            
            print(f"  → Processing {metadata['source']}: {metadata['title']} {metadata['season']} Week {metadata['week']}")
            nodes = chunk_document(content, metadata)
            
            # Generate embeddings
            nodes = generate_node_embeddings(nodes)
            
            all_nodes.extend(nodes)
        
        print(f"✅ Total nodes: {len(all_nodes)}")
        return all_nodes
    
    def search(
        self,
        query: str,
        title: str = None,
        season: str = None,
        top_k: int = 5
    ) -> List[dict]:
        """
        Search for relevant document chunks
        
        Args:
            query: User's question
            title: Filter by game title
            season: Filter by season
            top_k: Number of results to return
        
        Returns:
            List of relevant chunks with metadata
        """
        # Generate query embedding
        query_embedding = self.embed_model.get_text_embedding(query)
        
        # Search using pgvector
        from utils.database import execute_sql_json
        
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
        
        # Build filter conditions
        conditions = ["embedding IS NOT NULL"]
        if title:
            conditions.append(f"title = '{title}'")
        if season:
            conditions.append(f"season = '{season}'")
        
        where_clause = " AND ".join(conditions)
        
        # Search both tables
        sql = f"""
            SELECT 
                'origin' as source,
                id, title, season, week, storage_path, summary,
                1 - (embedding <=> '{embedding_str}'::vector) as similarity
            FROM report_origin
            WHERE {where_clause}
            
            UNION ALL
            
            SELECT 
                'deep' as source,
                id, title, season, week, storage_path, summary,
                1 - (embedding <=> '{embedding_str}'::vector) as similarity
            FROM report_deep_research
            WHERE {where_clause}
            
            ORDER BY similarity DESC
            LIMIT {top_k}
        """
        
        results = execute_sql_json(sql)
        
        return results
    
    def query(
        self,
        question: str,
        title: str = None,
        season: str = None,
        top_k: int = 3
    ) -> dict:
        """
        Full RAG query: search + generate answer
        
        Args:
            question: User's question
            title: Filter by game title
            season: Filter by season
            top_k: Number of documents to retrieve
        
        Returns:
            dict with answer and sources
        """
        # Search for relevant documents
        search_results = self.search(question, title, season, top_k)
        
        # Build context from search results
        context_parts = []
        sources = []
        
        for result in search_results:
            # Get full content if available
            from utils.database import get_report_content_from_storage
            
            content = None
            if result.get("storage_path"):
                content = get_report_content_from_storage(result["storage_path"])
            
            if not content:
                content = result.get("summary", "")
            
            if content:
                context_parts.append(f"""
--- [{result.get('source')}] {result.get('title')} {result.get('season')} Week {result.get('week')} (similarity: {result.get('similarity', 0):.2f}) ---
{content[:2000]}
""")
                sources.append({
                    "source": result.get("source"),
                    "title": result.get("title"),
                    "season": result.get("season"),
                    "week": result.get("week"),
                    "similarity": result.get("similarity", 0)
                })
        
        context = "\n".join(context_parts)
        
        # Generate answer using LLM
        from utils.llm import chat_completion
        
        system_prompt = """You are a game analytics expert. Answer the user's question based on the provided context from reports.

Be specific and cite data points from the reports. If the context doesn't contain enough information, say so."""
        
        user_prompt = f"""Question: {question}

Context from reports:
{context}

Please answer the question based on the context above."""
        
        answer = chat_completion([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        return {
            "answer": answer,
            "sources": sources,
            "context": context
        }


# Global RAG service instance
rag_service = None


def get_rag_service() -> RAGService:
    """Get or create RAG service singleton"""
    global rag_service
    if rag_service is None:
        rag_service = RAGService()
    return rag_service


# Test
if __name__ == "__main__":
    print("🧪 Testing LlamaIndex RAG...")
    
    service = get_rag_service()
    
    # Test search
    print("\n📝 Testing search...")
    results = service.search(
        query="Why did BR hours increase?",
        title="bo6_wz2",
        season="Season 3",
        top_k=3
    )
    
    print(f"Found {len(results)} results:")
    for r in results:
        print(f"  - [{r.get('source')}] {r.get('title')} {r.get('season')} W{r.get('week')} (sim: {r.get('similarity', 0):.3f})")
    
    # Test full query
    print("\n📝 Testing full query...")
    response = service.query(
        question="Why did BR hours increase so much in Week 1?",
        title="bo6_wz2",
        season="Season 3"
    )
    
    print(f"\nAnswer:\n{response['answer'][:500]}...")
    print(f"\nSources: {len(response['sources'])}")

