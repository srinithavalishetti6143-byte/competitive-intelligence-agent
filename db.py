import sqlite3
import json
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "database.sqlite")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Competitors Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS competitors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        domain TEXT,
        industry TEXT,
        tier TEXT DEFAULT 'Direct',
        threat_level TEXT DEFAULT 'Medium',
        baseline_summary TEXT,
        website_url TEXT,
        careers_url TEXT,
        pricing_url TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Intelligence Events Table (Pricing, Feature, Messaging, Hiring)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS intelligence_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        competitor_id INTEGER NOT NULL,
        category TEXT NOT NULL, -- 'Pricing', 'Feature', 'Messaging', 'Hiring'
        event_type TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        impact_score INTEGER DEFAULT 3, -- 1 (Low) to 5 (Critical)
        detected_at DATETIME NOT NULL,
        source_type TEXT DEFAULT 'Scraper', -- 'Scraper', 'Kaggle', 'Manual', 'Simulated'
        source_url TEXT,
        raw_snapshot TEXT,
        FOREIGN KEY (competitor_id) REFERENCES competitors (id) ON DELETE CASCADE
    )
    """)
    
    # Snapshots Table (Raw HTML / Metadata snapshots for diffing)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        competitor_id INTEGER NOT NULL,
        page_type TEXT NOT NULL, -- 'homepage', 'pricing', 'careers'
        content_hash TEXT NOT NULL,
        content_summary TEXT,
        raw_content TEXT,
        captured_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (competitor_id) REFERENCES competitors (id) ON DELETE CASCADE
    )
    """)
    
    # AI Pattern Insights Table (Cumulative pattern discoveries)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pattern_insights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        competitor_id INTEGER, -- Nullable for industry-wide macro patterns
        insight_title TEXT NOT NULL,
        timeframe_days INTEGER DEFAULT 180,
        pattern_category TEXT NOT NULL,
        summary TEXT NOT NULL,
        supporting_event_ids TEXT, -- JSON array of event IDs
        threat_assessment TEXT,
        recommended_response TEXT,
        confidence_score INTEGER DEFAULT 85,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (competitor_id) REFERENCES competitors (id) ON DELETE CASCADE
    )
    """)
    
    # Kaggle Datasets Log Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kaggle_imports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dataset_ref TEXT NOT NULL,
        title TEXT NOT NULL,
        records_imported INTEGER DEFAULT 0,
        imported_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()

# --- Competitor Helpers ---

def get_all_competitors():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM competitors ORDER BY threat_level DESC, name ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_competitor_by_id(comp_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM competitors WHERE id = ?", (comp_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def add_competitor(name, domain="", industry="SaaS / Tech", tier="Direct", threat_level="High", baseline_summary="", website_url="", careers_url="", pricing_url=""):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO competitors (name, domain, industry, tier, threat_level, baseline_summary, website_url, careers_url, pricing_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            domain=excluded.domain,
            industry=excluded.industry,
            tier=excluded.tier,
            threat_level=excluded.threat_level,
            website_url=excluded.website_url,
            careers_url=excluded.careers_url,
            pricing_url=excluded.pricing_url
    """, (name, domain, industry, tier, threat_level, baseline_summary, website_url, careers_url, pricing_url))
    comp_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return comp_id

def delete_competitor(comp_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM competitors WHERE id = ?", (comp_id,))
    conn.commit()
    conn.close()

# --- Intelligence Events Helpers ---

def add_event(competitor_id, category, event_type, title, description, impact_score=3, detected_at=None, source_type="Manual", source_url="", raw_snapshot=""):
    if not detected_at:
        detected_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO intelligence_events (competitor_id, category, event_type, title, description, impact_score, detected_at, source_type, source_url, raw_snapshot)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (competitor_id, category, event_type, title, description, impact_score, detected_at, source_type, source_url, raw_snapshot))
    event_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return event_id

def get_events(competitor_id=None, category=None, days_limit=365):
    conn = get_db()
    cursor = conn.cursor()
    
    query = """
        SELECT e.*, c.name as competitor_name, c.threat_level
        FROM intelligence_events e
        JOIN competitors c ON e.competitor_id = c.id
        WHERE 1=1
    """
    params = []
    
    if competitor_id:
        query += " AND e.competitor_id = ?"
        params.append(competitor_id)
        
    if category:
        query += " AND e.category = ?"
        params.append(category)
        
    if days_limit:
        cutoff = (datetime.now() - timedelta(days=days_limit)).strftime("%Y-%m-%d %H:%M:%S")
        query += " AND e.detected_at >= ?"
        params.append(cutoff)
        
    query += " ORDER BY e.detected_at DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# --- Pattern Insights Helpers ---

def save_pattern_insight(competitor_id, insight_title, pattern_category, summary, timeframe_days=180, supporting_event_ids=None, threat_assessment="Medium", recommended_response="", confidence_score=85):
    conn = get_db()
    cursor = conn.cursor()
    
    event_ids_str = json.dumps(supporting_event_ids or [])
    
    cursor.execute("""
        INSERT INTO pattern_insights (competitor_id, insight_title, timeframe_days, pattern_category, summary, supporting_event_ids, threat_assessment, recommended_response, confidence_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (competitor_id, insight_title, timeframe_days, pattern_category, summary, event_ids_str, threat_assessment, recommended_response, confidence_score))
    
    insight_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return insight_id

def get_pattern_insights(competitor_id=None):
    conn = get_db()
    cursor = conn.cursor()
    query = """
        SELECT p.*, c.name as competitor_name
        FROM pattern_insights p
        LEFT JOIN competitors c ON p.competitor_id = c.id
    """
    params = []
    if competitor_id:
        query += " WHERE p.competitor_id = ?"
        params.append(competitor_id)
        
    query += " ORDER BY p.created_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for r in rows:
        item = dict(r)
        if item.get("supporting_event_ids"):
            try:
                item["supporting_event_ids"] = json.loads(item["supporting_event_ids"])
            except:
                item["supporting_event_ids"] = []
        results.append(item)
    return results

# --- Stats & Overview ---

def get_dashboard_stats():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM competitors")
    total_competitors = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM intelligence_events")
    total_events = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM pattern_insights")
    total_insights = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT category, COUNT(*) as count 
        FROM intelligence_events 
        GROUP BY category
    """)
    category_counts = {row["category"]: row["count"] for row in cursor.fetchall()}
    
    cursor.execute("""
        SELECT c.name, COUNT(e.id) as count
        FROM competitors c
        LEFT JOIN intelligence_events e ON c.id = e.competitor_id
        GROUP BY c.id
        ORDER BY count DESC
    """)
    competitor_counts = [dict(r) for r in cursor.fetchall()]
    
    conn.close()
    return {
        "total_competitors": total_competitors,
        "total_events": total_events,
        "total_insights": total_insights,
        "category_counts": category_counts,
        "competitor_counts": competitor_counts
    }
