"""
Generate hero selection distribution, which will be used for sampling the first hero
"""
import pickle
from collections import defaultdict
import numpy
import pprint
import pandas as pd

data_path = "../data/games_roles.pkl"
output_path = '../data/stats/lol_hero_freqs.pickle'
select_dist = defaultdict(int)

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

    for i in range(len(blueChamps)):
        for c in blueChamps[i]:
            select_dist[c] += 1
        for c in redChamps[i]:
            select_dist[c] += 1

    pprint.pprint(select_dist)

    with open(output_path, 'wb') as f:
        a = keys
        p = defaultdict(float)
        N = len(blueChamps) * 10.0
        for i in a:
            p[i] = select_dist[i] / N
        print('a', a)
        print('p', p.values())
        print(p)
        print(numpy.sum(list(p.values())))
        pickle.dump((a, list(p.values())), f)

    with open(output_path, 'rb') as f:
        a, p = pickle.load(f)
        print(numpy.random.choice(a, size=1, p=p)[0])
