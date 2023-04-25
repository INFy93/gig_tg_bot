import json

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time


def get_gig_news() -> object:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0"
    }

    url = "https://crimeastar.net/archives/category/news_usual"
    req = requests.get(url, headers=headers)
    soup = BeautifulSoup(req.text, "lxml")

    articles = soup.find_all("article", class_="w-grid-item")

    last_news = {}
    for article in articles:
        article_title = article.find("h2", class_="post_title").find("a").text
        article_time = article.find("time", class_="post_date").get("datetime")
        date_from_iso = datetime.fromisoformat(article_time)
        date_time = datetime.strftime(date_from_iso, "%Y-%m-%d %H:%M:%S%z")
        article_date_timestamp = time.mktime(datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S%z").timetuple())
        article_link = article.find("h2", class_="post_title").find("a").get("href")
        article_id = article_link.split("/")[-1]
        last_news[article_id] = {
            "article_date_timestamp": article_date_timestamp,
            "article_title": article_title,
            "article_link": article_link
        }

    with open("news.json", "w", encoding="utf-8") as file:
        json.dump(last_news, file, indent=4, ensure_ascii=False)


def check_news_update():
    with open("news.json", encoding="utf-8") as file:
        news_list = json.load(file)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0"
    }

    url = "https://crimeastar.net/archives/category/news_usual"
    req = requests.get(url, headers=headers)
    soup = BeautifulSoup(req.text, "lxml")

    articles = soup.find_all("article", class_="w-grid-item")
    fresh_news = {}
    for article in articles:
        article_link = article.find("h2", class_="post_title").find("a").get("href")
        article_id = article_link.split("/")[-1]

        if article_id in news_list:
            continue
        else:
            article_title = article.find("h2", class_="post_title").find("a").text
            article_time = article.find("time", class_="post_date").get("datetime")
            date_from_iso = datetime.fromisoformat(article_time)
            date_time = datetime.strftime(date_from_iso, "%Y-%m-%d %H:%M:%S%z")
            article_date_timestamp = time.mktime(datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S%z").timetuple())
            news_list[article_id] = {
                "article_date_timestamp": article_date_timestamp,
                "article_title": article_title,
                "article_link": article_link
            }
            fresh_news[article_id] = {
                "article_date_timestamp": article_date_timestamp,
                "article_title": article_title,
                "article_link": article_link
            }
    with open("news.json", "w", encoding="utf-8") as file:
        json.dump(news_list, file, indent=4, ensure_ascii=False)

    return fresh_news


def main():
    # get_gig_news()
    print(check_news_update())


if __name__ == '__main__':
    main()
