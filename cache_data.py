import requests
import time
import json
from bs4 import BeautifulSoup
import re
import datetime
import pandas as pd
from tqdm import tqdm
from database_utils import write_to_data_base, create_tables,query_db
import os
import sqlite3

BASE_URL = "https://www.metacritic.com/browse/games/release-date/available/{}/metascore"
GAME_BASE_URL = "https://www.metacritic.com"
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

verbose_cache = False


def load_cache(cache_file_name):
    '''Load cache file

    Returns
    -------
    dict
        cache file
    '''
    try:
        cache_file = open(cache_file_name, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache


def save_cache(cache, cache_file_name):
    '''Save cache file

    Parameters
    ----------
    cache: dict
        cache file

    Returns
    -------
    none
    '''
    cache_file = open(cache_file_name, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()


def make_url_request_using_cache(url, cache):
    '''Get html from the url using cache

    Parameters
    ----------
    url: string
        url to get
    cache: dict
        cache file

    Returns
    -------
    string
        html content
    '''
    if (url in cache.keys()):  # the url is our unique key
        if verbose_cache:
            print("Using cache")
        return cache[url]
    else:
        if verbose_cache:
            print("Fetching")
        time.sleep(0.25)
        response = requests.get(url, headers=headers)
        cache[url] = response.text
        return cache[url]


def get_games_single_page(page_context):
    soup = BeautifulSoup(page_context, 'html.parser')
    titles = soup.find_all('td', class_='clamp-summary-wrap')
    game_list = []
    game_urls = []
    for title in titles:
        try:
            score = title.find('div', class_=re.compile('metascore_w large.*')).text
            score = int(score)
        except:
            score = None
        game_title = title.find('a', class_='title')
        name = game_title.text.strip()
        game_url = game_title['href']
        details = title.find("div", class_='clamp-details')
        launch_date = details.find('span', recursive=False).text
        launch_date = datetime.datetime.strptime(launch_date, "%B %d, %Y").date()
        platform = details.find('span', class_='data', ).text.strip()
        try:
            user_score = title.find('div', class_=re.compile('metascore_w user large.*')).text
            user_score = float(user_score)
        except:
            user_score = None
        game_list.append([name, launch_date, platform, score, user_score])
        game_urls.append(game_url)
    return game_list, game_urls


def get_game_detail_info(game_page_context):
    soup = BeautifulSoup(game_page_context, 'html.parser')
    try:
        developer = soup.find('li', class_="summary_detail developer").find("span", class_='data')
        developers=developer.find_all('a',class_='button')
        developer_names = [dev.text.strip() for dev in developers]
        developers={dev.text.strip():GAME_BASE_URL+dev['href'] for dev in developers}
    except:
        developer_names = []
        developers={}
    try:
        genres = soup.find('li', class_="summary_detail product_genre").find_all("span", class_='data')
        genres = [x.text.strip() for x in genres]
    except:
        genres = []
    try:
        num_of_players = soup.find('li', class_="summary_detail product_players").find("span",
                                                                                       class_='data').text.strip()
        if num_of_players == 'No Online Multiplayer':
            num_of_players = 0
        else:
            num_of_players = num_of_players.split(' ')[-1]
            num_of_players = int(num_of_players)
    except:
        num_of_players = None
    try:
        ratings = soup.find('li', class_="summary_detail product_rating").find("span", class_='data').text.strip()
    except:
        ratings = None
    try:
        detail_critic_reviews = soup.find('div', class_='module reviews_module critic_reviews_module')
        critic_reviews_counts = detail_critic_reviews.find_all('span', class_='count')
        critic_reviews_counts = [int(x.text.strip()) for x in critic_reviews_counts]
        critic_reviews_count_total = sum(critic_reviews_counts)
        critic_reviews_count_pos_percentage = critic_reviews_counts[0] / critic_reviews_count_total
    except:
        critic_reviews_count_total = None
        critic_reviews_count_pos_percentage = None
    try:
        detail_user_reviews = soup.find('div', class_='module reviews_module user_reviews_module')
        user_reviews_counts = detail_user_reviews.find_all('span', class_='count')
        user_reviews_counts = [int(x.text.strip().replace(",", "")) for x in user_reviews_counts]
        user_reviews_count_total = sum(user_reviews_counts)
        user_reviews_count_pos_percentage = user_reviews_counts[0] / user_reviews_count_total
    except:
        user_reviews_count_total = None
        user_reviews_count_pos_percentage = None

    return [developer_names, num_of_players, ratings,
            critic_reviews_count_total, critic_reviews_count_pos_percentage,
            user_reviews_count_total, user_reviews_count_pos_percentage,
            genres],developers


def get_game_infos_by_platform(url, cache):
    first_page = make_url_request_using_cache(url, cache)
    soup = BeautifulSoup(first_page, 'html.parser')
    last_page = soup.find('li', class_="page last_page")
    try:
        page_num = last_page.find('a').text
    except:
        page_num = 1
    all_games = []
    all_games_urls = []
    for page in range(int(page_num)):
        page_url = url + f"?page={page}"
        page_context = make_url_request_using_cache(page_url, cache)
        games_single_page, games_single_page_urls = get_games_single_page(page_context)
        all_games.extend(games_single_page)
        all_games_urls.extend(games_single_page_urls)
    all_developers=dict()
    for i in tqdm(range(len(all_games))):
        game_url = GAME_BASE_URL + all_games_urls[i]
        game_page_context = make_url_request_using_cache(game_url, cache)
        game_detail_info,developers=get_game_detail_info(game_page_context)
        all_games[i].extend(game_detail_info)
        all_developers.update(developers)
    return all_games,all_developers


def get_existing_companies(db_path):
    if not os.path.isfile(db_path):
        return {}
    try:
        response=query_db("SELECT CompanyId,CompanyName From Companies",db_path)
        developers={r[1]:r[0] for r in response}
    except sqlite3.OperationalError:
        developers={}
    return developers

def get_info_companies(developers,cache):
    result=[]
    for dev,url in tqdm(developers):
        try:
            page=make_url_request_using_cache(url,cache)
            soup=BeautifulSoup(page,'html.parser')
            count=soup.find("div",class_='reviews_total').find('span',class_='count').text
            count=count.replace(",","")
            count=int(count)
        except:
            count=None
        result.append([dev,url,count])
    return result

def cache_result_by_platform(platform,cache_path,db_path):
    cache=load_cache(cache_path)
    url=BASE_URL.format(platform)
    print("Fetching data for games")
    game_infos,all_developers=get_game_infos_by_platform(url,cache)
    #add new developers into database
    existing_developers=get_existing_companies(db_path)
    new_developers=[]
    count=len(existing_developers)
    for developer in all_developers:
        if developer not in existing_developers:
            count+=1
            existing_developers[developer]=count
            new_developers.append([developer,all_developers[developer]])
    print("Fetching data for developers")
    new_developers_records=get_info_companies(new_developers,cache)
    save_cache(cache,cache_path)
    create_tables(db_path)
    write_to_data_base(new_developers_records,game_infos,existing_developers,db_path)
    print("Success")





