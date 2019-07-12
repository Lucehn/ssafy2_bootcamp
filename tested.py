# json 패키지를 임포트합니다.
import json
from elice_utils import EliceUtils
elice_utils = EliceUtils()
from wordcloud import WordCloud
from collections import Counter
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from operator import itemgetter

def create_dict(filename):
    with open(filename) as file:
        json_string = file.read()
        return json.loads(json_string)


def create_json(dictionary, filename):
    with open(filename, 'w') as file:
        json_string = json.dumps(dictionary)
        file.write(json_string)

def make_tuple_sorted(filename):
    createdict = create_dict(filename)
    make_tuple = []
    for value in createdict:
        make_tuple.append((value, createdict[value]))
    return sorted(make_tuple, key=itemgetter(1), reverse=True)

def show_stats():
    tuplesort = make_tuple_sorted("fail.json")
    result_dict = {}

    for value in tuplesort:
        if len(result_dict) > 9:
            break
        result_dict[value[0]] = value[1]

    for value in result_dict:
        print("{}: {}회".format(value, result_dict[value]))

def show_tweets_by_month():
    tuplesort = make_tuple_sorted("fail.json")

    list_name = []
    list_count = []

    for value in tuplesort:
        if len(list_name) > 9:
            break
        list_name.append(value[0])
        list_count.append(value[1])

    plt.bar(list_name, list_count, align='center')
    plt.xticks(list_name, list_name)

    plt.savefig('graph.png')
    elice_utils = EliceUtils()
    elice_utils.send_image('graph.png')


def create_word_cloud():
    filename = 'fail.json'

    netflix_dict = create_dict(filename)

    trump_mask = np.array(Image.open('trump.png'))
    cloud = WordCloud(background_color='white', mask=trump_mask)
    cloud.fit_words(netflix_dict)
    cloud.to_file('cloud.png')
    elice_utils.send_image('cloud.png')

filename = 'fail.json'
filename = 'fail.json'

#value = input("값을 입력")

netflix_dict = create_dict(filename)

#if value in netflix_dict:
#    netflix_dict[value] += 1
#else:
#    netflix_dict[value] = 1

create_json(netflix_dict, filename)
updated_dict = create_dict(filename)
show_stats()
show_tweets_by_month()
create_word_cloud()