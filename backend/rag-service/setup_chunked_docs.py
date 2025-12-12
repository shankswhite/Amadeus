#!/usr/bin/env python3
"""
Setup chunked documents for LlamaIndex RAG
- Create chunks table
- Chunk all documents
- Generate embeddings for chunks
- Store in pgvector
"""
import sys
sys.path.insert(0, '.')

import subprocess
from llamaindex_rag import chunk_document, embed_model
from utils.database import execute_sql_json, get_report_content_from_storage


def create_chunks_table():
    """Create table for document chunks"""
    print("📋 Creating chunks table...")
    
    sql = """
    DROP TABLE IF EXISTS document_chunks CASCADE;
    CREATE TABLE document_chunks (
        id SERIAL PRIMARY KEY,
        source VARCHAR(20),
        report_id INTEGER,
        title VARCHAR(100),
        season VARCHAR(50),
        week INTEGER,
        chunk_index INTEGER,
        total_chunks INTEGER,
        content TEXT,
        embedding vector(1024),
        created_at TIMESTAMP DEFAULT NOW()
    );
    
    CREATE INDEX idx_chunks_lookup ON document_chunks(title, season, week);
    CREATE INDEX idx_chunks_embedding ON document_chunks 
        USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
    """
    
    cmd = [
        'ssh', '-o', 'StrictHostKeyChecking=no',
        'azureuser@4.155.228.61',
        f'docker exec supabase-db psql -U supabase_admin -d postgres -c "{sql}"'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode == 0:
        print("✅ Chunks table created")
    else:
        print(f"❌ Error: {result.stderr}")
        return False
    return True


def insert_chunk(chunk_data: dict) -> bool:
    """Insert a single chunk into database using file-based approach"""
    import tempfile
    import os
    
    embedding_str = "[" + ",".join(map(str, chunk_data['embedding'])) + "]"
    
    # Escape content for SQL
    content_escaped = chunk_data['content'].replace("'", "''").replace("\\", "\\\\")
    
    sql = f"""INSERT INTO document_chunks (source, report_id, title, season, week, chunk_index, total_chunks, content, embedding) VALUES ('{chunk_data['source']}', {chunk_data['report_id']}, '{chunk_data['title']}', '{chunk_data['season']}', {chunk_data['week']}, {chunk_data['chunk_index']}, {chunk_data['total_chunks']}, '{content_escaped}', '{embedding_str}'::vector);"""
    
    # Write SQL to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
        f.write(sql)
        temp_file = f.name
    
    try:
        # Copy file to VM, then to container, then execute
        scp_result = subprocess.run(
            ['scp', '-o', 'StrictHostKeyChecking=no', temp_file, 
             'azureuser@4.155.228.61:/tmp/chunk.sql'],
            capture_output=True, timeout=30
        )
        
        if scp_result.returncode != 0:
            print(f"    SCP Error: {scp_result.stderr.decode()[:100]}")
            return False
        
        # Copy from VM to container and execute
        result = subprocess.run(
            ['ssh', '-o', 'StrictHostKeyChecking=no', 'azureuser@4.155.228.61',
             'docker cp /tmp/chunk.sql supabase-db:/tmp/chunk.sql && docker exec supabase-db psql -U supabase_admin -d postgres -f /tmp/chunk.sql'],
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode != 0 and result.stderr:
            print(f"    SQL Error: {result.stderr[:100]}")
        
        return result.returncode == 0
    finally:
        os.unlink(temp_file)


def process_all_documents():
    """Process all documents: chunk + embed + store"""
    print("\n📚 Processing all documents...")
    
    # Get all reports
    reports = execute_sql_json("""
        SELECT 'origin' as source, id, title, season, week, storage_path, summary
        FROM report_origin
        UNION ALL
        SELECT 'deep' as source, id, title, season, week, storage_path, summary
        FROM report_deep_research
    """)
    
    print(f"Found {len(reports)} reports to process")
    
    total_chunks = 0
    
    for report in reports:
        print(f"\n→ Processing [{report['source']}] {report['title']} {report['season']} Week {report['week']}")
        
        # Get content
        content = None
        if report.get("storage_path"):
            content = get_report_content_from_storage(report["storage_path"])
        
        if not content:
            content = report.get("summary", "")
        
        if not content:
            print("  ⚠️ No content, skipping")
            continue
        
        # Chunk document
        metadata = {
            "source": report["source"],
            "title": report["title"],
            "season": report["season"],
            "week": report["week"]
        }
        
        nodes = chunk_document(content, metadata)
        print(f"  📄 Created {len(nodes)} chunks")
        
        # Generate embeddings in batch
        texts = [node.text for node in nodes]
        try:
            embeddings = embed_model.get_text_embeddings(texts)
            print(f"  🔢 Generated {len(embeddings)} embeddings")
        except Exception as e:
            print(f"  ❌ Embedding error: {e}")
            continue
        
        # Store chunks
        for i, (node, embedding) in enumerate(zip(nodes, embeddings)):
            chunk_data = {
                "source": report["source"],
                "report_id": report["id"],
                "title": report["title"],
                "season": report["season"],
                "week": report["week"],
                "chunk_index": i,
                "total_chunks": len(nodes),
                "content": node.text.replace("'", "''"),  # Escape quotes
                "embedding": embedding
            }
            
            if insert_chunk(chunk_data):
                total_chunks += 1
            else:
                print(f"  ⚠️ Failed to insert chunk {i}")
        
        print(f"  ✅ Stored {len(nodes)} chunks")
    
    print(f"\n✅ Total chunks stored: {total_chunks}")


def verify_chunks():
    """Verify chunks were stored correctly"""
    print("\n🔍 Verifying chunks...")
    
    result = execute_sql_json("""
        SELECT source, title, season, week, COUNT(*) as chunk_count
        FROM document_chunks
        GROUP BY source, title, season, week
        ORDER BY title, season, week
    """)
    
    print(f"\nChunks per document:")
    for r in result:
        print(f"  [{r['source']}] {r['title']} {r['season']} W{r['week']}: {r['chunk_count']} chunks")
    
    # Test vector search
    print("\n🔍 Testing vector search on chunks...")
    test_query = "Why did BR hours increase?"
    
    query_embedding = embed_model.get_text_embedding(test_query)
    embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
    
    results = execute_sql_json(f"""
        SELECT title, season, week, chunk_index, 
               LEFT(content, 100) as content_preview,
               1 - (embedding <=> '{embedding_str}'::vector) as similarity
        FROM document_chunks
        ORDER BY embedding <=> '{embedding_str}'::vector
        LIMIT 5
    """)
    
    print(f"\nTop 5 similar chunks for '{test_query}':")
    for r in results:
        print(f"  [{r['title']} S{r['season']} W{r['week']} #{r['chunk_index']}] sim={r['similarity']:.4f}")
        print(f"     {r['content_preview']}...")


def main():
    print("="*60)
    print("🚀 Setting up chunked documents for LlamaIndex RAG")
    print("="*60)
    
    # Step 1: Create table
    if not create_chunks_table():
        return
    
    # Step 2: Process documents
    process_all_documents()
    
    # Step 3: Verify
    verify_chunks()
    
    print("\n" + "="*60)
    print("✅ Setup complete!")
    print("="*60)


if __name__ == "__main__":
    main()

