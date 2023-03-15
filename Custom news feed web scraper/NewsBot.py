import os
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import time
from datetime import datetime

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))

Excepted_Countries = []

# user email address
sending = "example@gmail.com"

# user email password
pw = "examplepw"

receiving = "add@getpocket.com"

slack_hook = "https://hooks.slack.com/services/**************"


def add_to_pocket(content):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = ""
    msg['From'] = sending
    msg['To'] = receiving
    msg.attach(MIMEText(content))
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sending, pw)
    server.sendmail(sending, receiving, msg.as_string())
    server.quit()


def scrape_episodes():
    try:
        IMDb_Episodes = requests.get(
            "https://www.imdb.com/search/title/?title_type=tv_episode&user_rating=8.8,&num_votes=2500,&sort=release_date,desc&count=25",
            headers={"User-agent": "Mozilla/5.0"})
        IMDb_Episodes_html = BeautifulSoup(IMDb_Episodes.text, "html.parser")

        n_Episodes = 0
        for j in IMDb_Episodes_html.find_all("div", {"class": "lister-item mode-advanced"})[::-1]:
            url_string = "https://www.imdb.com" + j.h3.find_all("a")[1]["href"]
            url = url_string[:url_string.index('?ref_=adv_li_tt')]
            Series_url_string = "https://www.imdb.com" + j.h3.a["href"]
            Series_url = Series_url_string[:Series_url_string.index('?ref_=adv_li_tt')]
            if url not in Archive:
                Episode_page_html = BeautifulSoup(requests.get(Series_url).text, "html.parser")
                Country_1 = Episode_page_html.find("div", {"id": "titleDetails"}).find(
                    text=re.compile('Country')).parent.parent.a.text
                if Country_1 not in Excepted_Countries:
                    Ratings_url = url + "ratings"
                    Ratings_html = BeautifulSoup(requests.get(Ratings_url).text, "html.parser")
                    Votes_M = Ratings_html.find_all("td", {"class": "ratingTable"})[5]
                    if float(Votes_M.find("div", {"class": "bigcell"}).text) >= 9.0:
                        add_to_pocket(url)
                        Archive.append(url)
                        n_Episodes += 1
                    else:
                        Archive.append(url)
                else:
                    Archive.append(url)
        if n_Episodes == 0:
            print("No new episodes.")
        else:
            print("New Episode(s) - IMDb")
            requests.post(slack_hook,
                          json.dumps({"text": "   New Episode(s) - IMDb"}))
    except:
        requests.post(slack_hook,
                      json.dumps({"text": "   ERROR - Episodes"}))


def scrape_movies():
    try:
        # get the page html
        IMDb_Movies = requests.get(
            "https://www.imdb.com/search/title/?title_type=feature,tv_movie,documentary&user_rating=7.6,&num_votes=5000,&sort=release_date,desc&count=10",
            headers={"User-agent": "Mozilla/5.0"})
        IMDb_Movies_html = BeautifulSoup(IMDb_Movies.text, "html.parser")

        n_Movies = 0
        for j in IMDb_Movies_html.find_all("div", {"class": "lister-item mode-advanced"})[::-1]:
            url_string = "https://www.imdb.com" + j.h3.a["href"]
            url = url_string[:url_string.index('?ref_=adv_li_tt')]
            if url not in Archive:
                Movie_page_html = BeautifulSoup(requests.get(url).text, "html.parser")
                Country_1 = Movie_page_html.find("div", {"id": "titleDetails"}).find(
                    text=re.compile('Country')).parent.parent.a.text
                if Country_1 not in Excepted_Countries:
                    Ratings_url = url + "ratings"
                    Ratings_html = BeautifulSoup(requests.get(Ratings_url).text, "html.parser")
                    Votes_M = Ratings_html.find_all("td", {"class": "ratingTable"})[5]
                    Votes_F = Ratings_html.find_all("td", {"class": "ratingTable"})[10]
                    if float(Votes_M.find("div", {"class": "bigcell"}).text) >= 7.8:
                        N_M = float(Votes_M.a.text.replace(',', ''))
                        N_F = float(Votes_F.a.text.replace(',', ''))
                        if N_M / N_F < 4.0384 and float(Votes_M.find("div", {"class": "bigcell"}).text) < 8.0:
                            Archive.append(url)
                        else:
                            add_to_pocket(url)
                            Archive.append(url)
                            n_Movies += 1
                    else:
                        Archive.append(url)
                else:
                    Archive.append(url)
        if n_Movies == 0:
            print("No new movies.")
        else:
            print("New movie(s) - IMDb")
            requests.post(slack_hook,
                          json.dumps({"text": "   New movie(s) - IMDb"}))
    except:
        requests.post(slack_hook,
                      json.dumps({"text": "   ERROR - Movies"}))


def scrape_games():
    try:
        MC_Games = requests.get(
            "https://www.metacritic.com/browse/games/score/metascore/90day/all/filtered?sort=desc&view=condensed",
            headers={"User-agent": "Mozilla/5.0"})
        Games_html = BeautifulSoup(MC_Games.text, "html.parser")

        n_Games = 0
        for j in Games_html.find_all("tr", {"class": "expand_collapse"})[:20]:
            url = "https://www.metacritic.com" + j.a["href"]
            if url not in Archive:
                Games_MS = int(j.a.text)
                if Games_MS >= 90:
                    add_to_pocket(url)
                    Archive.append(url)
                    n_Games += 1
                else:
                    Archive.append(url)
        if n_Games == 0:
            print("No new games.")
        else:
            print("New game(s) - Metacritic")
            requests.post(slack_hook,
                          json.dumps({"text": "   New game(s) - Metacritic"}))
    except:
        requests.post(slack_hook,
                      json.dumps({"text": "   ERROR - Games"}))


def scrape_music():
    try:
        MC_Music = requests.get(
            "https://www.metacritic.com/browse/albums/release-date/new-releases/metascore?view=condensed",
            headers={"User-agent": "Mozilla/5.0"})
        Music_html = BeautifulSoup(MC_Music.text, "html.parser")

        n_Music = 0
        for j in Music_html.find_all("tr", {"class": "expand_collapse"})[:20]:
            url = "https://www.metacritic.com" + j.a["href"]
            if url not in Archive:
                Music_MS = int(j.a.text)
                if Music_MS >= 90:
                    add_to_pocket(url)
                    Archive.append(url)
                    n_Music += 1
                else:
                    Archive.append(url)
        if n_Music == 0:
            print("No new music albums.")
        else:
            print("New music album(s) - Metacritic")
            requests.post(slack_hook,
                          json.dumps({"text": "   New music album(s) - Metacritic"}))
    except:
        requests.post(slack_hook,
                      json.dumps({"text": "   ERROR - Music"}))


def scrape_economist():
    try:
        Econ = requests.get(
            "https://www.economist.com/graphic-detail/",
            headers={"User-agent": "Mozilla/5.0"})
        Econ_html = BeautifulSoup(Econ.text, "html.parser")

        n_Economist = 0
        for j in Econ_html.find_all("div", {"class": "teaser__text"})[::-1]:
            url = "https://www.economist.com" + j.h2.a["href"]
            if url not in Archive:
                add_to_pocket(url)
                Archive.append(url)
                n_Economist += 1
        if n_Economist == 0:
            print("No new Economist articles.")
        else:
            print("New article(s) - The Economist")
            requests.post(slack_hook,
                          json.dumps({"text": "   New article(s) - The Economist"}))
    except:
        requests.post(slack_hook,
                      json.dumps({"text": "   ERROR - The Economist"}))


def scrape_ted():
    try:
        # get the page html
        TED = requests.get(
            "https://www.ted.com/talks?sort=newest&topics%5B%5D=Science",
            headers={"User-agent": "Mozilla/5.0"})
        TED_html = BeautifulSoup(TED.text, "html.parser")

        n_TED = 0
        for j in TED_html.find_all("div", {"class": "media__message"})[:18]:
            url = "https://www.ted.com" + j.a["href"]
            if url not in Archive:
                # (sometimes this scrapes a loading page and fails):
                Talk = requests.get(url, headers={"User-agent": "Mozilla/5.0"})
                Talk_html = BeautifulSoup(Talk.text, "html.parser")
                try:
                    N_views = int(
                        ''.join(
                            list(filter(str.isdigit, Talk_html.find("span", text=re.compile('views')).parent.text))))
                    if N_views >= 500000:
                        add_to_pocket(url)
                        Archive.append(url)
                        n_TED += 1
                except:
                    print("TED talk page didn't load: " + url)
                    pass
        if n_TED == 0:
            print("No new TED talks.")
        else:
            print("New TED talk(s)")
            requests.post(slack_hook,
                          json.dumps({"text": "   New TED talk(s)"}))
    except:
        requests.post(slack_hook,
                  json.dumps({"text": "   ERROR - TED"}))





def scrape_reuters():
    try:
        options = Options()
        options.headless = True
        driver = webdriver.Firefox(options=options, service_log_path='/dev/null')
        driver.get(
            "https://www.reuters.com/?edition-redirect=uk")
        # sometimes this doesn't load properly and scraping fails. So wait 3s before reading html:
        time.sleep(3)
        pg = driver.page_source
        pg_html = BeautifulSoup(pg, "html.parser")

        n_ReutersUK = 0
        for j in pg_html.find("div", {"class": "TrendingStories-container-o6LEa"}).find_all("div", {
            "class": "StoryItem-content-19M61"})[:3]:
            url = "https://uk.reuters.com" + j.a["href"]
            if url not in Archive:
                add_to_pocket(url)
                Archive.append(url)
                n_ReutersUK += 1
        if n_ReutersUK == 0:
            print("No new uk.reuters articles.")
        else:
            print("New article(s) - uk.reuters")
            requests.post(slack_hook,
                          json.dumps({"text": "   New article(s) - uk.reuters"}))
        driver.quit()
    except:
        requests.post(slack_hook,
                      json.dumps({"text": "   ERROR - uk.reuters"}))


Dispatch_Scrape = {'Episodes': scrape_episodes,
                   'Movies': scrape_movies,
                   'Games': scrape_games,
                   'Music': scrape_music,
                   'Economist': scrape_economist,
                   'TED': scrape_ted,
                   'Reuters': scrape_reuters}

# read in Archive.csv file
df = pd.read_csv(os.path.join(THIS_FOLDER, "Archive.csv"))

# for each column (excluding index column),
for i in df.iloc[:, 1:]:
    # list all previous entries
    Archive = [x for x in df[i][:] if str(x) != 'nan']
    # If a column archive is getting full, replace it with the most recent 100 entries
    if len(Archive) > 900:
        Archive = Archive[-100:]
    # Dispatch scrape function
    Dispatch_Scrape[i]()
    # update column
    df.update(pd.DataFrame({i: Archive}))

# add timestamp and update .csv file
df.rename(columns={df.columns[0]: datetime.now().strftime("%d/%m/%Y %H:%M:%S")}, inplace=True)
df.to_csv(os.path.join(THIS_FOLDER, "Archive.csv"), index=False)
