#!/usr/bin/env python3
"""
Generate embeddings for all reports and store in pgvector
"""
import sys
sys.path.insert(0, '.')

from utils.llm import get_embedding
from utils.database import execute_sql_json, get_report_content_from_storage
import subprocess
import json


def get_all_reports():
    """Get all reports that need embeddings"""
    origin = execute_sql_json("""
        SELECT id, title, season, week, storage_path, summary 
        FROM report_origin 
        WHERE embedding IS NULL
    """)
    
    deep = execute_sql_json("""
        SELECT id, title, season, week, storage_path, summary 
        FROM report_deep_research 
        WHERE embedding IS NULL
    """)
    
    return {"origin": origin, "deep": deep}


def update_embedding(table: str, report_id: int, embedding: list):
    """Update embedding in database via SSH"""
    # Format embedding as PostgreSQL array
    embedding_str = "[" + ",".join(map(str, embedding)) + "]"
    
    sql = f"UPDATE {table} SET embedding = '{embedding_str}'::vector WHERE id = {report_id}"
    
    cmd = [
        'ssh', '-o', 'StrictHostKeyChecking=no',
        'azureuser@4.155.228.61',
        f'docker exec supabase-db psql -U supabase_admin -d postgres -c "{sql}"'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result.returncode == 0


def generate_and_store_embeddings():
    """Main function to generate embeddings for all reports"""
    print("🚀 Generating embeddings for reports...")
    
    reports = get_all_reports()
    
    # Process report_origin
    print(f"\n📄 Processing {len(reports['origin'])} origin reports...")
    for report in reports['origin']:
        print(f"  → {report['title']} {report['season']} Week {report['week']}")
        
        # Get content - use summary if full content not available
        content = report.get('summary', '')
        if report.get('storage_path'):
            full_content = get_report_content_from_storage(report['storage_path'])
            if full_content:
                content = full_content
        
        if not content:
            print(f"    ⚠️ No content, skipping")
            continue
        
        # Generate embedding
        try:
            embedding = get_embedding(content[:8000])  # Limit to 8000 chars
            print(f"    ✅ Generated embedding ({len(embedding)} dims)")
            
            # Store in database
            if update_embedding("report_origin", report['id'], embedding):
                print(f"    ✅ Stored in database")
            else:
                print(f"    ❌ Failed to store")
                
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    # Process report_deep_research
    print(f"\n📄 Processing {len(reports['deep'])} deep research reports...")
    for report in reports['deep']:
        print(f"  → {report['title']} {report['season']} Week {report['week']}")
        
        content = report.get('summary', '')
        if report.get('storage_path'):
            full_content = get_report_content_from_storage(report['storage_path'])
            if full_content:
                content = full_content
        
        if not content:
            print(f"    ⚠️ No content, skipping")
            continue
        
        try:
            embedding = get_embedding(content[:8000])
            print(f"    ✅ Generated embedding ({len(embedding)} dims)")
            
            if update_embedding("report_deep_research", report['id'], embedding):
                print(f"    ✅ Stored in database")
            else:
                print(f"    ❌ Failed to store")
                
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    print("\n✅ Embedding generation complete!")
    
    # Verify
    print("\n🔍 Verification:")
    origin_count = execute_sql_json("SELECT COUNT(*) as count FROM report_origin WHERE embedding IS NOT NULL")
    deep_count = execute_sql_json("SELECT COUNT(*) as count FROM report_deep_research WHERE embedding IS NOT NULL")
    
    print(f"   report_origin with embeddings: {origin_count[0]['count'] if origin_count else 0}")
    print(f"   report_deep_research with embeddings: {deep_count[0]['count'] if deep_count else 0}")


if __name__ == "__main__":
    generate_and_store_embeddings()

