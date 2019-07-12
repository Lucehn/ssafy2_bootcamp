# -*- coding: utf-8 -*-
import re
import urllib.request
from bs4 import BeautifulSoup
from flask import Flask
from slack import WebClient
from slackeventsapi import SlackEventAdapter

from googletrans import Translator
import nltk
from random import *
from elice_utils import EliceUtils
elice_utils = EliceUtils()
from wordcloud import WordCloud
from collections import Counter
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from operator import itemgetter
import json
from slack.web.classes import extract_json
from slack.web.classes.blocks import *
from slack.web.classes.elements import *
from slack.web.classes.interactions import MessageInteractiveEvent
from slackeventsapi import SlackEventAdapter


# nltk.download('all')

SLACK_TOKEN = "xoxb-683333830481-678287587427-XvqbGu1CUZzXnmzrAbOKrNzg"
SLACK_SIGNING_SECRET = "4c629ba3d6c5dc477b853b54c59379b1"

app = Flask(__name__)
slack_events_adaptor = SlackEventAdapter(SLACK_SIGNING_SECRET, "/listening", app)
slack_web_client = WebClient(token=SLACK_TOKEN)

quest_list = []
mean = []
target = ""
url = ""
source_code = ""
soup = ""

def create_json(dictionary, filename):
    with open(filename, 'w') as file:
        json_string = json.dumps(dictionary)
        file.write(json_string)

def create_dict(filename):
    with open(filename) as file:
        json_string = file.read()
        return json.loads(json_string)

def make_tuple_sorted(filename):
    createdict = create_dict(filename)
    make_tuple = []
    for value in createdict:
        make_tuple.append((value, createdict[value]))
    return sorted(make_tuple, key=itemgetter(1), reverse=True)

def result_update(filename):
    global target
    createdict = create_dict(filename)
    if target in createdict:
        createdict[target] += 1
    else:
        createdict[target] = 1
    create_json(createdict, filename)

def show_stats(text):
    if text in "showsuccess":
        tuplesort = make_tuple_sorted("success.join")
    else:
        tuplesort = make_tuple_sorted("fail.json")
    result_dict = {}

    for value in tuplesort:
        if len(result_dict) > 9:
            break
        result_dict[value[0]] = value[1]

    top_list = []
    for value in result_dict:
        top_list.append("{}: {}회".format(value, result_dict[value]))

    return "\n".join(top_list)

def create_word():
    global url, source_code, soup
    randomvalue = randint(100000, 200000)
    wordid = "000" + str(randomvalue)

    url = "https://dic.daum.net/word/view.do?wordid=ekw" + wordid
    source_code = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(source_code, "html.parser")

    word = ""
    for data in soup.find("span", class_="txt_cleanword"):
        word = data.strip().lower()
    return word

def word_interpret(word):
    translator = Translator()
    return translator.translate(word, src='en', dest='ko').text

def length_check(word):
    if len(word) > 130:
        return True
    else:
        return False

def include_check(word, target):
    if word in target:
        return True
    else:
        return False

def change_morpheme(word):
    target = nltk.word_tokenize(word)
    temp = [""]
    for value in target:
        temp[0] = temp[0] + value + " "

    res = nltk.pos_tag(temp)
    return res[0][1]

def output_result(isSuccess, message):
    global target, mean
    if isSuccess:
        result_update("success.json")
        result = ["*정답입니다!*"]
    else:
        result_update("fail.json")
        result = ["*틀렸습니다!*"]
        result.append("정답은 *" + target + "*입니다")
    result.append(target + "의 의미는 [" + message + "] 입니다.")
    result = result + ""<"" + mean + "|" + "자세히..." + ">"""
    target = ""
    return result

def create_soup_with_url(url):
    handler = urllib.request.urlopen(url)
    source_code = handler.read().decode('utf-8')
    return BeautifulSoup(source_code, 'html.parser')

def create_soup_with_query(query):
    url = 'https://dic.daum.net/search.do?q=' + query
    return create_soup_with_url(url)

def create_soup_with_word_id(query):
    global mean
    mean = []
    for data in query.find_all("strong", class_="tit_cleansch"):
        mean.append("https://dic.daum.net/word/view.do?wordid=" + data.get('data-tiara-id'))
    return create_soup_with_url(mean[0])

def _crawl(text):
    mean = []
    soup = create_soup_with_query(text)
    soup2 = create_soup_with_word_id(soup)

    for word in soup2.find("ul", class_="list_mean").find_all("li"):
        for i in word.find_all("span"):
            mean.append(i.get_text())
    return ' '.join(mean)

def search_word(text):
    global url, source_code, soup, target, quest_list
    total = []
    target = ""
    quest_list = []

    if "endict" in text:
        word = create_word()

        while True:
            memory = []
            converselist = []

            for data in soup.find_all("span", class_="txt_ex"):
                if len(memory) > 9:
                    pass
                memory.append(data.get_text())

            for value in range(len(memory)):
                if value % 2 == 0:
                    converselist.append(memory[value].lower())

            try:
                quiz = converselist[randint(0, len(converselist) - 1)]
            except ValueError:
                continue
            else:
                if length_check(quiz):
                    continue

                if include_check(word, quiz):
                    total.append("문제 :  " + quiz.replace(word, "______"))
                else:
                    continue
                total.append("해석 : " + word_interpret(quiz))
                quest_list.append(word)
                target_morpheme = change_morpheme(word)
                target = word
            break

        while len(quest_list) < 4:
            word = create_word()
            if word in quest_list:
                continue

            morpheme = change_morpheme(word)

            if morpheme != target_morpheme:
                continue
            else:
                quest_list.append(word)

        quest_list = sorted(quest_list)

        for value in range(len(quest_list)):
            total.append(str(value+1) + "번: " + quest_list[value])

        return '\n'.join(total)
    else:
        return "문제풀기 : 'endict'\n정답top10보기 : 'showsuccess'\n오답top10보기 : 'showfail'"

def answer_word(text):
    global target, quest_list
    for x in range(1, 5):
        if str(x)+"번" in text:
            break
        if x==4:
            return "'1번', '2번', '3번', '4번' 중에서 골라주세요."

    answer = int(text[13:14])
    message = _crawl(target.replace(" ", "%20"))
    if quest_list[answer-1] == target:
        return '\n'.join(output_result(True, message))
    else:
        return  '\n'.join(output_result(False, message))

@slack_events_adaptor.on("app_mention")
def app_mentioned(event_data):
    channel = event_data["event"]["channel"]
    text = event_data["event"]["text"]
    global target, quest_list
    #block1 = ImageBlock(image_url="https://www.google.com/search?q=%EC%82%AC%EC%A7%84&hl=ko&tbm=isch&source=iu&ictx=1&fir=2wdyILA0Zmx-fM%253A%252C5ISubKh2j_RsaM%252C_&vet=1&usg=AI4_-kQ8uhK4R40v3ieEJRoND9aOC6tq_g&sa=X&ved=2ahUKEwjv2oqura3jAhWJVrwKHWEFDuUQ9QEwBXoECAQQBA#imgrc=r_lTXSdLKmPwjM:&vet=1", alt_text="이미지가안뜰때보이는문구")
    #block2 = ImageBlock(image_url="https://www.google.com/search?q=%EC%82%AC%EC%A7%84&hl=ko&tbm=isch&source=iu&ictx=1&fir=2wdyILA0Zmx-fM%253A%252C5ISubKh2j_RsaM%252C_&vet=1&usg=AI4_-kQ8uhK4R40v3ieEJRoND9aOC6tq_g&sa=X&ved=2ahUKEwjv2oqura3jAhWJVrwKHWEFDuUQ9QEwBXoECAQQBA#imgrc=lXJrh_Cvs_W8rM:&vet=1", alt_text="이미지가안뜰때보이는문구")
    #my_blocks = [block1, block2]

    if "showsuccess" in text or "showfail" in text:
        message = show_stats(text)
    elif target == "":
        message = search_word(text)
    else:
        message = answer_word(text)

    slack_web_client.chat_postMessage(
        channel=channel,
        text=message,
        #blocks=extract_json(my_blocks)
    )

@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"

if __name__ == '__main__':
    app.run('127.0.0.1', port=4040)