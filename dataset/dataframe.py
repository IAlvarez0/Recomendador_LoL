import pandas as pd


def get_champ_ids(champs):
    """
    Funcion auxiliar para obtener los ids de los campeones
    """
    return [champ["championId"] for champ in champs]


def get_role(p):
    """
    Funcion auxiliar para obtiene el rol de un jugador
    """
    if p['role'] == 'DUO_SUPPORT':
        return p['role']
    # Si el jugador solo en bot, podemos suponer que es adc
    elif p['role'] == 'SOLO' and p['lane'] == 'BOTTOM':
        return 'DUO_CARRY'
    elif p['lane'] in ['JUNGLE', 'TOP', 'MIDDLE']:
        return p['lane']
    # Puede aparecer DUO_CARRY y MIDDLE juntos erróneamente
    # Primero comprobamos si es middle, luego si es carry
    elif p['role'] == 'DUO_CARRY':
        return p['role']
    else:
        return p['lane']


def df_extract_data(df):
    """
    De un dataframe con todos los datos de la partida,
    se obtienen: la victoria, los campeones, los vetos y los roles
    """
    game_id = df['gameId']
    platform_id = df['platformId']
    # La victoria o derrota del equipo Azul: 1 victoria, 0 derrota
    blue_win = pd.get_dummies(df.iloc[:, 10].apply(lambda teams: teams[0]["win"])).iloc[:, 1]

    # Campeone seleccionados
    blue_champs = df.iloc[:, 11].apply(lambda champs: champs[0:5]).apply(get_champ_ids)
    red_champs = df.iloc[:, 11].apply(lambda champs: champs[5:10]).apply(get_champ_ids)
    # Vetos
    blue_bans = df['teams'].apply(lambda team: team[0]['bans']).apply(lambda bans: [ban['championId'] for ban in bans])
    red_bans = df['teams'].apply(lambda team: team[1]['bans']).apply(lambda bans: [ban['championId'] for ban in bans])
    # Roles
    blue_roles = df['participants'].apply(lambda participants: [get_role(p['timeline']) for p in participants[0:5]])
    red_roles = df['participants'].apply(lambda participants: [get_role(p['timeline']) for p in participants[5:10]])

    df = pd.DataFrame()
    df['gameId'] = game_id
    df['platformId'] = platform_id
    df["blueChamps"] = blue_champs
    df["redChamps"] = red_champs
    df["blueBans"] = blue_bans
    df["redBands"] = red_bans
    df["blueRoles"] = blue_roles
    df["redRoles"] = red_roles
    df["blueWin"] = blue_win
    return df


def convert_champs(row):
    """
    Función auxiliar para codificar un campeon dependiendo de su equipo
    """
    for champ in row['blueChamps']:
        row[champ] = 1

    for champ in row['redChamps']:
        row[champ] = -1
    return row


def df_to_vector_1s(df):
    """
    Convierte un dataframe con los datos del draft
    en uno con la representacion de vector
    """
    df_champs = pd.read_json("../data/champion/champion.json")
    keys = sorted(list(df_champs["data"].apply(lambda champ: int(champ['key']))))
    df_aux = df[["blueChamps", "redChamps"]].copy()
    # Vector de 1 y -1 para los campeones
    df_aux[keys] = pd.DataFrame([[0] * len(keys)], index=df_aux.index)
    df_aux = df_aux.apply(convert_champs, axis=1)
    df_aux.drop(columns=['blueChamps', 'redChamps'], inplace=True)
    if 'blueWin' in df:
        df_aux["blueWin"] = df['blueWin']
    return df_aux


def df_to_champs_ids(df):
    """
    Convierte un dataframe con los datos del draft
    en uno con los ids de los campeones ordenados y la victoria
    """
    if 'blueWin' in df:
        df_aux = df[["blueChamps", "redChamps", "blueWin"]].copy()
    else:
        df_aux = df[["blueChamps", "redChamps"]].copy()
    df_aux['blueChamps'] = df_aux['blueChamps'].apply(lambda blue_champs: sorted(blue_champs))
    df_aux['redChamps'] = df_aux['redChamps'].apply(lambda red_champs: sorted(red_champs))
    return df_aux


def convert_to_global_stats(row, df_champs):
    """
    Funcion auxiliar para obtener las estadisticas por equipo
    """
    columns = [item + '_blue' for item in list(df_champs.columns)[2:]]
    for champ in row['blueChamps']:
        stats = list(df_champs.loc[df_champs["key"] == champ].iloc[0, 2:])
        row[columns] = row[columns] + stats

    columns = [item + '_red' for item in list(df_champs.columns)[2:]]
    for champ in row['redChamps']:
        stats = list(df_champs.loc[df_champs["key"] == champ].iloc[0, 2:])
        row[columns] = row[columns] + stats

    return row


def df_to_global_stats(df):
    """
    Convierte un dataframe con los datos del draft
    en uno con la representacion de estadisticas globales
    """
    df_aux = df[["blueChamps", "redChamps"]].copy()
    df_champs = pd.read_json("../data/champion/champs_stats.json")
    columns = [item + '_blue' for item in list(df_champs.columns)[2:]]
    columns += [item + '_red' for item in list(df_champs.columns)[2:]]
    df_aux[columns] = pd.DataFrame([[0] * len(columns)], index=df_aux.index)
    df_aux = df_aux.apply(lambda row: convert_to_global_stats(row, df_champs), axis=1)
    df_aux.drop(columns=["blueChamps", "redChamps"], inplace=True)
    if 'blueWin' in df:
        df_aux["blueWin"] = df['blueWin']
    return df_aux


def convert_to_stats_by_roles(row):
    """
        Funcion auxiliar para obtener las estadisticas por rol
    """
    df_champs = pd.read_json("../data/champion/champs_stats.json")
    champs = row['blueChamps']
    roles = row['blueRoles']
    for i in range(5):
        stats = list(df_champs.loc[df_champs["key"] == champs[i]].iloc[0, 2:])
        columns = [item + '_blue_' + roles[i] for item in list(df_champs.columns)[2:]]
        row[columns] = stats

    champs = row['redChamps']
    roles = row['redRoles']
    for i in range(5):
        stats = list(df_champs.loc[df_champs["key"] == champs[i]].iloc[0, 2:])
        columns = [item + '_red_' + roles[i] for item in list(df_champs.columns)[2:]]
        row[columns] = stats
    return row


def df_to_individual_stats_by_roles(df):
    """
        Convierte un dataframe con los datos del draft
        en uno con la representacion de estadisticas individuales por rol
    """
    df_aux = df[["blueChamps", "redChamps", "blueRoles", "redRoles"]].copy()

    const_roles = ['TOP', 'MIDDLE', 'JUNGLE', 'DUO_CARRY', 'DUO_SUPPORT']
    blue_roles_bad = df_aux['blueRoles'].apply(lambda rol: set([rol.count(i) for i in const_roles]) != {1})
    red_roles_bad = df_aux['redRoles'].apply(lambda rol: set([rol.count(i) for i in const_roles]) != {1})
    index_names = df_aux[blue_roles_bad | red_roles_bad].index
    df_aux.drop(index_names, inplace=True)

    df_champs = pd.read_json("../data/champion/champs_stats.json")
    for role in const_roles:
        columns = [item + '_blue_' + role for item in list(df_champs.columns)[2:]]
        df_aux[columns] = pd.DataFrame([[0] * len(columns)], index=df_aux.index)
        columns = [item + '_red_' + role for item in list(df_champs.columns)[2:]]
        df_aux[columns] = pd.DataFrame([[0] * len(columns)], index=df_aux.index)

    df_aux = df_aux.apply(lambda row: convert_to_stats_by_roles(row), axis=1)
    df_aux.drop(columns=["blueChamps", "redChamps", "blueRoles", "redRoles"], inplace=True)
    if 'blueWin' in df:
        df_aux["blueWin"] = df['blueWin']
    return df_aux


def count_diff_games(df):
    """
    Cuenta las veces que dos composiciones son iguales en un dataframe del draft
    que no ha sido transformado a otra representacion
    """
    df = df_to_champs_ids(df)
    df['champion'] = df['blueChamps'].apply(lambda champs: champs.copy())
    df.apply(lambda row: row['champion'].extend(row['redChamps']), axis=1)
    df['champion'] = df['champion'].apply(lambda champs: str(sorted(champs)))
    print(list(df.groupby("champion").size()).count(2))
    df['blueChamps'] = df['blueChamps'].apply(lambda champs: str(champs))
    df['redChamps'] = df['redChamps'].apply(lambda champs: str(champs))
    print(list(df.groupby(["blueChamps", "redChamps"]).size()).count(2))
