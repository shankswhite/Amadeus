"""
Database utilities for Supabase/PostgreSQL
- In Kubernetes: Direct PostgreSQL connection
- In Local: SSH remote execution to access PostgreSQL inside Docker container
"""
import subprocess
import json
import os
from typing import List, Dict, Any, Optional
import httpx
from config import config

# Check if running in Kubernetes
IN_KUBERNETES = os.environ.get("IN_KUBERNETES", "false").lower() == "true"

# PostgreSQL connection (for Kubernetes)
_pg_conn = None

def get_pg_connection():
    """Get PostgreSQL connection (for Kubernetes environment)"""
    global _pg_conn
    if _pg_conn is None:
        import psycopg2
        _pg_conn = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", config.PG_HOST),
            port=int(os.environ.get("POSTGRES_PORT", config.PG_PORT)),
            user=os.environ.get("POSTGRES_USER", config.PG_USER),
            password=os.environ.get("POSTGRES_PASSWORD", config.PG_PASSWORD),
            database=os.environ.get("POSTGRES_DB", config.PG_DATABASE)
        )
        _pg_conn.autocommit = True
    return _pg_conn


def execute_sql_direct(sql: str) -> List[Dict[str, Any]]:
    """Execute SQL directly (Kubernetes environment)"""
    try:
        conn = get_pg_connection()
        cursor = conn.cursor()
        
        # Wrap in JSON aggregation
        sql_clean = ' '.join(sql.split())
        json_sql = f"SELECT json_agg(row_to_json(t))::text FROM ({sql_clean}) t"
        
        cursor.execute(json_sql)
        result = cursor.fetchone()
        cursor.close()
        
        if result and result[0]:
            return json.loads(result[0])
        return []
    except Exception as e:
        print(f"SQL error (direct): {e}")
        global _pg_conn
        _pg_conn = None  # Reset connection on error
        return []


def execute_sql_via_ssh(sql: str) -> List[Dict[str, Any]]:
    """Execute SQL via SSH to Supabase VM Docker container (local environment)"""
    
    # Escape single quotes in SQL
    sql_escaped = sql.replace("'", "'\"'\"'")
    
    # Build SSH command
    cmd = f'''ssh -o StrictHostKeyChecking=no azureuser@4.155.228.61 "docker exec supabase-db psql -U supabase_admin -d postgres -t -A -F'|||' -c '{sql_escaped}'"'''
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"SQL Error: {result.stderr}")
            return []
        
        # Parse output
        output = result.stdout.strip()
        if not output:
            return []
        
        rows = []
        for line in output.split('\n'):
            if line.strip():
                rows.append({"raw": line})
        
        return rows
        
    except subprocess.TimeoutExpired:
        print("SQL timeout")
        return []
    except Exception as e:
        print(f"SQL error: {e}")
        return []


def execute_sql_json(sql: str) -> List[Dict[str, Any]]:
    """Execute SQL and return JSON results"""
    
    # Use direct connection in Kubernetes
    if IN_KUBERNETES:
        return execute_sql_direct(sql)
    
    # Otherwise use SSH for local development
    # Clean up SQL - replace newlines with spaces
    sql_clean = ' '.join(sql.split())
    
    # Wrap SQL in JSON aggregation
    json_sql = f"SELECT json_agg(row_to_json(t))::text FROM ({sql_clean}) t"
    
    # Build SSH command - use double quotes for outer, escape inner quotes
    cmd = [
        'ssh', '-o', 'StrictHostKeyChecking=no',
        'azureuser@4.155.228.61',
        f'docker exec supabase-db psql -U supabase_admin -d postgres -t -A -c "{json_sql}"'
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"SQL Error: {result.stderr}")
            return []
        
        output = result.stdout.strip()
        if not output or output == 'null':
            return []
        
        # Parse JSON
        data = json.loads(output)
        return data if data else []
        
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Raw output: {result.stdout[:200] if result else 'no output'}")
        return []
    except subprocess.TimeoutExpired:
        print("SQL timeout")
        return []
    except Exception as e:
        print(f"SQL error: {e}")
        return []


def execute_sql(sql: str, params: tuple = None) -> List[Dict[str, Any]]:
    """Execute SQL and return results as list of dicts"""
    # Replace parameters
    if params:
        for param in params:
            if isinstance(param, str):
                sql = sql.replace('%s', f"'{param}'", 1)
            else:
                sql = sql.replace('%s', str(param), 1)
    
    return execute_sql_json(sql)


def get_metrics_data(
    title: str,
    season: str,
    week: Optional[int] = None,
    metric_name: Optional[str] = None,
    data_type: Optional[str] = None,
    is_outlier: Optional[bool] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Get metrics data with filters"""
    # Use single quotes for SQL strings
    conditions = [f"title = '{title}'", f"season = '{season}'"]
    
    if week is not None:
        conditions.append(f"week_number = {week}")
    
    if metric_name:
        conditions.append(f"metric_name = '{metric_name}'")
    
    if data_type:
        conditions.append(f"data_type = '{data_type}'")
    
    if is_outlier is not None:
        conditions.append(f"is_outlier = {str(is_outlier).lower()}")
    
    sql = f"""
        SELECT * FROM metrics_data
        WHERE {' AND '.join(conditions)}
        ORDER BY week_number, contribution_rank_positive NULLS LAST
        LIMIT {limit}
    """
    
    return execute_sql_json(sql)


def get_report_metadata(
    title: str,
    season: str,
    week: Optional[int] = None,
    report_type: str = "origin"
) -> List[Dict[str, Any]]:
    """Get report metadata"""
    table = "report_origin" if report_type == "origin" else "report_deep_research"
    
    # Use single quotes for SQL strings
    conditions = [f"title = '{title}'", f"season = '{season}'"]
    
    if week is not None:
        conditions.append(f"week = {week}")
    
    sql = f"""
        SELECT id, title, season, week, storage_path, summary, content_length
        FROM {table}
        WHERE {' AND '.join(conditions)}
        ORDER BY week
    """
    
    return execute_sql_json(sql)


def get_report_content_from_storage(storage_path: str) -> Optional[str]:
    """Get report content from Supabase Storage"""
    try:
        headers = {
            "apikey": config.SUPABASE_KEY,
            "Authorization": f"Bearer {config.SUPABASE_KEY}"
        }
        
        # Extract filename from path
        filename = storage_path.split("/")[-1]
        url = f"{config.SUPABASE_URL}/storage/v1/object/reports/{filename}"
        
        response = httpx.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Storage error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching from storage: {e}")
        return None


def get_available_filters() -> Dict[str, List[Any]]:
    """Get available filter values for dropdowns"""
    titles = execute_sql_json("SELECT DISTINCT title FROM metrics_data ORDER BY title")
    seasons = execute_sql_json("SELECT DISTINCT season FROM metrics_data ORDER BY season")
    weeks = execute_sql_json("SELECT DISTINCT week_number FROM metrics_data ORDER BY week_number")
    
    return {
        "titles": [r.get("title") for r in titles if r.get("title")],
        "seasons": [r.get("season") for r in seasons if r.get("season")],
        "weeks": [r.get("week_number") for r in weeks if r.get("week_number")]
    }


def vector_search_reports(
    query_embedding: List[float],
    title: Optional[str] = None,
    season: Optional[str] = None,
    top_k: int = 3
) -> List[Dict[str, Any]]:
    """Search similar reports using pgvector cosine similarity (legacy - full documents)"""
    
    # Format embedding as PostgreSQL array
    embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
    
    # Build WHERE conditions
    conditions = ["embedding IS NOT NULL"]
    if title:
        conditions.append(f"title = '{title}'")
    if season:
        conditions.append(f"season = '{season}'")
    
    where_clause = " AND ".join(conditions)
    
    # Search in both tables and combine results
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
    
    return execute_sql_json(sql)


def vector_search_chunks(
    query_embedding: List[float],
    title: Optional[str] = None,
    season: Optional[str] = None,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """Search similar document chunks using pgvector cosine similarity (LlamaIndex style)"""
    
    # Format embedding as PostgreSQL array
    embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
    
    # Build WHERE conditions
    conditions = ["embedding IS NOT NULL"]
    if title:
        conditions.append(f"title = '{title}'")
    if season:
        conditions.append(f"season = '{season}'")
    
    where_clause = " AND ".join(conditions)
    
    sql = f"""
        SELECT 
            source,
            report_id,
            title,
            season,
            week,
            chunk_index,
            total_chunks,
            content,
            1 - (embedding <=> '{embedding_str}'::vector) as similarity
        FROM document_chunks
        WHERE {where_clause}
        ORDER BY embedding <=> '{embedding_str}'::vector
        LIMIT {top_k}
    """
    
    return execute_sql_json(sql)


# Test function
if __name__ == "__main__":
    print("Testing database connection...")
    
    # Test metrics
    metrics = get_metrics_data("bo6_wz2", "Season 3", 1)
    print(f"Metrics: {len(metrics)} rows")
    if metrics:
        print(f"Sample: {metrics[0]}")
    
    # Test reports
    reports = get_report_metadata("bo6_wz2", "Season 3", 1)
    print(f"Reports: {len(reports)} rows")
    if reports:
        print(f"Sample: {reports[0]}")
    
    # Test filters
    filters = get_available_filters()
    print(f"Filters: {filters}")
