import pickle

import pandas as pd


def convert_tags_and_partype(row):
    for tag in row['tags']:
        row[tag] = 1
    row[row['partype']] = 1
    return row


def create_df_champs_stats(source="../data/champion.json", filename="../data/champion/champs_stats.json"):
    """
    A partir del fichero con todos los datos de los campeones,
    genera un dataframe con las estadisticas de los campeones.
    Las etiquetas y el recurso son codificados con one-hot
    """
    df_champs = pd.read_json(source)
    df_champs.drop(columns=["type", "format", "version"], inplace=True)
    data = df_champs["data"].to_list()
    df = pd.DataFrame(data)
    df.drop(columns=["version", "name", "title", "blurb", "image"], inplace=True)
    info = pd.json_normalize((df['info']))
    stats = pd.json_normalize(df['stats'])
    df.drop(columns=["info", "stats"], inplace=True)

    tags = ['Assassin', 'Fighter', 'Marksman', 'Mage', 'Support', 'Tank']
    partypes = ['Fury', 'Ferocity', 'Heat', 'Blood Well', 'Courage', 'Grit', 'Flow', 'Shield', 'Crimson Rush', 'Rage',
                'Energy', 'None', 'Mana']
    df[tags + partypes] = pd.DataFrame([[0] * len(tags + partypes)], index=df.index)
    df = df.apply(lambda row: convert_tags_and_partype(row), axis=1)
    df.drop(columns=["tags", "partype"], inplace=True)
    df = df.join(info)
    df = df.join(stats)
    df.to_json(filename)


def create_freq_roles(source="../data/games_roles.pkl", filename='../data/stats/dict_freq_roles.pkl'):
    """
    Crea un fichero con la frecuencia con la que cada campeon ha estado en un rol
    """
    df = pd.read_pickle(source)[["blueChamps", "redChamps", "blueRoles", "redRoles"]]
    # Diccionario como clave un campeon y como valor un diccionario con los porcentajes de cada rol
    d = {}
    # Se obtienen las partidas de en cada rol
    for index, row in df.iterrows():
        b_champs = row['blueChamps']
        b_roles = row['blueRoles']
        r_champs = row['redChamps']
        r_roles = row['redRoles']
        for i in range(5):
            # Campeones del equipo Azul
            # Si el campeon no esta en el dicc, lo añadimos y inicializamos
            # el diccionario de la frecuencia de roles
            if b_champs[i] not in d:
                d[b_champs[i]] = {}

            aux = d[b_champs[i]]
            if b_roles[i] in aux:
                aux[b_roles[i]] += 1
            else:
                aux[b_roles[i]] = 1
            d[b_champs[i]] = aux

            # Campeones del equipo Rojo
            if r_champs[i] not in d:
                d[r_champs[i]] = {}

            aux = d[r_champs[i]]
            if r_roles[i] in aux:
                aux[r_roles[i]] += 1
            else:
                aux[r_roles[i]] = 1
            d[r_champs[i]] = aux

    # Se halla el porcentaje de cada rol
    for i in d:
        partidas = sum(d[i].values())
        for j in d[i]:
            d[i][j] = d[i][j] / partidas

    # Guardamos el diccionario
    with open(filename, 'wb') as f:
        pickle.dump(d, f)


def find_roles(comp, dict_roles_file="../data/stats/dict_freq_roles.pkl"):
    """
    Devuelve los roles de una lista de campeones.
    Recibe la lista, y el path al diccionario de frecuencia de roles
    """
    with open(dict_roles_file, 'rb') as f:
        dict_roles = pickle.load(f)
    roles = ['TOP', 'MIDDLE', 'JUNGLE', 'DUO_CARRY', 'DUO_SUPPORT']
    champs = comp.copy()
    p_roles = []
    asignaciones = []
    # Obtenemos para cada campeon, su probabilidad de estar en un rol
    for i in champs:
        p_roles.append([i, dict_roles[i]])

    while len(champs) > 0:
        p_max = 0
        for c, d in p_roles:
            # Si queda por asignar
            if c in champs:
                for rol in roles:
                    if rol in d and d[rol] > p_max:
                        p_max = d[rol]
                        rol_max = rol
                        champ = c
        # Si no se ha encontrado nuevo campeon que asignar, se asignan los restantes
        if champ not in champs:
            for i in range(len(champs)):
                asignaciones.append([champs[i], roles[i]])
            break
        # Asignamos el rol al campeon
        asignaciones.append([champ, rol_max])
        # Quitamos el campeon y el rol, pues ya estan asignados
        champs.remove(champ)
        roles.remove(rol_max)

    # Se crea la lista de roles final
    roles = []
    for c in comp:
        for a in asignaciones:
            if c == a[0]:
                roles.append(a[1])

    return roles
