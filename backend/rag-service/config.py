"""
RAG Service Configuration
"""
import os
from dataclasses import dataclass

@dataclass
class Config:
    # Azure OpenAI (for LLM)
    AZURE_OPENAI_ENDPOINT: str = os.environ.get(
        "AZURE_OPENAI_ENDPOINT", 
        "https://amadeus-ai-analyst.cognitiveservices.azure.com/"
    )
    AZURE_OPENAI_API_KEY: str = os.environ.get(
        "AZURE_OPENAI_API_KEY",
        "DMXvkbbTS5ZsC6m8yzfmAo8cALObxEoke6pjS7ZSeQBXyIWlx7WgJQQJ99BLACYeBjFXJ3w3AAAAACOGS3T5"
    )
    AZURE_OPENAI_API_VERSION: str = os.environ.get(
        "AZURE_OPENAI_API_VERSION",
        "2024-12-01-preview"
    )
    AZURE_OPENAI_DEPLOYMENT: str = os.environ.get(
        "AZURE_OPENAI_DEPLOYMENT",
        "gpt-4o"
    )
    
    # Azure AI Services (for Embedding - Cohere)
    AZURE_AI_ENDPOINT: str = os.environ.get(
        "AZURE_AI_ENDPOINT",
        "https://amadeus-ai-analyst.services.ai.azure.com"
    )
    AZURE_AI_API_KEY: str = os.environ.get(
        "AZURE_AI_API_KEY",
        "DMXvkbbTS5ZsC6m8yzfmAo8cALObxEoke6pjS7ZSeQBXyIWlx7WgJQQJ99BLACYeBjFXJ3w3AAAAACOGS3T5"
    )
    EMBEDDING_MODEL: str = os.environ.get(
        "EMBEDDING_MODEL",
        "Cohere-embed-v3-english"
    )
    
    # Supabase
    SUPABASE_URL: str = os.environ.get(
        "SUPABASE_URL",
        "http://4.155.228.61:8000"
    )
    SUPABASE_KEY: str = os.environ.get(
        "SUPABASE_KEY",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UiLCJpYXQiOjE3NjM3NjkwNTEsImV4cCI6MjA3OTEyOTA1MX0.Lo5Uda5J4r2WvIO0tLG1fGGAf08r6sP5efw11sc-aW4"
    )
    
    # PostgreSQL (via SSH tunnel for local dev)
    PG_HOST: str = os.environ.get("PG_HOST", "localhost")
    PG_PORT: int = int(os.environ.get("PG_PORT", "5432"))
    PG_USER: str = os.environ.get("PG_USER", "supabase_admin")
    PG_PASSWORD: str = os.environ.get(
        "PG_PASSWORD",
        "xYC7xJsll27MoVxr6Sg0LeaueDut+g0OyYf8nR2TOmY="
    )
    PG_DATABASE: str = os.environ.get("PG_DATABASE", "postgres")
    
    # RAG Settings
    TOP_K_RESULTS: int = 3  # Number of similar documents to retrieve
    EMBEDDING_DIMENSION: int = 1024  # Cohere-embed-v3-english dimension


config = Config()

