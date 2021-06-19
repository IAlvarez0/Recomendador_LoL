import pandas as pd


def set_check(row, s):
    """
    Funcion auxiliar que modifica una fila para que quitar los campeones de
    cada equipo que no coincidan con la composicion pasada, s.
    Halla coincidencias de la composicion con las partidas del dataset
    """
    set_blue = set(row['blueChamps'])
    set_red = set(row['redChamps'])
    s0 = set(s[0])
    s1 = set(s[1])
    lenb0 = len(set_blue & s0)
    lenr1 = len(set_red & s1)
    lenb1 = len(set_blue & s1)
    lenr0 = len(set_red & s0)
    # Ambos equipos tienen que tener coincidencias
    if not ((lenb0 != 0 and lenr1 != 0) or (lenb1 != 0 and lenr0 != 0)):
        row['blueChamps'] = None
        row['redChamps'] = None
    # Si hay coincidencias, elegimos la mejor opcion para hacer intereccion con
    # la composicion de cada equipo
    elif (lenb0 >= lenb1 and lenr1 >= lenb1) or (lenb0 >= lenr0 and lenr1 >= lenr0):
        row['blueChamps'] = set_blue & s0
        row['redChamps'] = set_red & s1
    else:
        row['blueChamps'] = set_blue & s1
        row['redChamps'] = set_red & s0
    return row


def get_wrs(state, maximo=10):
    """
    Funcion que obtiene los porcentajes de victoria asociados a una composicion.
    Evalua sus coincidencias con la base de datos. Para ello obtiene
    coincidencias de 4 campeones (2 por equipo), 6 campeones, 8 campeones
    y toda la composicion. Explicacion detallada en el TFG
    """
    df = pd.read_pickle("games_roles_eval.pkl")
    state = [sorted(i) for i in state]
    # Obtenemos los campeones que coinciden con la composicion
    df_set = df.apply(lambda row: set_check(row, state), axis=1)
    df_set.dropna(inplace=True)

    wr_list = []
    wins_list = []
    loses_list = []

    # Probamos distintos numeros de campeones iguales
    for i in range(maximo, 2, -2):
        true10 = df_set.apply(lambda row: len(row['blueChamps']) >= i / 2 and len(row['redChamps']) >= i / 2, axis=1)
        indexes = true10[true10 == True].index
        df_filtered = df_set.loc[indexes]
        # Hallamos los resultados de las partidas
        results = df_filtered.apply(
            lambda row: row['blueWin'] if any(map(lambda v: v in row['blueChamps'], state[0])) else (
                0 if row['blueWin'] == 1 else 1), axis=1)
        wins = list(results).count(1)
        wins_list.append(wins)
        loses = list(results).count(0)
        loses_list.append(loses)
        if wins != 0 or loses != 0:
            wr = wins / (wins + loses)
        else:
            wr = None
        wr_list.append(wr)
        # if wr is None:
        #    print('{} equal min, {} wins, {} loses'.format(i, wins, loses))
        # else:
        #    print('{} equal min, {} wins, {} loses, {:.2f} win rate'.format(i, wins, loses, wr))

    return wr_list, wins_list, loses_list
