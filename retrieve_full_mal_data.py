import pandas as pd
import os

import maldata

counter = 1
start_reading = False

print("loading MAL list...", flush=True)
filename = 'data\\mal_full\\mal_full_list'
filename_part = filename + '_pt' + str(counter)

if not os.path.exists(filename_part + '.pkl'):

    start_reading = True
    print("Loading part", counter, flush=True)

    mal_soup = maldata.loadtopanime(counter)
    mal_dict = maldata.createdict_top(mal_soup)
    mal_df = pd.DataFrame(mal_dict)

    mal_df.to_pickle(filename_part + '.pkl')

end_of_animelist = False
while not end_of_animelist:
    counter += 1
    filename_part = filename + '_pt' + str(counter)
    if not os.path.exists(filename_part + '.pkl'):
        if not start_reading:
            start_reading = True
            print("Resuming loading part", counter, flush=True)

        mal_soup = maldata.loadtopanime(counter)

        if mal_soup is not None:
            print("Loading part", counter, flush=True)

            mal_dict = maldata.createdict_top(mal_soup)
            mal_df = pd.DataFrame(mal_dict)
            mal_df.to_pickle(filename_part + '.pkl')

        else:
            end_of_animelist = True
            print("Done.")

mal_df_list = []
for i in range(1, counter):
    filename_part = filename + '_pt' + str(i)
    mal_df_list.append(pd.read_pickle(filename_part + '.pkl'))

mal_df = pd.DataFrame(mal_df_list)
mal_df.to_pickle(filename + '.pkl')