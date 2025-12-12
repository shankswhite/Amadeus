#!/usr/bin/env python3
"""
Open Deep Research API Client
Uses direct HTTP calls (not langgraph_sdk) for reliable results
"""

import httpx
import time
import re
from datetime import datetime
import os

# ===== Configuration =====
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbWFkZXVzLXVzZXIiLCJyb2xlIjoic2VydmljZV9yb2xlIiwiaWF0IjoxNzY0NjUzNjMzLCJleHAiOjE3OTYxODk2MzN9.4YyZeyrLPIbPOgS6XH-vidGEiDlEdtyY4mcjLU10kMo"
ODR_API = "https://odr-api.aiverse.chat"  # Cloudflare Tunnel

# Model configuration
DEFAULT_CONFIG = {
    "model": "o4-mini",
    "research_model": "o4-mini", 
    "report_writing_model": "o4-mini",
    "summarization_model": "o4-mini",
    "max_search_depth": 3,
    "max_search_results": 5,
    "allow_clarification": False
}

def run_research(query: str, save_dir: str = "reports"):
    """Run a research query and save the report."""
    
    headers = {
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json"
    }
    
    print("=" * 80)
    print("🔬 Open Deep Research Client")
    print("=" * 80)
    print(f"⏰ Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 API: {ODR_API}")
    print(f"📝 Query: {query[:80]}...")
    print()
    
    start_time = time.time()
    
    # Step 1: Create Thread
    print("📝 [1/4] Creating thread...")
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(f"{ODR_API}/threads", headers=headers, json={})
            response.raise_for_status()
            thread_id = response.json()["thread_id"]
            print(f"    ✅ Thread: {thread_id}")
    except Exception as e:
        print(f"    ❌ Failed: {e}")
        raise
    
    # Step 2: Start Research
    print("\n🔬 [2/4] Starting research...")
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{ODR_API}/threads/{thread_id}/runs",
                headers=headers,
                json={
                    "assistant_id": "Deep Researcher",
                    "input": {
                        "messages": [{"role": "user", "content": query}]
                    },
                    "config": {
                        "configurable": DEFAULT_CONFIG
                    }
                }
            )
            response.raise_for_status()
            run_id = response.json()["run_id"]
            print(f"    ✅ Run: {run_id}")
    except Exception as e:
        print(f"    ❌ Failed: {e}")
        raise
    
    # Step 3: Wait for Completion
    print("\n⏳ [3/4] Waiting for completion...")
    print("    (This may take several minutes)")
    
    check_count = 0
    try:
        with httpx.Client(timeout=3600.0) as client:
            while True:
                check_count += 1
                response = client.get(
                    f"{ODR_API}/threads/{thread_id}/runs/{run_id}",
                    headers=headers
                )
                response.raise_for_status()
                run_status = response.json()
                status = run_status.get("status")
                
                elapsed = int(time.time() - start_time)
                print(f"    [{check_count:02d}] Status: {status:12s} | {elapsed}s")
                
                if status == "success":
                    print("\n    ✅ Complete!")
                    break
                elif status == "error":
                    error_msg = run_status.get("error", "Unknown")
                    print(f"\n    ❌ Error: {error_msg}")
                    raise Exception(error_msg)
                
                time.sleep(10)
    except Exception as e:
        print(f"    ❌ Wait failed: {e}")
        raise
    
    # Step 4: Get Results
    print("\n📥 [4/4] Getting results...")
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                f"{ODR_API}/threads/{thread_id}/state",
                headers=headers
            )
            response.raise_for_status()
            state = response.json()
            
            values = state.get("values", {})
            messages = values.get("messages", [])
            
            # Get final report from last AI message
            final_report = ""
            for msg in reversed(messages):
                if msg.get("type") == "ai" or msg.get("role") == "assistant":
                    final_report = msg.get("content", "")
                    break
            
            # Also check final_report field
            if not final_report or len(final_report) < 100:
                final_report = values.get("final_report", final_report)
            
            if not final_report:
                print("    ⚠️ No report found!")
                print(f"    State keys: {list(values.keys())}")
                return None
            
            # Stats
            image_count = len(re.findall(r'!\[.*?\]\(.*?\)', final_report))
            link_count = len(re.findall(r'\[.*?\]\(https?://.*?\)', final_report))
            
            print(f"    ✅ Report: {len(final_report)} chars")
            print(f"    🖼️ Images: {image_count}")
            print(f"    🔗 Links: {link_count}")
            
    except Exception as e:
        print(f"    ❌ Failed: {e}")
        raise
    
    # Save Report
    os.makedirs(save_dir, exist_ok=True)
    safe_name = re.sub(r'[^\w\s-]', '', query[:50]).strip().replace(' ', '_')
    filename = f"{save_dir}/{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Research Report\n\n")
        f.write(f"**Query:** {query}\n\n")
        f.write(f"**Thread ID:** {thread_id}\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Time:** {int(time.time() - start_time)} seconds\n\n")
        f.write("---\n\n")
        f.write(final_report)
        f.write(f"\n\n---\n\n")
        f.write(f"*Stats: {image_count} images, {link_count} links, {len(final_report)} chars*\n")
    
    print(f"\n💾 Saved: {filename}")
    
    # Preview
    print("\n" + "=" * 80)
    print("📋 Preview (first 500 chars):")
    print("-" * 40)
    print(final_report[:500])
    print("..." if len(final_report) > 500 else "")
    print("=" * 80)
    
    total_time = int(time.time() - start_time)
    print(f"\n🎉 Done! Total time: {total_time} seconds")
    
    return filename


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "Call of Duty Black Ops 6 reviews and player feedback November 2024"
    
    run_research(query)
