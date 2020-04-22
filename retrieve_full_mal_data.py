## load libraries

import numpy as np
import pandas as pd

from bs4 import BeautifulSoup
import requests
import time, os

def MAL_loadtopanime(page_num):
    '''
    Load the top anime from MAL based on page_num, 50 per page
    Returns a soup of the list of top anime on page_num
    '''
    limit = (page_num - 1) * 50
    url = "https://myanimelist.net/topanime.php?limit=" + str(limit)
    response = requests.get(url)
    if response.status_code != 200:
        print('Error reading page ', page_num , ' of MAL Top Anime')
    else:
        return BeautifulSoup(response.text, 'html5lib').find_all(class_="detail")
    
def MAL_initEntry_top(soup):
    '''
    Takes the soup of an entry in the MAL top 50
    Returns a dictionay entry with Title and URL of the anime
    '''
    entry = {}
    entry['Title'] = soup.find(class_="hoverinfo_trigger").text
    entry['URL'] = soup.find(class_="hoverinfo_trigger").get('href')
    return entry

def MAL_retrieveEntry(entry):
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

def MAL_retrieveSidebar(anime_dict, soup):
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

def MAL_ppDuration(duration_entry):
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

def MAL_ppAired(anime_dict):
    '''
    Takes in the original anime sidebar dictionary
    Return the dictionary with 'Started' and 'Ended' columns added in Timestamp format
    '''
    def MAL_toDatetime(date_string):
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
    anime_dict['Started'] = MAL_toDatetime(aired_array[0])
    if len(aired_array) > 1:
        anime_dict['Ended'] = MAL_toDatetime(aired_array[1])
    return anime_dict

def remove_commas(input_str):
    return int(input_str.strip().replace(',',''))

def MAL_ppSidebar(sidebar_dict):
    '''
    Postprocessing of MAL sidebar
    Take in the unprocessed sidebar dictionary
    Return the processed sidebar dictionary
    '''

    if(sidebar_dict['Episodes'] == 'Unknown'):
        sidebar_dict['Episodes'] = np.nan
    else:
        sidebar_dict['Episodes'] = int(sidebar_dict['Episodes'])
    sidebar_dict['Duration'] = MAL_ppDuration(sidebar_dict['Duration'])
    sidebar_dict = MAL_ppAired(sidebar_dict)
    sidebar_dict['Members'] = remove_commas(sidebar_dict['Members'])
    sidebar_dict['Favorites'] = remove_commas(sidebar_dict['Favorites'])

    return sidebar_dict

def MAL_retrieveTopbar(anime_dict, soup):
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

def MAL_retrieveRelated(anime_dict, soup):
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

def MAL_createdict_top(soup):
    '''
    Takes in the soup of top anime and returns a dictionary list 
    '''
    mal_top = []
    for anime_soup in soup:

        # proceses the entry in the top 50 page(s) and gets the related page
        mal_entry = MAL_initEntry_top(anime_soup) 
        soup_mal_entry = MAL_retrieveEntry(mal_entry)
        
        # processes the anime page
        mal_entry = MAL_retrieveSidebar(mal_entry, soup_mal_entry)
        mal_entry = MAL_ppSidebar(mal_entry)
        mal_entry = MAL_retrieveTopbar(mal_entry, soup_mal_entry)
        mal_entry = MAL_retrieveRelated(mal_entry, soup_mal_entry)

        mal_top.append(mal_entry)
    
    return mal_top

counter = 1

mal_soup = MAL_loadtopanime(counter)
mal_dict = MAL_createdict_top(mal_soup)
mal_df = pd.DataFrame(mal_dict)

print("loading MAL list", end="")

end_of_animelist = False
while not end_of_animelist:
    counter += 1
    mal_soup = MAL_loadtopanime(counter)
    if mal_soup is not None:
        mal_dict = MAL_createdict_top(mal_soup)
        mal_df = pd.concat([mal_df, pd.DataFrame(mal_dict)])
        print(".", end="")
    else:
        end_of_animelist = True
        print("done.")


mal_df.to_pickle('mal_full_list.pkl')