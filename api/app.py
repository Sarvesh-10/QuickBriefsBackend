from flask import Flask,render_template
import requests
import nltk
import json
from newsapi.newsapi_client import NewsApiClient
import newspaper
from newspaper import Article
nltk.download('punkt')
Newsapi = NewsApiClient(api_key='cc10ab289d7a4bfaae76a9874cd6ee43')

app = Flask(__name__)

class News:
    author = 'Unknown'
    publishDetails =''
    title = ''
    url = ''
    urlToImage = ''
    description = ''
    summarizeNews = 'Summarized News'
    def __init__(self,author,publishDetails,title,url,urlToImage,desc):
        self.author = author
        self.publishDetails = publishDetails
        self.title = title
        self.url = url
        self.urlToImage = urlToImage
        self.description = desc




class NewsEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, News):
            return obj.__dict__
        return super().default(obj)





def formData(newsData):
    listOfNews = []
    for article in newsData['articles']:
        listOfNews.append(News(author=article['author'],publishDetails=article['publishedAt'],title=article['title'],url=article['url'],urlToImage=article['urlToImage'],desc=article['description']))
    return listOfNews


def summarize(listOfNews):
    for news in listOfNews:
        try:
            article = Article(news.url)
            article.download()
            article.parse()
            article.nlp()
            news.summarizeNews = article.summary
        except newspaper.ArticleException:
            print(newspaper.ArticleException.__name__)
            news.summarizeNews = news.description

    return listOfNews




@app.route('/')
def index():
    return "<h1>Add /sports or /business or /general or /health or /technology or /science</h1>"

@app.route('/get/<cat>')
def getNews(cat):
    newsData = Newsapi.get_top_headlines(language='en',category=cat)
    listOfNews = formData(newsData=newsData)
    listOfNews = summarize(listOfNews=listOfNews)
    jsonString =  json.dumps(listOfNews,cls=NewsEncoder)
    
    jsonObject = {
        "messageStatus":200,
        "articles":json.loads(jsonString)
    }
    return jsonObject
    





if __name__ == "__main__":
    app.run()



'''
1. categories
    i) general
    ii)Sports
    iii)Business
    iv)Entertainment
    v)Health
    ix)science
    x)Technology
    xiv)general    
'''






