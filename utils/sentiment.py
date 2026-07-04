import os
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = os.getenv('NEWS_API_KEY')

def get_news(company_name, num_articles=10):
    """Fetch latest news for a company"""
    url = f"https://newsapi.org/v2/everything"
    params = {
        'q': company_name,
        'language': 'en',
        'sortBy': 'publishedAt',
        'pageSize': num_articles,
        'apiKey': NEWS_API_KEY
    }
    try:
        response = requests.get(url, params=params)
        articles = response.json().get('articles', [])
        return articles
    except:
        return []

def analyze_sentiment(text):
    """Analyze sentiment of a text"""
    analyzer = SentimentIntensityAnalyzer()
    scores = analyzer.polarity_scores(text)
    
    compound = scores['compound']
    
    if compound >= 0.05:
        sentiment = 'Positive'
        emoji = '🟢'
    elif compound <= -0.05:
        sentiment = 'Negative'
        emoji = '🔴'
    else:
        sentiment = 'Neutral'
        emoji = '🟡'
    
    return {
        'sentiment': sentiment,
        'emoji': emoji,
        'score': compound,
        'positive': scores['pos'],
        'negative': scores['neg'],
        'neutral': scores['neu']
    }

def get_news_sentiment(company_name, num_articles=10):
    """Get news with sentiment analysis"""
    articles = get_news(company_name, num_articles)
    
    results = []
    for article in articles:
        title = article.get('title', '')
        description = article.get('description', '')
        text = f"{title} {description}"
        
        sentiment = analyze_sentiment(text)
        
        results.append({
            'title': title,
            'url': article.get('url', ''),
            'published': article.get('publishedAt', ''),
            'source': article.get('source', {}).get('name', ''),
            'sentiment': sentiment['sentiment'],
            'emoji': sentiment['emoji'],
            'score': sentiment['score']
        })
    
    return results

def get_overall_sentiment(company_name):
    """Get overall sentiment score for a company"""
    news = get_news_sentiment(company_name)
    
    if not news:
        return {'overall': 'Neutral', 'score': 0, 'news': []}
    
    avg_score = sum([n['score'] for n in news]) / len(news)
    
    positive = len([n for n in news if n['sentiment'] == 'Positive'])
    negative = len([n for n in news if n['sentiment'] == 'Negative'])
    neutral = len([n for n in news if n['sentiment'] == 'Neutral'])
    
    if avg_score >= 0.05:
        overall = 'Positive 🟢'
    elif avg_score <= -0.05:
        overall = 'Negative 🔴'
    else:
        overall = 'Neutral 🟡'
    
    return {
        'overall': overall,
        'score': avg_score,
        'positive_count': positive,
        'negative_count': negative,
        'neutral_count': neutral,
        'news': news
    }
