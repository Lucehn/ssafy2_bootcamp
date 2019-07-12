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


# 크롤링 함수 구현하기
def _crawl_music_chart(text):
    if not "music" in text:
        return "`@<봇이름> music` 과 같이 멘션해주세요."

    # 여기에 함수를 구현해봅시다.
    url = "https://music.bugs.co.kr/chart"
    source_code = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(source_code, "html.parser")

    title = []
    artist = []

    for data in (soup.find_all("p", class_="title")):
        if len(title) > 9:
            break
        title.append(data.get_text().strip())

    for data in soup.find_all("p", class_="artist"):
        if len(artist) > 9:
            break
        temp = data.get_text().strip().split("\n")
        artist.append(temp[0])

    message = []

    for i in range(len(title)):
        message.append(str(i + 1) + "위 : " + title[i] + "/" + artist[i])

    return '\n'.join(message)


# 챗봇이 멘션을 받았을 경우
@slack_events_adaptor.on("app_mention")
def app_mentioned(event_data):
    channel = event_data["event"]["channel"]
    text = event_data["event"]["text"]

    message = _crawl_music_chart(text)
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
