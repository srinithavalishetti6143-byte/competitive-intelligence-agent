import os
from db import init_db, get_dashboard_stats
from kaggle_integration import KaggleIntelPipeline
from ai_agent import CompeteMindAIAgent

def seed_database():
    print("Initializing SQLite Database Schema...")
    init_db()
    
    print("Checking database status...")
    stats = get_dashboard_stats()
    
    if stats["total_events"] == 0:
        print("Database is empty. Populating 6-Month Cumulative Intelligence Memory from Kaggle Competitive Datasets...")
        pipeline = KaggleIntelPipeline()
        
        # Import curated Kaggle datasets (Pricing, Features, Hiring, Messaging over 6 months)
        res1 = pipeline.import_kaggle_dataset("dataset/tech-competitors-6month-pricing-features")
        print(" ->", res1["message"])
        
        res2 = pipeline.import_kaggle_dataset("dataset/competitor-hiring-spikes-ai-engineering")
        print(" ->", res2["message"])
        
        res3 = pipeline.import_kaggle_dataset("dataset/saas-messaging-rebrand-positioning-shifts")
        print(" ->", res3["message"])
        
        print("Running initial AI Pattern Spotter across 180-day cumulative memory window...")
        agent = CompeteMindAIAgent()
        analysis = agent.run_cumulative_pattern_analysis(timeframe_days=180)
        print(f" -> Pattern analysis complete! {analysis.get('patterns_detected_count', 0)} macro strategic patterns detected.")
    else:
        print(f"Database already contains {stats['total_competitors']} competitors, {stats['total_events']} events, and {stats['total_insights']} pattern insights.")

if __name__ == "__main__":
    seed_database()
