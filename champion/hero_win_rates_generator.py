"""
Generate hero win rate distribution, which will be used for a baseline strategy
"""
import pickle
from collections import defaultdict
import pprint
import pandas as pd

data_path = "../data/games_roles.pkl"
output_path = '../data/stats/lol_win_rate_dict.pickle'
select_dict = defaultdict(int)
win_rate_dict = defaultdict(int)

if __name__ == '__main__':
    df = pd.read_pickle(data_path)
    blueWin = df['blueWin']
    blueChamps = df['blueChamps']
    redChamps = df['redChamps']

    df_champs = pd.read_json("../data/champion/champion.json")
    keys = sorted(list(df_champs["data"].apply(lambda champ: int(champ['key']))))
    M = len(keys)

    print(len(blueChamps))  # numero de partidas
    print(M)  # numero de campeones

    for i in range(len(blueWin)):
        for c in blueChamps[i]:
            select_dict[c] += 1
            if blueWin[i]:
                win_rate_dict[c] += 1
        for c in redChamps[i]:
            select_dict[c] += 1
            if not blueWin[i]:
                win_rate_dict[c] += 1

    print('select dict:')
    pprint.pprint(select_dict)
    print('win rate dict:')
    pprint.pprint(win_rate_dict)

    with open(output_path, 'wb') as f:
        p = defaultdict(float)
        for i in keys:
            if select_dict[i] == 0:
                p[i] = 0
                continue
            p[i] = win_rate_dict[i] / select_dict[i]
        print('p', p)
        pickle.dump(p, f)
