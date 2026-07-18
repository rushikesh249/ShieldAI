import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "shieldai.db"

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Currency Scans History Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS currency_scans (
        id TEXT PRIMARY KEY,
        timestamp TEXT,
        prediction TEXT,
        confidence REAL,
        features TEXT,
        genuine_indicators TEXT,
        counterfeit_indicators TEXT,
        authenticity_summary TEXT,
        evidence TEXT,
        image_url TEXT
    )
    ''')
    conn.commit()
    conn.close()

def save_scan(data: Dict[str, Any]):
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO currency_scans (
        id, timestamp, prediction, confidence, features, genuine_indicators, 
        counterfeit_indicators, authenticity_summary, evidence, image_url
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get("id"),
        data.get("timestamp", datetime.now().isoformat()),
        data.get("riskLevel"), # using riskLevel as prediction label
        data.get("confidenceScore", 0.0),
        json.dumps(data.get("features", [])),
        json.dumps(data.get("genuineIndicators", [])),
        json.dumps(data.get("counterfeitIndicators", [])),
        data.get("authenticitySummary", ""),
        json.dumps(data.get("evidence", [])),
        data.get("image_url", "")
    ))
    
    conn.commit()
    conn.close()

def get_all_scans() -> List[Dict[str, Any]]:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM currency_scans ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        results.append({
            "id": row["id"],
            "timestamp": row["timestamp"],
            "prediction": row["prediction"],
            "confidenceScore": row["confidence"],
            "features": json.loads(row["features"]) if row["features"] else [],
            "genuineIndicators": json.loads(row["genuine_indicators"]) if row["genuine_indicators"] else [],
            "counterfeitIndicators": json.loads(row["counterfeit_indicators"]) if row["counterfeit_indicators"] else [],
            "authenticitySummary": row["authenticity_summary"],
            "evidence": json.loads(row["evidence"]) if row["evidence"] else [],
            "image_url": row["image_url"]
        })
    return results

def delete_scan(scan_id: str):
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute('DELETE FROM currency_scans WHERE id = ?', (scan_id,))
    conn.commit()
    conn.close()

def get_stats() -> Dict[str, Any]:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as total FROM currency_scans')
    total = cursor.fetchone()["total"]
    
    cursor.execute('SELECT COUNT(*) as fake FROM currency_scans WHERE prediction = "High Risk"')
    fake = cursor.fetchone()["fake"]
    
    cursor.execute('SELECT COUNT(*) as genuine FROM currency_scans WHERE prediction = "Low Risk"')
    genuine = cursor.fetchone()["genuine"]
    
    cursor.execute('SELECT AVG(confidence) as avg_conf FROM currency_scans')
    avg_conf = cursor.fetchone()["avg_conf"]
    
    # daily analytics could be grouped by date
    cursor.execute('SELECT substr(timestamp, 1, 10) as date, COUNT(*) as count FROM currency_scans GROUP BY date ORDER BY date DESC LIMIT 30')
    daily = [{"date": r["date"], "scans": r["count"]} for r in cursor.fetchall()]
    
    conn.close()
    
    return {
        "totalScans": total,
        "fakeDetected": fake,
        "genuineDetected": genuine,
        "averageConfidence": round(avg_conf or 0.0, 2),
        "dailyAnalytics": daily
    }

# Initialize on import
init_db()
