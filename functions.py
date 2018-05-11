from bs4 import BeautifulSoup
import html5lib
import requests


def get_data():
    """ Example data fetch function, rewrite your own! """
    data = []
    url = "https://www.iltalehti.fi"
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html5lib")
    most_read = soup.find("div", id="iltab_tuoreimmat-kaikki")

    for news in most_read.find_all("p"):
        item = {}
        href = news.find("a").get("href")
        link = url + href
        text = news.find("a").text

        # Identifier for in memory database
        item["identifier"] = href

        # Message to be sent to chats
        item["message"] = "{} [linkki]({})".format(text, link)
        data.append(item)

    return data
