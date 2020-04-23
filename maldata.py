'''
Retrieval functions for MyAnimeList (MAL)
'''
## load libraries

import numpy as np
import pandas as pd

from bs4 import BeautifulSoup
import requests
import time, os

def loadtopanime(page_num):
    '''
    Load the top anime from MAL based on page_num, 50 per page
    So X = (page_num - 1) * 50 + 1) to (page_num * 50)
    Returns a soup of the list of X top anime on page_num
    '''
    limit = (page_num - 1) * 50
    url = "https://myanimelist.net/topanime.php?limit=" + str(limit)
    response = requests.get(url)
    if response.status_code != 200:
        print('Enountered', response.status_code, 'error while reading page', page_num , 'of MAL Top Anime')
    else:
        return BeautifulSoup(response.text, 'html5lib').find_all(class_="detail")
    
def initEntry_top(soup):
    '''
    Takes the soup of an entry in the MAL top 50
    Returns a dictionay entry with Title and URL of the anime
    '''
    entry = {}
    entry['Title'] = soup.find(class_="hoverinfo_trigger").text
    entry['URL'] = soup.find(class_="hoverinfo_trigger").get('href')
    return entry

def retrieveEntry(entry):
    '''
    Takes a dictionary that has URL and Title of the MAL anime
    Returns a soup of the anine page in question
    '''
    response = requests.get(entry['URL'])
    if response.status_code != 200:
        print('Encountered ' + str(response.status_code) + ' error reading ' + entry['Title'])
        return -1
    else:
        return BeautifulSoup(response.text, 'html5lib')

def retrieveSidebar(anime_dict, soup):
    '''
    Returns anime_dict with additional raw data for the sidebar of the anime entry 
    '''
    sidebar = soup.find(id='content')
    headers = sidebar.find_all(class_="dark_text")
    for header in headers:
        column_name = header.text.strip()[:-1]
        # print(column_name) # error-checking
        entry = header.next_sibling.strip()
        # print(entry) # error-checking
        if(entry.strip() == "None found,"): # no entries
            entry = []
        elif(entry == ""):
            # special case for score
            if(column_name == 'Score'):
                entry = header.findNext().text
            else:
                entry_soup = header.findNext('a')
                # print(entry_soup.text, " ||| ", entry_soup.findNext('a'), " ||| ", entry_soup.findNext().name) # error-checking
                
                # create a list of items if more than one entry; signifed by the plural in column_name
                if(column_name[-1] != 's'):
                    entry = entry_soup.text
                else:
                    entry = [entry_soup.text]
                    while(entry_soup.findNext().name != 'div'):
                        entry_soup = entry_soup.findNext('a')
                        entry.append(entry_soup.text)
        anime_dict[column_name] = entry
        # print('---')
    return anime_dict

def ppDuration(duration_entry):
    '''
    Takes in the raw duration entry in the form (xx min.) (xx hr.) (per ep)
    Returns total number of minutes per episode
    '''
    duration_array = duration_entry.split()
    duration_norm = 0
    if 'min.' in duration_array:
        duration_norm += int(duration_array[duration_array.index('min.') - 1])
    if 'hr.' in duration_array:
        duration_norm += 60 * int(duration_array[duration_array.index('hr.') - 1])
    return duration_norm

def ppAired(anime_dict):
    '''
    Takes in the original anime sidebar dictionary
    Return the dictionary with 'Started' and 'Ended' columns added in Timestamp format
    '''
    def toDatetime(date_string):
        try:
            try:
                return pd.to_datetime(aired_array[0], format="%b %d, %Y")
            except:
                try:
                    return pd.to_datetime(aired_array[0], format="%b, %Y")
                except:
                    return pd.to_datetime(aired_array[0], format="%Y")
        except:
            return np.nan

    aired_array = anime_dict['Aired'].split(' to ')
    anime_dict['Started'] = toDatetime(aired_array[0])
    if len(aired_array) > 1:
        anime_dict['Ended'] = toDatetime(aired_array[1])
    return anime_dict

def remove_commas(input_str):
    return int(input_str.strip().replace(',',''))

def ppSidebar(sidebar_dict):
    '''
    Postprocessing of MAL sidebar
    Take in the unprocessed sidebar dictionary
    Return the processed sidebar dictionary
    '''

    if(sidebar_dict['Episodes'] == 'Unknown'):
        sidebar_dict['Episodes'] = np.nan
    else:
        sidebar_dict['Episodes'] = int(sidebar_dict['Episodes'])
    sidebar_dict['Duration'] = ppDuration(sidebar_dict['Duration'])
    sidebar_dict = ppAired(sidebar_dict)
    sidebar_dict['Members'] = remove_commas(sidebar_dict['Members'])
    sidebar_dict['Favorites'] = remove_commas(sidebar_dict['Favorites'])

    return sidebar_dict

def retrieveTopbar(anime_dict, soup):
    '''
    Retrieves the score and voters from the topbar of the anime entry
    Return the modified anime_dict
    '''

    topbar = soup.find(class_='anime-detail-header-stats')
    
    if(anime_dict['Score'] == 'N/A'):
        anime_dict['Score'] = np.nan 
        anime_dict['Voters'] = np.nan # no score means no one voted
    else:
        anime_dict['Score'] = float(topbar.find(class_='score-label').text)
        anime_dict['Voters'] = remove_commas(topbar.find(class_='score').get('data-user').split()[0])

    return anime_dict

def retrieveRelated(anime_dict, soup):
    '''
    Retrieves related anime from the anime entry
    Returns the modified anime_dict
    '''
    related = soup.find(class_='anime_detail_related_anime')
    if(related is None): # nothing to add, so return
        return anime_dict
    related_rows = related.find_all('tr')
    for item in related_rows:
        header = item.find('td').text.strip()[:-1]
        entry = item.find('td').find_next().text.strip()
        anime_dict[header] = [item.strip() for item in entry.split(',')]
    
    return anime_dict

def createdict_top(soup):
    '''
    Takes in the soup of top anime and returns a dictionary list 
    '''
    mal_top = []
    for anime_soup in soup:

        # proceses the entry in the top 50 page(s) and gets the related page
        mal_entry = initEntry_top(anime_soup) 
        soup_mal_entry = retrieveEntry(mal_entry)
        
        # processes the anime page
        mal_entry = retrieveSidebar(mal_entry, soup_mal_entry)
        mal_entry = ppSidebar(mal_entry)
        mal_entry = retrieveTopbar(mal_entry, soup_mal_entry)
        mal_entry = retrieveRelated(mal_entry, soup_mal_entry)

        mal_top.append(mal_entry)
    
    return mal_top

def loadanime_char(page_num, char):
    '''
    Load the first X anime starting with char based on page number, 50 per page
    So X = (page_num - 1) * 50 + 1) to (page_num * 50)
    To load anime with non-alphabetical starts, use '.'
    Returns a soup of the list of the first X anime starting with char
    '''
    limit = (page_num - 1) * 50
    url = "https://myanimelist.net/anime.php?letter=" + char + "&show=" + str(limit)
    response = requests.get(url)
    if response.status_code != 200:
        print('Encountered', response.status_code, 'error while reading page', page_num , 'of MAL anime starting with', char)
    else:
        return BeautifulSoup(response.text, 'html5').find_all(class_="picSurround")

def initEntry_char(soup):
    '''
    Takes the soup of an entry in the MAL alphabetical list
    Returns a dictionay entry with Title and URL of the anime
    '''
    entry = {}
    entry['Title'] = soup.find("img").get('alt')
    entry['URL'] = soup.get('href')
    return entry

def createdict_firstchar(soup):
    '''
    Takes in the soup of first X anime starting with char and returns a dictionary list 
    '''
    mal_firstchar = []
    for anime_soup in soup:

        anime_soup = anime_soup.find(class_="hoverinfo_trigger")

        # proceses the entry in the top 50 page and gets the related page
        mal_entry = initEntry_char(anime_soup) 
        soup_mal_entry = retrieveEntry(mal_entry)
        
        # processes the anime page
        mal_entry = retrieveSidebar(mal_entry, soup_mal_entry)
        mal_entry = ppSidebar(mal_entry)
        mal_entry = retrieveTopbar(mal_entry, soup_mal_entry)
        mal_entry = retrieveRelated(mal_entry, soup_mal_entry)

        mal_firstchar.append(mal_entry)
    return mal_firstchar
