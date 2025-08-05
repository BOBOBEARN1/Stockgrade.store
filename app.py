from flask import Flask, jsonify
import requests

app = Flask(__name__)

NEWS_API_KEY = 'YOUR_NEWS_API_KEY'  # Replace with your actual API key
STOCK_SYMBOLS = ['AAPL', 'TSLA', 'MSFT', 'GOOGL']

# Define keyword lists by star rating
keywords_4_star = ['Positive Endpoint', 'Inside Press Release', 'Positive CEO Statement']
keywords_3_star = ['Phase III', 'Positive', 'Top-Line', 'Significant', 'Demonstrates', 'Treatment',
                   'Drug Trial', 'Agreement', 'Cancer', 'Partnership', 'Collaboration', 'Improvement',
                   'Successful', 'Billionaire', 'Carl Icahn', 'Increase', 'Awarded', 'Primary']
keywords_2_star = ['Phase II', 'Receives', 'FDA', 'Approval', 'Benefit', 'Beneficial', 'Fast Track',
                   'Breakout', 'Acquires', 'Acquisition', 'Expand', 'Expansion', 'Contract',
                   'Completes', 'Promising', 'Achieves', 'Achievement', 'Launches']
keywords_1_star = ['Phase I', 'Grants', 'Any Large Sum of Money', 'Investors', 'Accepted',
                   'New', 'Signs', 'Merger', 'Gain']

def fetch_news(symbol):
    url = f'https://newsapi.org/v2/everything?q={symbol}&apiKey={NEWS_API_KEY}&pageSize=5&sortBy=publishedAt'
    response = requests.get(url)
    return response.json().get('articles', [])

def rate_article(title):
    title_lower = title.lower()
    score = 0

    if any(kw.lower() in title_lower for kw in keywords_4_star):
        score = 4
    elif any(kw.lower() in title_lower for kw in keywords_3_star):
        score = 3
    elif any(kw.lower() in title_lower for kw in keywords_2_star):
        score = 2
    elif any(kw.lower() in title_lower for kw in keywords_1_star):
        score = 1

    return score

@app.route('/')
def analyze_news():
    all_news = []

    for symbol in STOCK_SYMBOLS:
        articles = fetch_news(symbol)
        for article in articles:
            title = article['title']
            rating = rate_article(title)
            if rating > 0:
                all_news.append({
                    'symbol': symbol,
                    'title': title,
                    'rating': f'{rating} ⭐',
                    'url': article['url']
                })

    # Sort by highest star rating
    sorted_news = sorted(all_news, key=lambda x: x['rating'], reverse=True)
    return jsonify(sorted_news)

if __name__ == '__main__':
    app.run()