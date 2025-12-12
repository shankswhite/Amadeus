"""
Configuration for LIDA Service
"""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "http://4.155.228.61:8000")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Server
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))

# Database Schema
DATABASE_SCHEMA = """
Tables:
1. research_reports
   - id: BIGSERIAL PRIMARY KEY
   - thread_id: TEXT UNIQUE NOT NULL
   - title: TEXT NOT NULL
   - season: TEXT
   - week_number: INTEGER
   - week_start_date: DATE
   - week_end_date: DATE
   - report_content: TEXT
   - created_at: TIMESTAMPTZ

2. anomalies
   - id: BIGSERIAL PRIMARY KEY
   - thread_id: TEXT (FK)
   - title: TEXT NOT NULL
   - season: TEXT
   - week_number: INTEGER
   - week_start_date: DATE
   - week_end_date: DATE
   - metric_name: TEXT
   - metric_value: NUMERIC
   - deviation_percentage: NUMERIC
   - severity: TEXT
   - created_at: TIMESTAMPTZ
"""

