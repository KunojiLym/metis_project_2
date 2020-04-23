import pandas as pd

import maldata

counter = 1

print("loading MAL list", end="", flush=True)

mal_soup = maldata.loadtopanime(counter)
mal_dict = maldata.createdict_top(mal_soup)
mal_df = pd.DataFrame(mal_dict)

print(".", end="", flush=True)


end_of_animelist = False
while not end_of_animelist:
    counter += 1
    mal_soup = maldata.loadtopanime(counter)
    if mal_soup is not None:
        mal_dict = maldata.createdict_top(mal_soup)
        mal_df = pd.concat([mal_df, pd.DataFrame(mal_dict)])
        print(".", end="", flush=True)
    else:
        end_of_animelist = True
        print("done.")


mal_df.to_pickle('mal_full_list.pkl')