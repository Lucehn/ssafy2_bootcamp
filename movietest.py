# -*- coding: utf-8 -*-
import re
import urllib.request

from bs4 import BeautifulSoup

from flask import Flask
from slack import WebClient
from slackeventsapi import SlackEventAdapter

SLACK_TOKEN = "xoxb-683333830481-678287587427-XvqbGu1CUZzXnmzrAbOKrNzg"
SLACK_SIGNING_SECRET = "4c629ba3d6c5dc477b853b54c59379b1"

app = Flask(__name__)
# /listening 으로 슬랙 이벤트를 받습니다.
slack_events_adaptor = SlackEventAdapter(SLACK_SIGNING_SECRET, "/listening", app)
slack_web_client = WebClient(token=SLACK_TOKEN)

namedic = {}

# 크롤링 함수 구현하기
def _crawl(text):
    # 여기에 함수를 구현해봅시다.
    if not "영화" in text and len(namedic)==0:
        return "'영화'단어를 입력하셔야 됩니다."
    elif "영화" in text:
        url = "https://movie.naver.com/movie/running/current.nhn"

        # URL 주소에 있는 HTML 코드를 soup에 저장합니다.
        source_code = urllib.request.urlopen(url).read()
        soup = BeautifulSoup(source_code, "html.parser")

        message = []
        link = []

        for data in soup.find_all("dt", class_="tit"):
            link.append(data.find("a")["href"].split("=")[1])

        for data in soup.find_all("dt", class_="tit"):
            temp = data.get_text().strip().split("\n")
            if len(temp) == 1:
                message.append(temp[0])
            else:
                message.append(temp[1])

        for value in range(len(message)):
            namedic[message[value]] = link[value]

        return '\n'.join(message)

    elif not text[13:] in namedic:
        return "해당 영화는 존재하지 않습니다"

    else:
        url = "https://movie.naver.com/movie/bi/mi/basic.nhn?code=" + namedic[text[13:]]
        source_code = urllib.request.urlopen(url).read()
        soup = BeautifulSoup(source_code, "html.parser")

        story = []
        for data in soup.find_all("p", class_="con_tx"):
            story.append(data.get_text().strip())

        return '\n'.join(story)


# 챗봇이 멘션을 받았을 경우
@slack_events_adaptor.on("app_mention")
def app_mentioned(event_data):
    channel = event_data["event"]["channel"]
    text = event_data["event"]["text"]

    message = _crawl(text)
    slack_web_client.chat_postMessage(
        channel=channel,
        text=message
    )


# / 로 접속하면 서버가 준비되었다고 알려줍니다.
@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"


if __name__ == '__main__':
    app.run('127.0.0.1', port=4040)
