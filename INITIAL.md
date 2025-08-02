## FEATURE:


RSS Scraper (Python)

Fetches RSS feeds from target WordPress sites.

Extracts outbound links inside feed content.

Resolves redirects, strips all existing affiliate junk, and re-tags Amazon links.

Skips links pointing back to the original RSS domain.

Stores all results in data/deals.json (consumed by frontend).

Playwright JS Fallback

Installs headless Chromium.

Enabled only when USE_PLAYWRIGHT=true in vercel.env.

Renders JS-heavy pages when httpx fails.

React Frontend

Displays deals in native mobile app style with smooth panels.

Fetches data/deals.json and maps to DealCards.

Fully controlled by Vercel environment variables.

Vercel Environment Variable Hack

Misuses vercel.env for dynamic reconfiguration.

Site name, scraping URLs, affiliate tags, UI toggles — all set via env, enabling infinite site variations with no code changes.

CI/CD via GitHub Actions

Runs hourly cron job to scrape feeds.

Updates JSON and deploys frontend.

Caches Playwright browsers for faster runs.

## EXAMPLES:

2. EXAMPLES
2.1 Python: Pydantic Models (scraper/models.py)
python
Copy
Edit
from pydantic import BaseModel, HttpUrl
from typing import List

class ProcessedLink(BaseModel):
    original: HttpUrl
    resolved: HttpUrl
    final: HttpUrl
    is_affiliate: bool

class FeedItem(BaseModel):
    title: str
    link: HttpUrl
    processed_links: List[ProcessedLink]
2.2 Python: Playwright Module (scraper/js_fallback.py)
python
Copy
Edit
import os
from playwright.sync_api import sync_playwright

USE_PLAYWRIGHT = os.getenv("USE_PLAYWRIGHT", "false").lower() == "true"

def fetch_js_content(url: str) -> str:
    if not USE_PLAYWRIGHT:
        return ""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=15000)
            html = page.content()
            browser.close()
            return html
    except Exception as e:
        print(f"[!] Playwright failed: {e}")
        return ""
2.3 Python: Main Scraper (scraper/main.py)
python
Copy
Edit
import os, json, httpx, feedparser
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from models import FeedItem, ProcessedLink
from js_fallback import fetch_js_content, USE_PLAYWRIGHT

FEED_SOURCES = os.getenv("RSS_SOURCES", "").split(",")
AFFILIATE_TAGS = {
    "amazon.com": os.getenv("AMAZON_TAG_US", "mytag-20"),
    "amazon.ca": os.getenv("AMAZON_TAG_CA", "mytagca-20"),
}
OUTPUT_FILE = os.getenv("OUTPUT_JSON", "data/deals.json")
client = httpx.Client(follow_redirects=True, timeout=10)

def resolve_url(url: str) -> str:
    try:
        r = client.get(url)
        return str(r.url)
    except: return url

def clean_url(url: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    for bad in ["tag","affid","ref","utm_source","utm_medium","utm_campaign"]:
        query.pop(bad, None)
    return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))

def add_affiliate(url: str) -> str:
    for domain, tag in AFFILIATE_TAGS.items():
        if domain in url:
            base = clean_url(url)
            sep = "&" if "?" in base else "?"
            return f"{base}{sep}tag={tag}"
    return clean_url(url)

def fetch_content(url: str) -> str:
    try:
        r = client.get(url)
        if "<html" in r.text.lower(): return r.text
        raise ValueError("No HTML")
    except:
        return fetch_js_content(url) if USE_PLAYWRIGHT else ""

def process_link(original_url: str, rss_domain: str) -> ProcessedLink:
    resolved = resolve_url(original_url)
    if rss_domain in resolved:
        return ProcessedLink(original=original_url,resolved=resolved,final=resolved,is_affiliate=False)
    final = add_affiliate(resolved)
    return ProcessedLink(original=original_url,resolved=resolved,final=final,is_affiliate=final!=resolved)

def scrape_feed(feed_url: str):
    rss = feedparser.parse(feed_url); rss_domain = urlparse(feed_url).netloc; results = []
    for entry in rss.entries:
        links = []
        content_html = fetch_content(entry.link)
        soup = BeautifulSoup(content_html, "html.parser")
        for a in soup.find_all("a", href=True):
            links.append(process_link(a["href"], rss_domain).dict())
        results.append(FeedItem(title=entry.title, link=entry.link, processed_links=links).dict())
    return results

def main():
    all_items = [item for feed in FEED_SOURCES if feed.strip() for item in scrape_feed(feed.strip())]
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE,"w") as f: json.dump(all_items,f,indent=2)
    print(f"[+] Scraping complete → {OUTPUT_FILE}")

if __name__ == "__main__": main()
2.4 React: DealCard (frontend/src/components/DealCard.jsx)
javascript
Copy
Edit
export default function DealCard({ title, links }) {
  return (
    <div className="rounded-2xl p-4 shadow-md bg-white dark:bg-gray-900 m-2">
      <h2 className="text-lg font-bold mb-2">{title}</h2>
      {links.map((l, i) => (
        <a key={i} href={l.final} target="_blank" rel="noopener noreferrer"
           className="block bg-blue-600 text-white p-2 rounded-lg mb-1 hover:bg-blue-800">
          Buy Now →
        </a>
      ))}
    </div>
  );
}
2.5 React: Fetch Hook (frontend/src/utils/useDeals.js)
javascript
Copy
Edit
import { useEffect, useState } from "react";

export function useDeals() {
  const [deals, setDeals] = useState([]);
  useEffect(() => {
    fetch("/data/deals.json")
      .then(r => r.json())
      .then(setDeals)
      .catch(() => setDeals([]));
  }, []);
  return deals;
}


## DOCUMENTATION:

Pydantic – https://docs.pydantic.dev/latest/

Pydantic AI – https://ai.pydantic.dev/

BeautifulSoup – https://www.crummy.com/software/BeautifulSoup/bs4/doc/

httpx – https://www.python-httpx.org/

Playwright – https://playwright.dev/python/

React – https://react.dev/

Vercel Environment Variables – https://vercel.com/docs/environment-variables

GitHub Actions – https://docs.github.com/en/actions

## OTHER CONSIDERATIONS:
FILE STRUCTURE
bash
Copy
Edit
project-root/
├─ scraper/
│  ├─ main.py
│  ├─ models.py
│  ├─ js_fallback.py
├─ data/
│  └─ deals.json
├─ frontend/
│  ├─ src/
│  │  ├─ components/DealCard.jsx
│  │  ├─ utils/useDeals.js
│  │  └─ pages/index.jsx
├─ .github/workflows/scraper.yml
├─ requirements.txt
├─ vercel.env
└─ README.md



Playwright Overhead: Installed but triggered only when needed.

Dynamic Config: Every deployment can point to different feeds via vercel.env.

SEO: Consider SSR with Next.js later if you need indexing.

Performance: JSON is served statically by Vercel → blazing fast.

Scaling: Each repo + env file = one new affiliate site.

