import feedparser
import requests

def fetch_rss_news():
    sources = [
        {"name": "机器之心", "url": "https://www.jiqizhixin.com/feed"},
        {"name": "MIT Tech Review", "url": "https://www.technologyreview.com/top-stories/feed"},
        {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed"},
        {"name": "The Verge AI", "url": "https://www.theverge.com/ai/rss/index.xml"}
    ]
    
    news = []
    for src in sources:
        try:
            feed = feedparser.parse(src["url"])
            for entry in feed.entries[:3]:  # 每源取 3 条
                summary = entry.get('summary', '')
                if len(summary) > 100:
                    summary = summary[:100] + '...'
                news.append({
                    "source": src["name"],
                    "title": entry.title,
                    "link": entry.link,
                    "published": entry.get('published', ''),
                    "summary": summary
                })
        except Exception as e:
            continue
    
    # 按发布时间排序
    news.sort(key=lambda x: x.get('published', ''), reverse=True)
    return news[:10]  # 返回前 10 条

def main():
    news = fetch_rss_news()
    print("AI News Digest (RSS)")
    print("=" * 50)
    for i, item in enumerate(news, 1):
        print(f"{i}. {item['source']} - {item['title']}")
        print(f"   {item['summary']}")
        print(f"   {item['link']}\n")

if __name__ == "__main__":
    main()