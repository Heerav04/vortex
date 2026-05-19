import sqlite3
import pandas as pd
from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "telemetry.sqlite3"

def generate_report():
    print("========================================")
    print("       VORTEX EVALUATION REPORT         ")
    print("========================================\n")
    
    print("1. TEST HARNESS STATUS")
    print("   Run `pytest tests/` to view exact routing accuracy.")
    print("   (Automated test pass rate generally reflects intent accuracy)\n")
    
    print("2. RAG RETRIEVAL SUMMARY")
    print("   Run `python evals/run_rag_eval.py` to calculate exact precision/recall.\n")
    
    if not DB_PATH.exists():
        print("3. TELEMETRY: No data available yet.")
        return
        
    try:
        with sqlite3.connect(DB_PATH) as conn:
            df = pd.read_sql_query("SELECT * FROM events WHERE event_type='tool_executed'", conn)
            
        if df.empty:
            print("3. TELEMETRY: No tool execution data available yet.")
            return
            
        print("3. LIVE LATENCY & RELIABILITY SNAPSHOT")
        avg_lat = df['latency_ms'].mean()
        print(f"   Avg Tool Latency:  {avg_lat:.2f} ms")
        
        df['success'] = df['payload'].apply(lambda x: json.loads(x).get('success', False))
        success_rate = (df['success'].sum() / len(df)) * 100
        print(f"   Execution Success: {success_rate:.2f}%")
        
        failures = df[df['success'] == False]
        print(f"   Failure Count:     {len(failures)}")
        if not failures.empty:
            print("   Recent Failures:")
            for _, row in failures.head(3).iterrows():
                payload = json.loads(row['payload'])
                print(f"     - {payload.get('tool')}.{payload.get('action')}")
    except Exception as e:
        print(f"Error reading telemetry: {e}")
            
if __name__ == "__main__":
    generate_report()
