from flask import Flask, render_template, request, jsonify, make_response
import os
import json
from datetime import datetime, timedelta

from db import (
    init_db, get_all_competitors, get_competitor_by_id, add_competitor, delete_competitor,
    get_events, add_event, get_pattern_insights, get_dashboard_stats
)
from kaggle_integration import KaggleIntelPipeline
from scraper import CompetitorScraper
from ai_agent import CompeteMindAIAgent
from seed_data import seed_database

app = Flask(__name__, template_folder="templates", static_folder="static")

# Initialize DB and seed dataset on startup
init_db()
seed_database()

kaggle_pipeline = KaggleIntelPipeline()
scraper = CompetitorScraper()
ai_agent = CompeteMindAIAgent()

# --- Page Routes ---

@app.route("/")
def index():
    return render_template("index.html")

# --- API Endpoints ---

@app.route("/api/dashboard/stats", methods=["GET"])
def api_dashboard_stats():
    stats = get_dashboard_stats()
    stats["kaggle_authenticated"] = kaggle_pipeline.authenticated
    return jsonify(stats)

@app.route("/api/competitors", methods=["GET", "POST"])
def api_competitors():
    if request.method == "POST":
        data = request.json or {}
        name = data.get("name")
        if not name:
            return jsonify({"status": "error", "message": "Competitor name is required"}), 400
            
        comp_id = add_competitor(
            name=name,
            domain=data.get("domain", ""),
            industry=data.get("industry", "SaaS / Tech"),
            tier=data.get("tier", "Direct"),
            threat_level=data.get("threat_level", "Medium"),
            baseline_summary=data.get("baseline_summary", ""),
            website_url=data.get("website_url", ""),
            careers_url=data.get("careers_url", ""),
            pricing_url=data.get("pricing_url", "")
        )
        return jsonify({"status": "success", "message": f"Competitor '{name}' added successfully", "competitor_id": comp_id})
    else:
        competitors = get_all_competitors()
        return jsonify(competitors)

@app.route("/api/competitors/<int:comp_id>", methods=["DELETE"])
def api_delete_competitor(comp_id):
    delete_competitor(comp_id)
    return jsonify({"status": "success", "message": "Competitor deleted"})

@app.route("/api/timeline", methods=["GET"])
def api_timeline():
    comp_id = request.args.get("competitor_id", type=int)
    category = request.args.get("category")
    days = request.args.get("days", default=365, type=int)
    
    events = get_events(competitor_id=comp_id, category=category, days_limit=days)
    return jsonify({
        "timeframe_days": days,
        "total_events": len(events),
        "events": events
    })

@app.route("/api/events", methods=["POST"])
def api_add_event():
    data = request.json or {}
    comp_id = data.get("competitor_id")
    category = data.get("category")
    title = data.get("title")
    description = data.get("description")
    
    if not comp_id or not category or not title:
        return jsonify({"status": "error", "message": "competitor_id, category, and title are required"}), 400
        
    event_id = add_event(
        competitor_id=comp_id,
        category=category,
        event_type=data.get("event_type", "Manual Entry"),
        title=title,
        description=description or title,
        impact_score=data.get("impact_score", 3),
        detected_at=data.get("detected_at"),
        source_type=data.get("source_type", "Manual"),
        source_url=data.get("source_url", "")
    )
    return jsonify({"status": "success", "event_id": event_id})

@app.route("/api/ingest/scrape", methods=["POST"])
def api_scrape():
    data = request.json or {}
    comp_id = data.get("competitor_id")
    if not comp_id:
        return jsonify({"status": "error", "message": "competitor_id is required"}), 400
        
    result = scraper.monitor_competitor_pages(comp_id)
    return jsonify(result)

@app.route("/api/kaggle/search", methods=["GET"])
def api_kaggle_search():
    query = request.args.get("q", "competitor tech saas pricing hiring")
    results = kaggle_pipeline.search_datasets(query)
    return jsonify(results)

@app.route("/api/kaggle/import", methods=["POST"])
def api_kaggle_import():
    data = request.json or {}
    dataset_ref = data.get("dataset_ref")
    if not dataset_ref:
        return jsonify({"status": "error", "message": "dataset_ref is required"}), 400
        
    result = kaggle_pipeline.import_kaggle_dataset(dataset_ref)
    return jsonify(result)

@app.route("/api/analyze/patterns", methods=["POST"])
def api_analyze_patterns():
    data = request.json or {}
    comp_id = data.get("competitor_id")
    timeframe_days = data.get("timeframe_days", 180)
    
    analysis = ai_agent.run_cumulative_pattern_analysis(competitor_id=comp_id, timeframe_days=timeframe_days)
    return jsonify(analysis)

@app.route("/api/insights", methods=["GET"])
def api_get_insights():
    comp_id = request.args.get("competitor_id", type=int)
    insights = get_pattern_insights(competitor_id=comp_id)
    return jsonify(insights)

@app.route("/api/simulate", methods=["POST"])
def api_simulate():
    """Simulates a new competitor move (Pricing, Feature, Messaging, Hiring) live to verify cumulative memory response."""
    data = request.json or {}
    comp_id = data.get("competitor_id", 1)
    category = data.get("category", "Pricing")
    title = data.get("title", "Simulated Competitor Move")
    desc = data.get("description", "Simulated event added to evaluate memory pattern updates.")
    impact = data.get("impact_score", 4)
    
    event_id = add_event(
        competitor_id=comp_id,
        category=category,
        event_type="Simulated Event",
        title=title,
        description=desc,
        impact_score=impact,
        source_type="Simulator"
    )
    
    # Re-run pattern spotter
    analysis = ai_agent.run_cumulative_pattern_analysis(timeframe_days=180)
    
    return jsonify({
        "status": "success",
        "message": f"Simulated {category} event added to competitor memory!",
        "event_id": event_id,
        "updated_analysis": analysis
    })

@app.route("/api/export/report", methods=["GET"])
def api_export_report():
    """Generates full cumulative competitive intelligence report."""
    events = get_events(days_limit=180)
    insights = get_pattern_insights()
    stats = get_dashboard_stats()
    
    report_md = f"# CompeteMind AI — Cumulative Competitive Intelligence Executive Briefing\n"
    report_md += f"**Generated At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report_md += f"**Cumulative Memory Horizon:** 180 Days | **Total Competitors Tracked:** {stats['total_competitors']} | **Events Analyzed:** {stats['total_events']}\n\n"
    
    report_md += "## Executive Summary & Landscape Macro Trends\n"
    report_md += "Over the 6-month cumulative observation window, competitor moves demonstrate a distinct convergence towards AI-native functionality combined with aggressive monetization changes. Weekly point-in-time checks fail to register the deliberate sequencing behind these shifts.\n\n"
    
    report_md += "## Strategic Pattern Discoveries (Cumulative Memory)\n"
    for ins in insights:
        report_md += f"### {ins['insight_title']}\n"
        report_md += f"- **Target Competitor:** {ins.get('competitor_name', 'Industry Wide')}\n"
        report_md += f"- **Threat Assessment:** {ins.get('threat_assessment', 'Medium')}\n"
        report_md += f"- **Confidence Score:** {ins.get('confidence_score', 85)}%\n"
        report_md += f"- **Summary:** {ins['summary']}\n"
        report_md += f"- **Recommended Response:** {ins.get('recommended_response', 'N/A')}\n\n"
        
    report_md += "## Recent Cumulative Events Log\n"
    for ev in events[:20]:
        report_md += f"- **[{ev['detected_at'][:10]}] {ev['competitor_name']} ({ev['category']})**: {ev['title']} — {ev['description']}\n"

    response = make_response(report_md)
    response.headers["Content-Disposition"] = "attachment; filename=CompeteMind_Cumulative_Report.md"
    response.headers["Content-Type"] = "text/markdown; charset=utf-8"
    return response

if __name__ == "__main__":
    print("\n" + "="*70)
    print(" CompeteMind AI — Cumulative Competitive Intelligence Agent ")
    print(" Backend running on http://127.0.0.1:5000")
    print("="*70 + "\n")
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
