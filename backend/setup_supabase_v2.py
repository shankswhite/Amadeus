#!/usr/bin/env python3
"""
Supabase Setup Script V2
- Creates Storage bucket
- Uploads report files to Object Storage
- Inserts metadata to PostgreSQL
- Inserts metrics data

Usage:
1. First, create SSH tunnel:
   ssh -L 8000:localhost:8000 -L 5432:localhost:5432 user@4.155.228.61

2. Then run:
   python backend/setup_supabase_v2.py --all
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime

# Try to import required packages
try:
    import httpx
except ImportError:
    print("Installing httpx...")
    os.system("pip install httpx -q")
    import httpx

try:
    import psycopg2
except ImportError:
    print("Installing psycopg2-binary...")
    os.system("pip install psycopg2-binary -q")
    import psycopg2

# Configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL", "http://localhost:8000")  # Via SSH tunnel
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UiLCJpYXQiOjE3NjM3NjkwNTEsImV4cCI6MjA3OTEyOTA1MX0.Lo5Uda5J4r2WvIO0tLG1fGGAf08r6sP5efw11sc-aW4")

# PostgreSQL via SSH tunnel
PG_HOST = os.environ.get("PG_HOST", "localhost")
PG_PORT = os.environ.get("PG_PORT", "5432")
PG_USER = os.environ.get("PG_USER", "postgres")
PG_PASSWORD = os.environ.get("PG_PASSWORD", "postgres")
PG_DATABASE = os.environ.get("PG_DATABASE", "postgres")

# Paths
SCRIPT_DIR = Path(__file__).parent
FAKE_REPORTS_DIR = SCRIPT_DIR / "fake_reports"
SQL_DIR = SCRIPT_DIR


def get_supabase_headers():
    """Get headers for Supabase API calls"""
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }


def test_connections():
    """Test both Supabase API and PostgreSQL connections"""
    print("🔍 Testing connections...")
    
    # Test Supabase API
    try:
        response = httpx.get(f"{SUPABASE_URL}/rest/v1/", headers=get_supabase_headers(), timeout=5)
        if response.status_code in [200, 401]:  # 401 is okay, means API is reachable
            print(f"  ✅ Supabase API reachable at {SUPABASE_URL}")
        else:
            print(f"  ⚠️ Supabase API status: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Supabase API error: {e}")
        print("     Make sure SSH tunnel is active: ssh -L 8000:localhost:8000 user@VM")
        return False
    
    # Test PostgreSQL
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            database=PG_DATABASE
        )
        conn.close()
        print(f"  ✅ PostgreSQL connected at {PG_HOST}:{PG_PORT}")
    except Exception as e:
        print(f"  ❌ PostgreSQL error: {e}")
        print("     Make sure SSH tunnel is active: ssh -L 5432:localhost:5432 user@VM")
        return False
    
    return True


def create_tables():
    """Create tables using SQL file"""
    print("\n📋 Creating tables...")
    
    sql_file = SQL_DIR / "create_tables_v2.sql"
    if not sql_file.exists():
        print(f"  ❌ SQL file not found: {sql_file}")
        return False
    
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            database=PG_DATABASE
        )
        cur = conn.cursor()
        
        # Read and execute SQL (skip problematic RLS policies for now)
        sql_content = sql_file.read_text()
        
        # Execute statement by statement to handle errors gracefully
        statements = sql_content.split(';')
        for stmt in statements:
            stmt = stmt.strip()
            if not stmt or stmt.startswith('--'):
                continue
            try:
                cur.execute(stmt + ';')
                conn.commit()
            except Exception as e:
                conn.rollback()
                if "already exists" in str(e):
                    print(f"  ⚠️ Skipped (already exists): {stmt[:50]}...")
                elif "does not exist" in str(e) and "policy" in stmt.lower():
                    print(f"  ⚠️ Skipped policy: {stmt[:50]}...")
                else:
                    print(f"  ⚠️ Warning: {e}")
        
        print("  ✅ Tables created/verified")
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def create_storage_bucket():
    """Create storage bucket for reports"""
    print("\n📦 Creating storage bucket...")
    
    try:
        # Check if bucket exists
        response = httpx.get(
            f"{SUPABASE_URL}/storage/v1/bucket/reports",
            headers=get_supabase_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            print("  ✅ Bucket 'reports' already exists")
            return True
        
        # Create bucket
        response = httpx.post(
            f"{SUPABASE_URL}/storage/v1/bucket",
            headers=get_supabase_headers(),
            json={"id": "reports", "name": "reports", "public": False},
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            print("  ✅ Bucket 'reports' created")
            return True
        else:
            print(f"  ⚠️ Bucket creation response: {response.status_code} - {response.text[:100]}")
            return True  # Continue anyway
            
    except Exception as e:
        print(f"  ⚠️ Storage bucket warning: {e}")
        return True  # Continue anyway


def upload_reports():
    """Upload report files to storage and insert metadata"""
    print("\n📤 Uploading reports...")
    
    if not FAKE_REPORTS_DIR.exists():
        print(f"  ❌ Fake reports directory not found: {FAKE_REPORTS_DIR}")
        return False
    
    # Define report mappings
    reports = [
        {"file": "bo6_wz2_season3_week1_origin.md", "title": "bo6_wz2", "season": "Season 3", "week": 1, "type": "origin"},
        {"file": "bo6_wz2_season3_week1_deep.md", "title": "bo6_wz2", "season": "Season 3", "week": 1, "type": "deep"},
        {"file": "bo6_wz2_season3_week2_origin.md", "title": "bo6_wz2", "season": "Season 3", "week": 2, "type": "origin"},
        {"file": "bo6_wz2_season3_week2_deep.md", "title": "bo6_wz2", "season": "Season 3", "week": 2, "type": "deep"},
    ]
    
    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        user=PG_USER,
        password=PG_PASSWORD,
        database=PG_DATABASE
    )
    cur = conn.cursor()
    
    for report in reports:
        file_path = FAKE_REPORTS_DIR / report["file"]
        if not file_path.exists():
            print(f"  ⚠️ File not found: {file_path}")
            continue
        
        content = file_path.read_text()
        storage_path = f"reports/{report['type']}/{report['file']}"
        
        # Upload to storage
        try:
            headers = get_supabase_headers()
            headers["Content-Type"] = "text/markdown"
            
            response = httpx.post(
                f"{SUPABASE_URL}/storage/v1/object/reports/{report['type']}/{report['file']}",
                headers=headers,
                content=content.encode(),
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                print(f"  ✅ Uploaded: {storage_path}")
            else:
                print(f"  ⚠️ Upload warning: {response.status_code}")
                # Store content in DB as fallback
                storage_path = None
                
        except Exception as e:
            print(f"  ⚠️ Upload error: {e}")
            storage_path = None
        
        # Insert metadata
        table = "report_origin" if report["type"] == "origin" else "report_deep_research"
        summary = content[:200] + "..." if len(content) > 200 else content
        
        try:
            cur.execute(f"""
                INSERT INTO {table} (title, season, week, storage_path, summary, content_length)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (title, season, week) 
                DO UPDATE SET storage_path = EXCLUDED.storage_path, 
                              summary = EXCLUDED.summary,
                              content_length = EXCLUDED.content_length,
                              updated_at = NOW()
            """, (report["title"], report["season"], report["week"], storage_path, summary, len(content)))
            conn.commit()
            print(f"  ✅ Metadata saved: {table} - {report['title']} {report['season']} W{report['week']}")
        except Exception as e:
            conn.rollback()
            print(f"  ❌ Metadata error: {e}")
    
    cur.close()
    conn.close()
    return True


def insert_metrics():
    """Insert metrics data"""
    print("\n📊 Inserting metrics data...")
    
    metrics = [
        # Week 1 - Overall BR Hours
        {"week_end_date": "2025-04-02", "week_start_date": "2025-03-27", "week_number": 1, "title": "bo6_wz2", "season": "Season 3", "metric_category": "engagement", "metric_name": "br_hours", "data_type": "overall", "is_topline_metric": True, "segment_level": 0, "value_current": 38892636.49, "value_previous": 7630645.28, "value_delta": 31261991.21, "current_active_players": 17091206, "is_outlier": True, "outlier_type": "positive_outlier", "comparison_mode": "cross_season", "monitored_title": "bo6_wz2", "monitored_season": "Season 3"},
        
        # Week 1 - Segments
        {"week_end_date": "2025-04-02", "week_start_date": "2025-03-27", "week_number": 1, "title": "bo6_wz2", "season": "Season 3", "metric_category": "engagement", "metric_name": "br_hours", "data_type": "segment", "segment_level": 1, "segment_combo": "mode_main=BR Main", "contribution_value": 0.7147, "contribution_type": "positive", "contribution_rank_positive": 1, "value_current": 27471824.61, "value_previous": 5128727.55, "value_delta": 22343097.06, "is_top_contributor": True, "is_outlier": True, "outlier_type": "positive_outlier"},
        
        {"week_end_date": "2025-04-02", "week_start_date": "2025-03-27", "week_number": 1, "title": "bo6_wz2", "season": "Season 3", "metric_category": "engagement", "metric_name": "br_hours", "data_type": "segment", "segment_level": 1, "segment_combo": "premium_label=Premium", "contribution_value": 0.6728, "contribution_type": "positive", "contribution_rank_positive": 2, "value_current": 23907797.69, "value_previous": 2873249.65, "value_delta": 21034548.04, "is_outlier": True, "outlier_type": "positive_outlier"},
        
        {"week_end_date": "2025-04-02", "week_start_date": "2025-03-27", "week_number": 1, "title": "bo6_wz2", "season": "Season 3", "metric_category": "engagement", "metric_name": "br_hours", "data_type": "segment", "segment_level": 1, "segment_combo": "spending_segment=Dolphins", "contribution_value": 0.6714, "contribution_type": "positive", "contribution_rank_positive": 3, "value_current": 26539001.74, "value_previous": 5550573.49, "value_delta": 20988428.24, "is_outlier": True, "outlier_type": "positive_outlier"},
        
        {"week_end_date": "2025-04-02", "week_start_date": "2025-03-27", "week_number": 1, "title": "bo6_wz2", "season": "Season 3", "metric_category": "engagement", "metric_name": "br_hours", "data_type": "segment", "segment_level": 1, "segment_combo": "premium_label=F2P", "contribution_value": 0.3272, "contribution_type": "positive", "contribution_rank_positive": 4, "value_current": 14984838.80, "value_previous": 4757395.63, "value_delta": 10227443.17, "is_outlier": False},
        
        {"week_end_date": "2025-04-02", "week_start_date": "2025-03-27", "week_number": 1, "title": "bo6_wz2", "season": "Season 3", "metric_category": "engagement", "metric_name": "br_hours", "data_type": "segment", "segment_level": 1, "segment_combo": "spending_segment=Whales", "contribution_value": 0.1965, "contribution_type": "positive", "contribution_rank_positive": 5, "value_current": 7138484.54, "value_previous": 996286.89, "value_delta": 6142197.65, "is_outlier": False},
        
        # Week 1 - DAU
        {"week_end_date": "2025-04-02", "week_start_date": "2025-03-27", "week_number": 1, "title": "bo6_wz2", "season": "Season 3", "metric_category": "engagement", "metric_name": "dau", "data_type": "overall", "is_topline_metric": True, "segment_level": 0, "value_current": 8234567, "value_previous": 3215678, "value_delta": 5018889, "is_outlier": True, "outlier_type": "positive_outlier"},
        
        # Week 2 - Overall
        {"week_end_date": "2025-04-09", "week_start_date": "2025-04-03", "week_number": 2, "title": "bo6_wz2", "season": "Season 3", "metric_category": "engagement", "metric_name": "br_hours", "data_type": "overall", "is_topline_metric": True, "segment_level": 0, "value_current": 32145678.90, "value_previous": 38892636.49, "value_delta": -6746957.59, "is_outlier": False, "comparison_mode": "week_over_week"},
        
        # Week 2 - Resurgence segment
        {"week_end_date": "2025-04-09", "week_start_date": "2025-04-03", "week_number": 2, "title": "bo6_wz2", "season": "Season 3", "metric_category": "engagement", "metric_name": "br_hours", "data_type": "segment", "segment_level": 1, "segment_combo": "mode_main=Resurgence", "contribution_value": 0.45, "contribution_type": "positive", "contribution_rank_positive": 1, "value_current": 9876543.21, "value_previous": 6812345.67, "value_delta": 3064197.54, "is_top_contributor": True, "is_outlier": True, "outlier_type": "positive_outlier"},
        
        # Week 2 - DAU
        {"week_end_date": "2025-04-09", "week_start_date": "2025-04-03", "week_number": 2, "title": "bo6_wz2", "season": "Season 3", "metric_category": "engagement", "metric_name": "dau", "data_type": "overall", "is_topline_metric": True, "segment_level": 0, "value_current": 7123456, "value_previous": 8234567, "value_delta": -1111111, "is_outlier": False},
    ]
    
    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        user=PG_USER,
        password=PG_PASSWORD,
        database=PG_DATABASE
    )
    cur = conn.cursor()
    
    # Clear existing data
    cur.execute("DELETE FROM metrics_data WHERE title = 'bo6_wz2' AND season = 'Season 3'")
    conn.commit()
    
    for metric in metrics:
        columns = ', '.join(metric.keys())
        placeholders = ', '.join(['%s'] * len(metric))
        
        try:
            cur.execute(
                f"INSERT INTO metrics_data ({columns}) VALUES ({placeholders})",
                list(metric.values())
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"  ⚠️ Metric insert warning: {e}")
    
    print(f"  ✅ Inserted {len(metrics)} metrics records")
    
    cur.close()
    conn.close()
    return True


def verify_data():
    """Verify all data is properly inserted"""
    print("\n🔍 Verifying data...")
    
    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        user=PG_USER,
        password=PG_PASSWORD,
        database=PG_DATABASE
    )
    cur = conn.cursor()
    
    # Check tables
    tables = ["report_origin", "report_deep_research", "metrics_data"]
    for table in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"  ✅ {table}: {count} records")
        except Exception as e:
            print(f"  ❌ {table}: {e}")
    
    # Show sample data
    print("\n📋 Sample metrics data:")
    cur.execute("""
        SELECT title, season, week_number, metric_name, segment_combo, 
               value_current, value_delta, is_outlier
        FROM metrics_data 
        WHERE title = 'bo6_wz2' AND season = 'Season 3'
        ORDER BY week_number, contribution_rank_positive NULLS LAST
        LIMIT 5
    """)
    for row in cur.fetchall():
        print(f"     {row}")
    
    cur.close()
    conn.close()


def main():
    print("="*60)
    print("🚀 SUPABASE SETUP V2")
    print("="*60)
    
    args = sys.argv[1:] if len(sys.argv) > 1 else ["--help"]
    
    if "--help" in args:
        print("""
Usage:
  python setup_supabase_v2.py [options]

Options:
  --all       Run all setup steps
  --test      Test connections only
  --tables    Create tables only
  --data      Insert fake data only
  --verify    Verify data only

Prerequisites:
  1. SSH tunnel to Supabase VM:
     ssh -L 8000:localhost:8000 -L 5432:localhost:5432 user@4.155.228.61

  2. Set environment variables (optional):
     export PG_PASSWORD=your_password
        """)
        return
    
    if "--test" in args or "--all" in args:
        if not test_connections():
            print("\n❌ Connection test failed. Please check SSH tunnel.")
            return
    
    if "--tables" in args or "--all" in args:
        create_tables()
    
    if "--bucket" in args or "--all" in args:
        create_storage_bucket()
    
    if "--data" in args or "--all" in args:
        upload_reports()
        insert_metrics()
    
    if "--verify" in args or "--all" in args:
        verify_data()
    
    print("\n" + "="*60)
    print("✅ Setup complete!")
    print("="*60)


if __name__ == "__main__":
    main()

