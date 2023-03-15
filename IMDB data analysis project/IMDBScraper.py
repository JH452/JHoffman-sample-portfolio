from bs4 import BeautifulSoup
import requests
import csv
import time
import re


# csv column headings
header = [['Rank','Title','url','Votes_10','Votes_9','Votes_8','Votes_7','Votes_6','Votes_5','Votes_4','Votes_3','Votes_2','Votes_1','Votes_M','Votes_F','AvgRating_M','AvgRating_F']]

# write csv file with headings
writer = csv.writer(open('IMDB_top1000.csv', 'w'))
writer.writerows(header)

# data exclusion criteria
exceptedCountries = ["India", "Bangladesh"]

# top 1000 titles is split into 4 web pages; process each in turn
for i in ["https://www.imdb.com/search/title/?groups=top_1000&sort=user_rating,desc&count=250&view=simple",
          "https://www.imdb.com/search/title/?groups=top_1000&sort=user_rating,desc&count=250&start=251&view=simple",
          "https://www.imdb.com/search/title/?groups=top_1000&sort=user_rating,desc&count=250&start=501&view=simple",
          "https://www.imdb.com/search/title/?groups=top_1000&sort=user_rating,desc&count=250&start=751&view=simple"]:
    time.sleep(2)
    # request and parse the top 1000 list
    pg = requests.get(i, headers={"User-agent": "Mozilla/5.0"})
    pg_html = BeautifulSoup(pg.text, "html.parser")
    # generate a list of move titles on the page
    if i == "https://www.imdb.com/search/title/?groups=top_1000&sort=user_rating,desc&count=250&view=simple":
        movieList = pg_html.find_all("div", {"class": "col-title"})[130:250]
    else:
        movieList = pg_html.find_all("div", {"class": "col-title"})[:250]
    for j in movieList:
        time.sleep(2)
        # request and parse the individual movie page
        title_string = str(j.a)
        url = "https://www.imdb.com" + title_string[9:title_string.index('?ref_=adv_li_tt">')]
        moviePageHtml = BeautifulSoup(requests.get(url).text, "html.parser")
        # check that movie isn't excluded
        country1 = moviePageHtml.find("div", {"id": "titleDetails"}).find(text=re.compile('Country')).parent.parent.a.text
        if country1 not in exceptedCountries:
            time.sleep(2)
            # 'line' is the list of data for this movie be written to the csv
            line = []
            # append the movie ranking (1 - 1000)
            try:
                line.append(int(j.find("span", {"class": "lister-item-index unbold text-primary"}).text[:-1]))
            except:
                line.append(1000)
            # append the movie title
            line.append(j.a.text)
            # append the movie IMDB page url
            line.append(url)
            # request and parse the ratings page for the movie
            ratingsPage = requests.get(url + "ratings", headers={"User-agent": "Mozilla/5.0"})
            ratingsPageHtml = BeautifulSoup(ratingsPage.text, "html.parser")
            # select number of user votes for ratings 1 to 10
            votes10_1 = ratingsPageHtml.find_all("div", {"class": "allText"})[3:33:3]
            # append each number of votes
            for k in votes10_1:
                line.append(int(''.join(ch for ch in str(k) if ch.isdigit())))
            # select and append number of ratings either M or F, and average rating either M or F
            votes_M = ratingsPageHtml.find_all("td", {"class": "ratingTable"})[5]
            votes_F = ratingsPageHtml.find_all("td", {"class": "ratingTable"})[10]
            line.append(int(votes_M.a.text.replace(',', '')))
            line.append(int(votes_F.a.text.replace(',', '')))
            line.append(float(votes_M.find("div", {"class": "bigcell"}).text))
            line.append(float(votes_F.find("div", {"class": "bigcell"}).text))
            # check correct format of line
            print(line[0])
            # write movie ratings data to csv
            writer.writerow(line)




