from flask import Flask, jsonify
import requests
import nltk
import json
from newsapi.newsapi_client import NewsApiClient
import newspaper
from celery import Celery
from celery.schedules import crontab
import redis
from newspaper import Article

# Download required NLTK resources
nltk.download('punkt')

# Initialize NewsAPI client
Newsapi = NewsApiClient(api_key='cc10ab289d7a4bfaae76a9874cd6ee43')

# Redis client setup
redis_client = redis.Redis(host='quickbriefscache-nyc3n7.serverless.use1.cache.amazonaws.com', port=6379, decode_responses=True)

# Flask app setup
app = Flask(__name__)

# Celery configuration
app.config['CELERY_BROKER_URL'] = 'quickbriefscache-nyc3n7.serverless.use1.cache.amazonaws.com:6379:6379/0'
app.config['CELERY_RESULT_BACKENDS'] = 'quickbriefscache-nyc3n7.serverless.use1.cache.amazonaws.com:6379/0'
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

@celery.task(name='fetch_and_store_news')
def fetch_and_store_news():
    print("Fetching and storing news...")
    for category in CATEGORIES:
        newsData = Newsapi.get_top_headlines(language='en', category=category)
        if newsData and newsData['status'] == 'ok':
            listOfNews = formData(newsData=newsData)
            listOfNews = summarize(listOfNews=listOfNews)
            jsonString = json.dumps(listOfNews, cls=NewsEncoder)
            redis_key = f"news:{category}"
            redis_client.set(redis_key, jsonString, ex=3600)
            print(f"News for category '{category}' stored in Redis.")
        else:
            print(f"Failed to fetch news for category '{category}'.")

# Celery Beat schedule
celery.conf.beat_schedule = {
    'fetch_and_store_news': {
        'task': 'fetch_and_store_news',
        'schedule': crontab(minute=0, hour='*/2'),  # Every 30 seconds
    },
}



# News categories
CATEGORIES = ["business", "technology", "sports", "entertainment", "health"]

# News class for encapsulating news data
class News:
    def __init__(self, author, publishDetails, title, url, urlToImage, desc):
        self.author = author or 'Unknown'
        self.publishDetails = publishDetails or ''
        self.title = title or ''
        self.url = url or ''
        self.urlToImage = urlToImage or ''
        self.description = desc or ''
        self.summarizeNews = 'Summarized News'

# JSON encoder for News objects
class NewsEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, News):
            return obj.__dict__
        return super().default(obj)

# Helper function to process news data
def formData(newsData):
    listOfNews = []
    for article in newsData['articles']:
        listOfNews.append(News(
            author=article.get('author'),
            publishDetails=article.get('publishedAt'),
            title=article.get('title'),
            url=article.get('url'),
            urlToImage=article.get('urlToImage'),
            desc=article.get('description')
        ))
    return listOfNews

# Summarize news articles
def summarize(listOfNews):
    for news in listOfNews:
        if not news.url:
            continue
        try:
            article = Article(news.url)
            article.download()
            article.parse()
            article.nlp()
            news.summarizeNews = article.summary
        except newspaper.ArticleException:
            news.summarizeNews = news.description
    return listOfNews

# Task to fetch and store news in Redis

# celery.register_task(fetch_and_store_news)


# Flask routes


@app.before_first_request
def startup_task():
    """Trigger Celery task to fetch news at startup."""
    fetch_and_store_news.delay()

@app.route('/')
def index():
    return "<h1>Add /sports, /business, /general, /health, /technology, or /science</h1>"

@app.route('/get/<cat>')
def getNews(cat):
    try:
        redis_key = f"news:{cat}"
        cached_news = redis_client.get(redis_key)

        if cached_news:
            news_data = json.loads(cached_news)
            return jsonify({"messageStatus": 200, "articles": news_data})
        else:
            newsData = Newsapi.get_top_headlines(language='en', category=cat)
            if newsData and newsData['status'] == 'ok':
                listOfNews = formData(newsData=newsData)
                listOfNews = summarize(listOfNews=listOfNews)
                jsonString = json.dumps(listOfNews, cls=NewsEncoder)
                redis_client.set(redis_key, jsonString, ex=3600)
                return jsonify({"messageStatus": 200, "articles": json.loads(jsonString)})
            else:
                return jsonify({"messageStatus": 500, "message": "Failed to fetch news."}), 500
    except Exception as e:
        return jsonify({"messageStatus": 500, "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)