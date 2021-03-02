"""
<tr ><th scope="row" class="center " data-stat="quarter" >1</th><td class="center " data-stat="qtr_time_remain" ><a href="#pbp_41.000">15:00</a></td><td class="center iz" data-stat="down" ></td><td class="center iz" data-stat="yds_to_go" ></td><td class="left " data-stat="location" csk="35" >KAN 35</td><td class="left " data-stat="detail" ><a name="pbp_41.000"></a><a href="/players/B/ButkHa00.htm">Harrison Butker</a> kicks off 68 yards, returned by <a href="/players/M/MickJa01.htm">Jaydon Mickens</a> for 26 yards (tackle by <a href="/players/O/ODanDo00.htm">Dorian O'Daniel</a>)</td><td class="right iz" data-stat="pbp_score_aw" >0</td><td class="right iz" data-stat="pbp_score_hm" >0</td><td class="right " data-stat="exp_pts_before" >0.000</td><td class="right " data-stat="exp_pts_after" >0.480</td></tr>

"""
import re
import util_2
import bs4
import queue
import json
import sys
import csv
import requests
import numpy as np
import re
from bs4 import BeautifulSoup,Comment

TEAM_ABBREVIATIONS = {'Browns' : ['CLE'], 'Ravens' : ['BAL'], 'Packers' : ['GNB'], 
                      'Vikings' : ['MIN'], 'Texans' : ['HOU'], 'Chiefs' : ['KAN'], 
                      'Seahawks' : ['SEA'], 'Falcons' : ['ATL'], 'Bears' : ['CHI'],
                      'Lions' : ['DET'], 'Chargers' : ['SDG', 'LAC'], 'Bengals' : ['CIN'],
                      'Buccaneers' : ['TAM'], 'Saints' : ['NOR'], 'Steelers' : ['PIT'],
                      'Giants' : ['NYG'], 'Football Team' : ['WAS'], 'Eagles' : ['PHI'],
                      'Jets' : ['NYJ'], 'Bills' : ['BUF'], 'Dolphins' : ['MIA'], 'Patriots' : ['NWE'],
                      'Colts' : ['IND'], 'Jaguars' : ['JAX'], 'Raiders' : ['OAK', 'RAI'], 'Panthers' : ['CAR'],
                      'Cardinals' : ['ARI'], '49ers' : ['SFO'], 'Cowboys' : ['DAL'], 'Rams' : ['STL', 'LAR'],
                      'Titans' : ['TEN'], 'Broncos' : ['DEN'], 'Redskins' : ['WAS']}

def team_mapper(year, soup, teams_raw):
    teams = []
    for team in teams_raw:
        if team == 'Chargers':
            if year < 2017:
                teams.append(TEAM_ABBREVIATIONS['Chargers'][0])
            else:
                teams.append(TEAM_ABBREVIATIONS['Chargers'][1])
        elif team == 'Raiders':
            if year < 2020:
                teams.append(TEAM_ABBREVIATIONS['Raiders'][0])
            else:
                teams.append(TEAM_ABBREVIATIONS['Raiders'][1])
        elif team == 'Rams':
            if year < 2016:
                teams.append(TEAM_ABBREVIATIONS['Rams'][0])
            else:
                teams.append(TEAM_ABBREVIATIONS['Rams'][1])
        else:
            teams.append(TEAM_ABBREVIATIONS[team][0])
    return teams


def coin_flipper(coiner, teams_raw):
    for word in coiner:
        if word in teams_raw:
            possession = word
        if word == '(deferred)':
            for x in teams_raw:
                if x is not possession:
                    possession = x
                    break
    return possession


def extractor(link, year=2021):
    request_obj = util_2.get_request(link)
    document = util_2.read_request(request_obj)
    soup = bs4.BeautifulSoup(document, "html5lib")

    title_lst = soup.find("title").text.split()
    teams_raw = [word for word in title_lst if word in TEAM_ABBREVIATIONS.keys()]
    mapped_teams = team_mapper(year, soup, teams_raw)

    comments = soup.find_all(text=lambda text:isinstance(text, Comment))

    for comment in comments:
        comment_soup = bs4.BeautifulSoup(comment, "html5lib")
        coin_toss = comment_soup.find("div", class_="table_container", id="div_game_info")
        
        if coin_toss is not None:
            coiner = coin_toss.find_all("td", {"class":"center", "data-stat":"stat"})[0].text.split()
            possession = coin_flipper(coiner, teams_raw)

        play_by_play = comment_soup.find("div", class_="table_container", id='div_pbp')
        if play_by_play is not None:
            break

    return play_by_play, possession, mapped_teams


def scrape_all(play_by, teams):
    master_lst = []
    quarter_tags = play_by.find_all("th", scope="row", class_="center")
    for row in quarter_tags:
        if str(type(row)) == "<class 'bs4.element.Tag'>":
            sub_lst = []

            sub_lst.append(row.text) # quarter
            sub_lst.append(row.nextSibling.text) # time
            sub_lst.append(row.nextSibling.nextSibling.text) # down
            sub_lst.append(row.nextSibling.nextSibling.nextSibling.text) # togo
            location = row.nextSibling.nextSibling.nextSibling.nextSibling.text.split()
            if len(location) > 1:
                sub_lst += ([location[0]], [location[1]]) # loc_team and loc_number
            else:
                sub_lst += ['', '']

            # extracting the play info without player names
            sub_play = row.nextSibling.nextSibling.nextSibling.nextSibling.nextSibling
            string = ''
            for sub in sub_play.contents:
                if str(type(sub)) == "<class 'bs4.element.NavigableString'>":
                    string += sub
                else:
                    string += '!??!'

            sub_lst.append(string)

            sub_lst.append(sub_play.nextSibling.text) # away score
            sub_lst.append(sub_play.nextSibling.nextSibling.text) # home score
            sub_lst.append(sub_play.nextSibling.nextSibling.nextSibling.text) # epb
            sub_lst.append(sub_play.nextSibling.nextSibling.nextSibling.nextSibling.text) # epa

            try:
                variable = row.parent['class']
            except KeyError:
                variable = []
            if variable is not None:
                if switch == 0:
                    switch = 1
                else:
                    switch = 0
            sub_lst.append(teams[switch])
                #print("at divider")

            master_lst.append(sub_lst)
    
    return master_lst


def play_classifier(numpy_array):
    lst = ['deep left', 'deep middle', 'deep right', 'short left', 'short right', 'short middle']

    detail_column = numpy_array[:, 9].tolist()
    numpy_array = np.delete(numpy_array, 9, 1)
    numpy_array = np.delete(numpy_array, 11, 1)

    play_classify = []
    for play in detail_column:
        play_info = []
        try:
            play_type = re.findall('(?<=|||)[a-z]+', play)[0] #find a way to handle special cases
        except IndexError:
            play_type = None
        if play_type == 'pass':
            play_info.append('pass')
            try:
                success = re.findall('(?<=pass)[a-z]+', play)[0]
            except IndexError:
                success = None
            if success == 'complete':
                try:
                    yardage = re.findall('((?<=for)[0-9]+(?=(yard|yards)|no gain)', play)[0]
                except IndexError:
                    yardage = None
                if yardage == None:
                    play_info += [''] * 2
                else:
                    if yardage == 'no gain':
                        yardage = 0
                    try:
                        location = re.findall('(?<=complete)[a-z]+ [a-z]+', play)[0]
                    except IndexError:
                        location = None
                    if location in lst:
                        play_info.append(location)
                        play_info.append(yardage)
                    else:
                        play_info += [''] * 2
            elif success == 'incomplete':
                yardage = '0'
                try:
                    location = re.findall('(?<=complete)[a-z]+ [a-z]+', play)[0]
                except IndexError:
                    location = None
                if location in lst:
                    play_info.append(location)
                    play_info.append(str(yardage))
                else:
                    play_info += [''] * 2
            else:
                play_info += [''] * 2
        elif play_type == ('up' or 'left' or 'right'):
            play_info.append('run')
            if play_type == 'up':
                play_type = 'middle'
            play_info.append(play_type)
            try:
                yardage = re.findall('((?<=for)[0-9]+(?=(yard|yards)|no gain)', play)[0]
            except IndexError:
                yardage = None
            if yardage == None:
                play_info.append('')
            else:
                if yardage == 'no gain':
                    yardage = 0
                play_info.append(str(yardage))
        else:
            play_info += [''] * 3
        no_play = re.findall('no play', play)
        if no_play != []:
            play_info = [''] * 3
        play_classify.append(play_info)

    detail_array = np.array(play_classify)
    master_array = np.concatenate(numpy_array, detail_array, axis=1)

