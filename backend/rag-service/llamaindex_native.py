"""
Native LlamaIndex RAG Implementation using PGVectorStore
- Uses official LlamaIndex VectorStoreIndex
- Requires SSH tunnel to Supabase PostgreSQL
"""
import os
import subprocess
import time
from typing import List, Optional

from llama_index.core import (
    VectorStoreIndex,
    Document,
    Settings,
    StorageContext
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.embeddings import BaseEmbedding
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.llms.azure_openai import AzureOpenAI
from sqlalchemy import make_url
from pydantic import PrivateAttr

from config import config


# SSH Tunnel Configuration
SSH_USER = "azureuser"
SSH_HOST = "4.155.228.61"
LOCAL_PORT = 54321
DB_CONTAINER_IP = None  # Will be fetched dynamically


def get_db_container_ip() -> str:
    """Get the internal IP of supabase-db container"""
    global DB_CONTAINER_IP
    if DB_CONTAINER_IP:
        return DB_CONTAINER_IP
    
    result = subprocess.run(
        ['ssh', '-o', 'StrictHostKeyChecking=no', f'{SSH_USER}@{SSH_HOST}',
         "docker inspect supabase-db --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'"],
        capture_output=True, text=True, timeout=30
    )
    DB_CONTAINER_IP = result.stdout.strip()
    print(f"[LlamaIndex] supabase-db IP: {DB_CONTAINER_IP}")
    return DB_CONTAINER_IP


def ensure_ssh_tunnel() -> bool:
    """Ensure SSH tunnel to PostgreSQL is established"""
    # Check if tunnel exists
    result = subprocess.run(['lsof', '-i', f':{LOCAL_PORT}'], capture_output=True, text=True)
    if 'ssh' in result.stdout:
        print(f"[LlamaIndex] SSH tunnel already exists on port {LOCAL_PORT}")
        return True
    
    # Get container IP
    db_ip = get_db_container_ip()
    if not db_ip:
        print("[LlamaIndex] ❌ Failed to get DB container IP")
        return False
    
    # Create tunnel
    print(f"[LlamaIndex] Creating SSH tunnel: localhost:{LOCAL_PORT} → {db_ip}:5432")
    subprocess.run(
        ['ssh', '-o', 'StrictHostKeyChecking=no', '-f', '-N', 
         '-L', f'{LOCAL_PORT}:{db_ip}:5432', f'{SSH_USER}@{SSH_HOST}'],
        capture_output=True
    )
    
    time.sleep(2)
    
    # Verify
    result = subprocess.run(['lsof', '-i', f':{LOCAL_PORT}'], capture_output=True, text=True)
    if 'ssh' in result.stdout:
        print(f"[LlamaIndex] ✅ SSH tunnel established")
        return True
    
    print("[LlamaIndex] ❌ Failed to establish SSH tunnel")
    return False


def get_connection_string() -> str:
    """Get PostgreSQL connection string via SSH tunnel"""
    return f"postgresql://supabase_admin:xYC7xJsll27MoVxr6Sg0LeaueDut+g0OyYf8nR2TOmY%3D@127.0.0.1:{LOCAL_PORT}/postgres"


class CohereAzureEmbedding(BaseEmbedding):
    """Custom embedding class that wraps Cohere via Azure AI"""
    
    _endpoint: str = PrivateAttr()
    _api_key: str = PrivateAttr()
    _model: str = PrivateAttr()
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._endpoint = config.AZURE_AI_ENDPOINT
        self._api_key = config.AZURE_AI_API_KEY
        self._model = config.EMBEDDING_MODEL
    
    @classmethod
    def class_name(cls) -> str:
        return "CohereAzureEmbedding"
    
    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        import httpx
        
        url = f"{self._endpoint}/openai/v1/embeddings"
        headers = {
            "api-key": self._api_key,
            "Content-Type": "application/json"
        }
        data = {
            "input": texts,
            "model": self._model
        }
        
        response = httpx.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        return [item["embedding"] for item in result["data"]]
    
    def _get_text_embedding(self, text: str) -> List[float]:
        return self._get_embeddings([text])[0]
    
    def _get_query_embedding(self, query: str) -> List[float]:
        return self._get_text_embedding(query)
    
    async def _aget_text_embedding(self, text: str) -> List[float]:
        return self._get_text_embedding(text)
    
    async def _aget_query_embedding(self, query: str) -> List[float]:
        return self._get_query_embedding(query)


def setup_llamaindex():
    """Configure LlamaIndex settings"""
    # Setup LLM
    Settings.llm = AzureOpenAI(
        deployment_name=config.AZURE_OPENAI_DEPLOYMENT,
        azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
        api_key=config.AZURE_OPENAI_API_KEY,
        api_version=config.AZURE_OPENAI_API_VERSION,
    )
    
    # Setup embedding
    Settings.embed_model = CohereAzureEmbedding()
    
    # Setup text splitter
    Settings.text_splitter = SentenceSplitter(
        chunk_size=512,
        chunk_overlap=50
    )
    
    print("[LlamaIndex] ✅ Settings configured")


def get_vector_store() -> PGVectorStore:
    """Get PGVectorStore instance"""
    ensure_ssh_tunnel()
    
    vector_store = PGVectorStore.from_params(
        database="postgres",
        host="127.0.0.1",
        port=str(LOCAL_PORT),
        user="supabase_admin",
        password="xYC7xJsll27MoVxr6Sg0LeaueDut+g0OyYf8nR2TOmY=",
        table_name="llamaindex_embeddings",
        embed_dim=1024,
    )
    
    print("[LlamaIndex] ✅ PGVectorStore connected")
    return vector_store


class NativeLlamaIndexRAG:
    """Native LlamaIndex RAG using PGVectorStore"""
    
    def __init__(self):
        setup_llamaindex()
        self.vector_store = get_vector_store()
        self.index = None
    
    def load_documents(self, documents: List[Document]) -> VectorStoreIndex:
        """Load documents into the index"""
        storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )
        
        self.index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            show_progress=True
        )
        
        print(f"[LlamaIndex] ✅ Loaded {len(documents)} documents")
        return self.index
    
    def load_from_store(self) -> VectorStoreIndex:
        """Load existing index from vector store"""
        self.index = VectorStoreIndex.from_vector_store(
            self.vector_store
        )
        print("[LlamaIndex] ✅ Loaded existing index")
        return self.index
    
    def query(self, question: str, top_k: int = 5) -> dict:
        """Query the index"""
        if not self.index:
            self.load_from_store()
        
        query_engine = self.index.as_query_engine(
            similarity_top_k=top_k
        )
        
        response = query_engine.query(question)
        
        return {
            "answer": str(response),
            "sources": [
                {
                    "text": node.text[:200],
                    "score": node.score
                }
                for node in response.source_nodes
            ]
        }


# Test
if __name__ == "__main__":
    print("="*60)
    print("🧪 Testing Native LlamaIndex RAG")
    print("="*60)
    
    # Ensure tunnel
    if not ensure_ssh_tunnel():
        print("❌ Cannot proceed without SSH tunnel")
        exit(1)
    
    # Initialize
    rag = NativeLlamaIndexRAG()
    
    # Create test documents
    print("\n📝 Creating test documents...")
    docs = [
        Document(
            text="BR hours increased by 410% in Season 3 Week 1. The main drivers were the new Avalon map release and Double XP weekend event.",
            metadata={"title": "bo6_wz2", "season": "Season 3", "week": 1}
        ),
        Document(
            text="Premium players contributed 67.3% of the BR hours growth. The Dolphins spending segment also showed significant increase.",
            metadata={"title": "bo6_wz2", "season": "Season 3", "week": 1}
        ),
    ]
    
    # Load documents
    print("\n📚 Loading documents into PGVectorStore...")
    rag.load_documents(docs)
    
    # Query
    print("\n❓ Querying: 'Why did BR hours increase?'")
    result = rag.query("Why did BR hours increase?")
    
    print(f"\n📊 Answer: {result['answer'][:500]}...")
    print(f"\n📎 Sources: {len(result['sources'])}")
    for src in result['sources']:
        print(f"   - Score: {src['score']:.3f} | {src['text'][:100]}...")
    
    print("\n✅ Test complete!")

