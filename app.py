# app.py
import os
import re
import requests
from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)

# --- CONFIG ---
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")  # set this in Render environment variables
NEWS_API_TIMEOUT = 10  # seconds
DEFAULT_SYMBOLS = ["AAPL", "TSLA", "MSFT", "GOOGL"]
DEFAULT_PAGE_SIZE = 5  # number of articles per symbol to fetch

# --- KEYWORDS (from your screenshot) ---
KEYWORDS_4 = [
    "positive endpoint",
    "inside press release",
    "positive ceo statement",
    "positive italic font",  # kept from screenshot
]
KEYWORDS_3 = [
    "phase iii", "positive", "top-line", "top line", "significant", "demonstrates",
    "treatment", "drug trial", "drug trials", "agreement", "cancer", "partnership",
    "collaboration", "improvement", "successful", "billionaire", "carl icahn",
    "increase", "awarded", "primary"
]
KEYWORDS_2 = [
    "phase ii", "receives", "fda", "approval", "benefit", "beneficial", "fast track",
    "breakout", "acquire", "acquires", "acquisition", "expand", "expansion",
    "contract", "completes", "promising", "achieve", "achievement", "launches"
]
KEYWORDS_1 = [
    "phase i", "grants", "investors", "accepted", "new", "signs", "merger", "gain",
    "any large sum of money"
]

# Precompile regexes (lowercase matching)
def compile_kw_list(kw_list):
    return [re.compile(r"\b" + re.escape(k.lower()) + r"\b") for k in kw_list]

KW4_RE = compile_kw_list(KEYWORDS_4)
KW3_RE = compile_kw_list(KEYWORDS_3)
KW2_RE = compile_kw_list(KEYWORDS_2)
KW1_RE = compile_kw_list(KEYWORDS_1)

# --- Helpers ---
def rate_title(title: str) -> int:
    """Return 4,3,2,1 or 0 (0 means no relevant keywords found). Priority: 4>3>2>1."""
    if not title:
        return 0
    t = title.lower()

    if any(r.search(t) for r in KW4_RE):
        return 4
    if any(r.search(t) for r in KW3_RE):
        return 3
    if any(r.search(t) for r in KW2_RE):
        return 2
    if any(r.search(t) for r in KW1_RE):
        return 1
    return 0

def fetch_news_for_symbol(symbol: str, page_size: int = DEFAULT_PAGE_SIZE):
    """Fetch recent news headlines for a symbol using NewsAPI.org"""
    if not NEWS_API_KEY:
        return {"error": "No NEWS_API_KEY configured."}

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": symbol,
        "pageSize": page_size,
        "sortBy": "publishedAt",
        "language": "en",
        "apiKey": NEWS_API_KEY,
    }
    try:
        resp = requests.get(url, params=params, timeout=NEWS_API_TIMEOUT)
        resp.raise_for_status()
    except Exception as e:
        return {"error": f"fetch error: {e}"}

    data = resp.json()
    # early error from API
    if data.get("status") != "ok":
        return {"error": data.get("message", "unknown error from news api")}
    return data.get("articles", [])

# --- Routes ---
@app.route("/")
def home():
    return (
        "Stock-grade: GET /analyze?symbols=AAPL,TSLA&limit=5 — returns JSON of headlines rated 1-4 stars.\n"
        "Set NEWS_API_KEY environment variable before deploying."
    )

@app.route("/analyze")
def analyze():
    """
    Query params:
      - symbols: comma-separated tickers (default uses DEFAULT_SYMBOLS)
      - limit: per-symbol fetch limit (default DEFAULT_PAGE_SIZE)
    """
    symbols_param = request.args.get("symbols", None)
    limit_param = request.args.get("limit", None)
    if symbols_param:
        symbols = [s.strip().upper() for s in symbols_param.split(",") if s.strip()]
    else:
        symbols = DEFAULT_SYMBOLS[:]

    try:
        limit = int(limit_param) if limit_param else DEFAULT_PAGE_SIZE
        if limit < 1 or limit > 50:
            limit = DEFAULT_PAGE_SIZE
    except:
        limit = DEFAULT_PAGE_SIZE

    results = []
    for symbol in symbols:
        fetched = fetch_news_for_symbol(symbol, page_size=limit)
        if isinstance(fetched, dict) and fetched.get("error"):
            # return error structure for that symbol
            results.append({
                "symbol": symbol,
                "error": fetched["error"]
            })
            continue

        for art in fetched:
            title = art.get("title") or ""
            published_at = art.get("publishedAt")
            rating = rate_title(title)
            if rating == 0:
                # Skip headlines without any matching keywords. Remove this line if you want all headlines.
                continue

            results.append({
                "symbol": symbol,
                "title": title,
                "rating": rating,
                "stars": "★" * rating,
                "url": art.get("url"),
                "source": art.get("source", {}).get("name"),
                "publishedAt": published_at
            })

    # Sort by rating desc, then by publishedAt desc
    def sort_key(x):
        # rating first (higher better), then publishedAt (newer first)
        ts = x.get("publishedAt")
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00")) if ts else datetime.min
        except:
            dt = datetime.min
        return (-x.get("rating", 0), -dt.timestamp())

    sorted_results = sorted(results, key=sort_key)
    return jsonify(sorted_results)


if __name__ == "__main__":
    # For local testing only; Render will use Gunicorn
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)