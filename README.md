# CompeteMind AI — Cumulative Competitive Intelligence Agent

> **Monitors, remembers, and synthesizes competitor moves over a 6-to-12 month cumulative horizon.**
> Identifies subtle macro patterns—pricing escalation trends, strategic AI pivots, stealth upmarket pushes, and hiring velocity shifts—that weekly checks miss.

---

## 💡 Key Problem Solved

Competitive intelligence is **only useful if it is cumulative**. A weekly check reveals isolated events (e.g. a minor feature launch or a job posting). **An AI agent that remembers 6+ months of competitor activity spots macro patterns**:
1. **Pricing Escalation Sequences**: Tightening freemium limits in Month 1 $\rightarrow$ raising seat prices in Month 3 $\rightarrow$ removing transparent enterprise pricing in Month 6.
2. **AI Transformation Pivots**: Hiring spikes in LLM/RAG engineers in Q1 $\rightarrow$ rolling out semantic search in Q2 $\rightarrow$ shifting homepage tagline to "AI Work Assistant" in Q3.
3. **Upmarket Target Pivots**: Hiring enterprise sales leadership from Snowflake $\rightarrow$ adding enterprise compliance postings $\rightarrow$ locking down volume discounts.

---

## 🚀 System Architecture & Capabilities

```
┌────────────────────────────────────────────────────────────────────────┐
│                        COMPETEMIND AI DASHBOARD                        │
│         (Interactive Dark Mode UI, Charts, 6-Month Timeline)          │
└───────────────────┬────────────────────────────────┬───────────────────┘
                    │                                │
    ┌───────────────▼──────────────┐  ┌──────────────▼───────────────┐
    │  Flask Python Backend API    │  │ Kaggle Datasets Pipeline      │
    │  - REST Endpoints            │  │ - Search & Download API       │
    │  - Report Exporter           │  │ - Pre-packaged SaaS Index     │
    └───────────────┬──────────────┘  └──────────────┬───────────────┘
                    │                                │
    ┌───────────────▼────────────────────────────────▼───────────────┐
    │                SQLite Cumulative Memory Store                   │
    │   Competitors | Intelligence Events | Snapshots | Pattern Insights│
    └───────────────────────────────┬────────────────────────────────┘
                                    │
    ┌───────────────────────────────▼────────────────────────────────┐
    │        CompeteMind AI Agent & Pattern Synthesis Engine         │
    │        - 6-Month Macro Pattern Spotter                         │
    │        - Google Gemini API / Fallback Intelligence Synthesizer │
    │        - Counter-Strategy & Executive Playbook Generator       │
    └────────────────────────────────────────────────────────────────┘
```

### Core Components

1. **Cumulative Memory Store (`db.py`)**:
   - Structured SQLite database logging moves across **Pricing**, **Features**, **Messaging**, and **Hiring**.
   - Maintains snapshots and historical timeframes for multi-month pattern recognition.

2. **Kaggle Datasets & API Integration (`kaggle_integration.py`)**:
   - Integrates Kaggle API search and dataset downloading.
   - Includes pre-packaged Kaggle Competitive Intelligence datasets (SaaS Pricing Index, Talent Hiring Velocity, Positioning Shifts) for out-of-the-box operation.

3. **Live Web Scraper & Differential Hashing Engine (`scraper.py`)**:
   - Monitors target competitor URLs (Homepage, Pricing, Careers).
   - Generates MD5 text hashes and differential diffs to automatically flag price updates and tagline changes.

4. **AI Pattern Spotter & Strategy Synthesizer (`ai_agent.py`)**:
   - Evaluates cumulative events across 30d, 90d, 180d, and 365d time windows.
   - Integrates Google Gemini API with a deterministic fallback engine to compute threat levels, confidence scores, and counter-strategy playbooks.

5. **Interactive Web Dashboard (`templates/index.html` & `static/js/app.js`)**:
   - Tailwind CSS dark-mode dashboard with Chart.js analytics.
   - Interactive 6-month memory timeline with category & time-window filter pills.
   - Competitor comparison matrix and instant move simulator.

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.9+
- Pip package manager

### Dependencies Installation
```bash
pip install flask pandas kaggle plotly requests beautifulsoup4
```

### Running the Application

1. **Initialize and Seed Cumulative Memory**:
   ```bash
   python seed_data.py
   ```

2. **Start the Web Dashboard & API Server**:
   ```bash
   python app.py
   ```

3. **Access Web Dashboard**:
   Open your browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

---

## 📊 Kaggle Datasets Integration

CompeteMind connects directly to Kaggle datasets:
- **Kaggle API Credentials**: Place your `kaggle.json` token in `~/.kaggle/access_token` or set the `KAGGLE_API_TOKEN` environment variable.
- **Offline / Built-in Datasets**: If Kaggle API credentials are not provided, CompeteMind uses built-in competitive datasets so you can test pattern synthesis right away.

---

## 📜 API Endpoints Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `GET /` | `GET` | Serves the interactive Web Dashboard UI |
| `GET /api/dashboard/stats` | `GET` | Retrieves aggregate metrics and category breakdown |
| `GET /api/competitors` | `GET / POST` | Fetch or add new tracked competitors |
| `GET /api/timeline` | `GET` | Query cumulative timeline events (filter by `days` & `category`) |
| `POST /api/analyze/patterns` | `POST` | Execute AI Pattern Spotter across 180-day memory |
| `GET /api/kaggle/search` | `GET` | Search competitive datasets on Kaggle |
| `POST /api/kaggle/import` | `POST` | Import Kaggle dataset CSV into cumulative memory |
| `POST /api/ingest/scrape` | `POST` | Trigger live URL differential scan for price/messaging shifts |
| `POST /api/simulate` | `POST` | Inject a simulated competitor move to test real-time pattern updates |
| `GET /api/export/report` | `GET` | Download Markdown Executive Intelligence Briefing |
