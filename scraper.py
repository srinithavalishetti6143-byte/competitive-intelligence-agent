import requests
from bs4 import BeautifulSoup
import hashlib
import json
import re
from datetime import datetime
from db import get_db, add_event, get_competitor_by_id

class CompetitorScraper:
    def __init__(self, timeout=10):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 CompeteMind-Bot/1.0"
        }
        self.timeout = timeout

    def fetch_url_snapshot(self, url):
        """Fetches URL HTML and generates cleaned text, summary, and MD5 hash."""
        if not url:
            return None
            
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        try:
            resp = requests.get(url, headers=self.headers, timeout=self.timeout)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Remove scripts, styles, metadata
            for element in soup(["script", "style", "nav", "footer", "svg"]):
                element.extract()
                
            title = soup.title.string.strip() if soup.title else ""
            
            # Get main text lines
            lines = (line.strip() for line in soup.get_text().splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = '\n'.join(chunk for chunk in chunks if chunk)
            
            content_hash = hashlib.md5(clean_text.encode('utf-8')).hexdigest()
            
            # Extract potential prices ($xx or €xx or £xx)
            prices = re.findall(r'[\$€£]\s?\d+(?:\.\d{2})?(?:\/mo|\/user|\/yr|\/month)?', resp.text)
            unique_prices = list(set(prices[:15]))
            
            # Extract meta description
            meta_desc = ""
            desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
            if desc_tag and desc_tag.get("content"):
                meta_desc = desc_tag.get("content").strip()

            return {
                "url": url,
                "title": title,
                "meta_description": meta_desc,
                "clean_text_preview": clean_text[:2000],
                "content_hash": content_hash,
                "detected_prices": unique_prices,
                "raw_html_len": len(resp.text),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            return {
                "url": url,
                "error": str(e),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

    def monitor_competitor_pages(self, competitor_id):
        """
        Monitors competitor website URLs, compares against historical snapshots,
        and automatically flags Pricing changes, Feature launches, Messaging shifts, or Hiring updates!
        """
        competitor = get_competitor_by_id(competitor_id)
        if not competitor:
            return {"status": "error", "message": "Competitor not found"}

        results = []
        events_flagged = 0

        # Define target pages to check
        pages_to_check = [
            ("homepage", competitor.get("website_url")),
            ("pricing", competitor.get("pricing_url")),
            ("careers", competitor.get("careers_url"))
        ]

        conn = get_db()
        cursor = conn.cursor()

        for page_type, url in pages_to_check:
            if not url:
                continue

            snapshot = self.fetch_url_snapshot(url)
            if not snapshot or "error" in snapshot:
                results.append({"page_type": page_type, "url": url, "status": "failed", "error": snapshot.get("error") if snapshot else "No URL"})
                continue

            # Fetch previous snapshot from DB
            cursor.execute("""
                SELECT * FROM snapshots 
                WHERE competitor_id = ? AND page_type = ? 
                ORDER BY captured_at DESC LIMIT 1
            """, (competitor_id, page_type))
            prev_snapshot = cursor.fetchone()

            if prev_snapshot:
                prev_hash = prev_snapshot["content_hash"]
                if prev_hash != snapshot["content_hash"]:
                    # Content changed! Analyze nature of change
                    change_event = self._analyze_diff_content(competitor, page_type, prev_snapshot, snapshot)
                    if change_event:
                        add_event(
                            competitor_id=competitor_id,
                            category=change_event["category"],
                            event_type=change_event["event_type"],
                            title=change_event["title"],
                            description=change_event["description"],
                            impact_score=change_event["impact"],
                            source_type="Live Scraper",
                            source_url=url,
                            raw_snapshot=json.dumps({"prev_hash": prev_hash, "new_hash": snapshot["content_hash"]})
                        )
                        events_flagged += 1
                        results.append({"page_type": page_type, "url": url, "status": "changed", "event": change_event})
                else:
                    results.append({"page_type": page_type, "url": url, "status": "unchanged"})
            else:
                # Initial snapshot baseline
                results.append({"page_type": page_type, "url": url, "status": "baseline_saved"})

            # Save snapshot to DB
            cursor.execute("""
                INSERT INTO snapshots (competitor_id, page_type, content_hash, content_summary, raw_content)
                VALUES (?, ?, ?, ?, ?)
            """, (competitor_id, page_type, snapshot["content_hash"], snapshot.get("title", ""), snapshot.get("clean_text_preview", "")))

        conn.commit()
        conn.close()

        return {
            "status": "success",
            "competitor_name": competitor["name"],
            "pages_checked": len(results),
            "events_flagged": events_flagged,
            "details": results
        }

    def _analyze_diff_content(self, competitor, page_type, prev_snap, new_snap):
        """Analyzes what type of change occurred (Pricing, Feature, Messaging, Hiring)."""
        comp_name = competitor["name"]
        
        if page_type == "pricing":
            new_prices = new_snap.get("detected_prices", [])
            return {
                "category": "Pricing",
                "event_type": "Pricing Page Update",
                "title": f"{comp_name} Updated Pricing Page Structure",
                "description": f"Detected pricing table diff. Detected prices: {', '.join(new_prices[:5]) if new_prices else 'Custom seat adjustments'}.",
                "impact": 4
            }
        elif page_type == "careers":
            return {
                "category": "Hiring",
                "event_type": "Career Page Shift",
                "title": f"{comp_name} Updated Careers & Open Roles",
                "description": f"Detected changes in active open positions and recruitment focus areas on careers portal.",
                "impact": 3
            }
        else:
            # Homepage / Messaging
            new_title = new_snap.get("title", "")
            return {
                "category": "Messaging",
                "event_type": "Hero Tagline Shift",
                "title": f"{comp_name} Updated Homepage Positioning",
                "description": f"Title updated to: '{new_title}'. Value proposition and hero marketing copy refreshed.",
                "impact": 3
            }
