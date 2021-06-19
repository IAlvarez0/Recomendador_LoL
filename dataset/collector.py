import os
import pickle
from multiprocessing.context import Process
import pandas as pd
import json
from datetime import datetime, timedelta
import requests
from riotwatcher import LolWatcher

lol_watcher = LolWatcher('')  # Introducir la API key de Riot Games
regions = ["br1", "eun1", "euw1", "jp1", "kr", "la1", "la2", "na1", "oc1", "ru", "tr1"]
# Aqui se indica la fecha y la habilidad de los jugadores
inicio = datetime(year=2021, month=3, day=31, hour=5, minute=0, second=0)
fin = datetime(2021, 4, 14, 5, 0, 0)
# Si la habilidad de los jugadores es Diamante o menor
tier = "DIAMOND"
division = "I"
rank = tier + "/" + division + "/"
# Si la habilidad de los jugadores es mayor que Diamante: master, grandmaster, challenger
# rank = "master/"

# Variables para guardar el estado actual de la recoleccion.
# La recoleccion se puede parar y volver a ejecutar y continuara
estado = ["", 0]
my_region = ""

# Listas auxiliares con los ids de las cuentas y los juegos
account_ids = []
game_ids = []


def to_timestamp(date):
    return int(date.timestamp() * 1000)


def save_obj():
    """
    Funcion que guarda el estado actual de la ejecucion para poder
    retomar la obtencion de datos donde se dejo
    """
    global my_region, estado
    print(estado)
    print(my_region + '.pkl')
    with open(my_region + '.pkl', 'wb') as f:
        pickle.dump(estado, f, pickle.HIGHEST_PROTOCOL)


def load_obj():
    """
    Funcion que obtiene el estado actual de la ejecucion para poder
    retomar la obtencion de datos donde se dejo
    """
    global my_region
    with open(my_region + '.pkl', 'rb') as f:
        return pickle.load(f)


def crear_path(tipo_dato):
    global rank, my_region
    return "data/" + rank + tipo_dato + "/" + my_region + "_" + tipo_dato + ".json"


def get_account_ids():
    """
    Funcion que consigue los account ids
    """
    global account_ids, lol_watcher, rank, my_region

    summoner_ids = []
    # La paginacion solo es necesaria para Diamante para abajo
    page = 1
    while True:
        # Obtenemos los summoner ids
        players = lol_watcher.league.entries(region=my_region, queue="RANKED_SOLO_5x5", tier=tier, division=division,
                                             page=page)
        # players = lol_watcher.league.masters_by_queue(region=my_region, queue="RANKED_SOLO_5x5")['entries']
        if len(players) == 0:
            break
        for i in players:
            summoner_ids.append(i['summonerId'])
        page += 1

    # Transformamos los summoner ids a account ids
    for i in summoner_ids:
        while True:
            try:
                response = lol_watcher.summoner.by_id(my_region, i)
                account_ids.append(response['accountId'])
                break
            # Si no se encuentra, pasamos al siguiente id
            except requests.HTTPError as e:
                if e.response.status_code == 404:
                    break
                else:
                    print(e)
                    continue
            except Exception as e:
                print(e)
                continue

    df = pd.DataFrame(summoner_ids)
    df.columns = ['summoner_id']
    df['account_id'] = account_ids
    df.to_json("data/" + rank + "account_ids/" + my_region + "_account_ids.json", orient="records")
    print(my_region + " : get_account_ids completada: " + str(len(account_ids)))


def get_game_ids(posicion):
    """
    Funcion que obtiene los ids de las partidas.
    Se puede parar con una interrupcion y volver a correr y seguira en el ultimo.
    Para ello se emplea el parametro posicion y objeto pickle para guardar el estado
    """
    global account_ids, game_ids, lol_watcher, rank, my_region, estado
    path = "data/" + rank + "game_ids/" + my_region + "_game_ids.json"
    f = open(path, "a")
    contador = posicion
    for account in account_ids[posicion:]:
        game_ids_aux = []
        begin_time = inicio
        # El rango maximo de tiempo para la request es una semana
        end_time = inicio + timedelta(7)
        while end_time <= fin:
            while True:
                try:
                    # 420 son las partidas 5v5 Ranked Solo games
                    games = lol_watcher.match.matchlist_by_account(my_region, account, {'420'},
                                                                   begin_time=to_timestamp(begin_time),
                                                                   end_time=to_timestamp(end_time))['matches']
                    for i in games:
                        game_ids.append(i['gameId'])
                        game_ids_aux.append(i['gameId'])
                    break
                except requests.HTTPError as e:
                    # Si no hay partidos
                    if e.response.status_code == 404:
                        break
                    # Si el acceso esta prohibido, la clave a expirado
                    # Guardamos el estado y salimos
                    elif e.response.status_code == 403:
                        game_ids = list(set(game_ids))
                        for i in game_ids:
                            print(json.dumps(i), file=f)
                        f.close()

                        save_obj()
                        return 0
                    else:
                        print(e)
                        continue
                # Si llega una interrupcion, guardamos y salimos
                except KeyboardInterrupt:
                    game_ids = list(set(game_ids))
                    for i in game_ids:
                        print(json.dumps(i), file=f)
                    f.close()

                    save_obj()
                    return 0
                except Exception as e:
                    print(e)
                    continue
            begin_time = end_time
            if end_time + timedelta(7) > fin and end_time != fin:
                end_time = fin
            else:
                end_time = end_time + timedelta(7)
        contador += 1
        estado = ["game_ids", contador]

    game_ids = list(set(game_ids))
    for i in game_ids:
        print(json.dumps(i), file=f)
    f.close()
    # Quitamos duplicados
    game_ids = list(set(list(pd.read_json(path, lines=True)[0])))
    f = open(path, "w")
    for i in game_ids:
        print(json.dumps(i), file=f)
    f.close()
    # df = pd.DataFrame(game_ids)
    # df.columns = ['game_id']
    # df.to_json("data/" + rank + "game_ids/" + my_region + "_game_ids.json", orient="records")
    estado = ["game_data", 0]
    save_obj()
    print(my_region + " : get_game_ids completada: " + str(len(game_ids)))
    return 1


def get_game_data(posicion):
    """
    Funcion que obtiene los datos de las partidas.
    Se puede parar con una interrupcion y volver a correr y seguira en el ultimo.
    Para ello se emplea el parametro posicion y objeto pickle para guardar el estado
    """
    global game_ids, lol_watcher, rank, my_region, estado
    print(my_region + " : get_game_data iniciada")
    contador = posicion
    f = open("data/" + rank + "games/" + my_region + "_game_jsons.json", "a")
    for gId in game_ids[posicion:]:
        while True:
            try:
                game = lol_watcher.match.by_id(my_region, gId)
                print(json.dumps(game), file=f)
                contador += 1
                estado = ["game_data", contador]
                break
            except requests.HTTPError as e:
                if e.response.status_code == 404:  # Not found
                    break
                # Si el acceso esta prohibido, la clave ha caducado. Guardamos
                elif e.response.status_code == 403:
                    save_obj()
                    f.close()
                    return
                else:
                    print(e)
                    continue
            # Si llega una interrupcion, guardamos
            except KeyboardInterrupt:
                save_obj()
                f.close()
                return
            except Exception as e:
                print(e)
                continue
    f.close()
    estado = ["", 0]
    save_obj()
    print(my_region + " : get_game_data completada")


def get_data(region):
    """
    Funcion que realiza el proceso de obtencion de datos.
    Comprueba en que parte del proceso se esta para continuar en ese
    """
    global account_ids, game_ids, my_region, estado

    my_region = region
    path = crear_path("account_ids")
    # Si no existen los ids de los jugadores, se obtienen
    if not os.path.isfile(path):
        get_account_ids()
    else:
        account_ids = list(pd.read_json(path)["account_id"])

    path = crear_path("game_ids")
    # Si existe el objeto del estado del proceso
    if os.path.isfile(my_region + ".pkl"):
        estado_antiguo = load_obj()
        estado = estado_antiguo
        # Si se encuentra buscando ids de partidas
        if estado_antiguo[0] == "game_ids":
            if get_game_ids(estado_antiguo[1]):
                get_game_data(0)
            return
        # Si se encuentra obteneniendo los datos de partidas
        elif estado_antiguo[0] == "game_data":
            game_ids = list(pd.read_json(path, lines=True)[0])
            get_game_data(estado_antiguo[1])
            return

    # Si no existe el fichero de ids de partidas
    if not os.path.isfile(path):
        if get_game_ids(0):
            get_game_data(0)
            return
    # Si existe el fichero de ids de partidas, falta recoger los datos de las partidas
    elif not os.path.isfile("data/" + rank + "games/" + my_region + "_game_jsons.json"):
        game_ids = list(pd.read_json(path, lines=True)[0])
        get_game_data(0)
        return

    print(my_region + " : datos recogidos.")


if __name__ == '__main__':
    p = []
    for region in regions:
        p.append(Process(target=get_data, args=(region,)))
        p[-1].start()  # start now

    for j in p:
        j.join()
