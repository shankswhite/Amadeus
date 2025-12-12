"""
LLM and Embedding utilities using Azure OpenAI and Azure AI Services (Cohere)
"""
from openai import AzureOpenAI
from typing import List
import httpx
from config import config


# Initialize Azure OpenAI client (for LLM)
client = AzureOpenAI(
    azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
    api_key=config.AZURE_OPENAI_API_KEY,
    api_version=config.AZURE_OPENAI_API_VERSION
)


def get_embedding(text: str) -> List[float]:
    """Get embedding vector using Cohere-embed-v3-english via Azure AI Services"""
    try:
        url = f"{config.AZURE_AI_ENDPOINT}/openai/v1/embeddings"
        headers = {
            "api-key": config.AZURE_AI_API_KEY,
            "Content-Type": "application/json"
        }
        data = {
            "input": [text],  # Cohere requires list format
            "model": config.EMBEDDING_MODEL
        }
        
        response = httpx.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result["data"][0]["embedding"]
        
    except Exception as e:
        print(f"Warning: Embedding error ({e}). Using placeholder.")
        # Return placeholder embedding (not for production use)
        import hashlib
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        return [(hash_val >> i) % 1000 / 1000 for i in range(config.EMBEDDING_DIMENSION)]


def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Get embeddings for multiple texts in one API call"""
    try:
        url = f"{config.AZURE_AI_ENDPOINT}/openai/v1/embeddings"
        headers = {
            "api-key": config.AZURE_AI_API_KEY,
            "Content-Type": "application/json"
        }
        data = {
            "input": texts,
            "model": config.EMBEDDING_MODEL
        }
        
        response = httpx.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        return [item["embedding"] for item in result["data"]]
        
    except Exception as e:
        print(f"Batch embedding error: {e}")
        return [get_embedding(text) for text in texts]


def chat_completion(
    messages: List[dict],
    temperature: float = 0.7,
    max_tokens: int = 2000
) -> str:
    """Get chat completion from Azure OpenAI"""
    response = client.chat.completions.create(
        model=config.AZURE_OPENAI_DEPLOYMENT,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content


def analyze_question(question: str, context: str = "") -> dict:
    """Analyze user question to extract intent and key elements"""
    system_prompt = """You are a data analyst assistant. Analyze the user's question and extract:
1. The main intent (e.g., "explain growth", "compare metrics", "identify anomalies")
2. Key metrics mentioned or implied (e.g., "br_hours", "dau")
3. Key segments mentioned (e.g., "Premium", "BR Main", "Dolphins")
4. Time context (e.g., "this week", "compared to last week")

Respond in JSON format:
{
    "intent": "string",
    "key_metrics": ["list", "of", "metrics"],
    "key_segments": ["list", "of", "segments"],
    "time_context": "string"
}"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Question: {question}\n\nContext: {context}"}
    ]
    
    response = chat_completion(messages, temperature=0.3, max_tokens=500)
    
    # Parse JSON response
    import json
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return {
            "intent": "unknown",
            "key_metrics": [],
            "key_segments": [],
            "time_context": ""
        }

