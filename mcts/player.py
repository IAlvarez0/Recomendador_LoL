import random
from mcts.node import Node
import logging
import numpy
import pickle
import pandas as pd
from champion.champs_utils import find_roles

# Modificacion del codigo de DraftArtist. Se hacen las siguientes modificaciones:
#   Se mejora el backpropagation que hace que el arbol vaya mucho mas rapido
#
#   Se modifica el Monte Carlo para que pueda usar redes neuronales con distintas
#   configuraciones. Para ello ademas de la red neuronal se indica: la configuracion
#   y la transformacion realizada al escalar. La evaluacion del Monte Carlo se cambia
#   para que haga las transformaciones necesarias de una lista de ids a la
#   representacion adecuada.

logger = logging.getLogger('mcts')
champs = sorted(list(pd.read_json("../data/champion/champion.json")["data"].apply(lambda champ: int(champ['key']))))
df_stats = pd.read_json("../data/champion/champs_stats.json")
COLUMNS = df_stats.columns
COLUMNS_GLOBAL_BLUE = [item + '_blue' for item in list(COLUMNS)[2:]]
COLUMNS_GLOBAL_RED = [item + '_red' for item in list(COLUMNS)[2:]]

CONST_ROLES = ['TOP', 'MIDDLE', 'JUNGLE', 'DUO_CARRY', 'DUO_SUPPORT']
COLUMNS_ROLES = []
for role in CONST_ROLES:
    if len(COLUMNS_ROLES) == 0:
        COLUMNS_ROLES = [item + '_blue_' + role for item in list(COLUMNS)[2:]]
        COLUMNS_ROLES += [item + '_red_' + role for item in list(COLUMNS)[2:]]
    else:
        COLUMNS_ROLES += [item + '_blue_' + role for item in list(COLUMNS)[2:]]
        COLUMNS_ROLES += [item + '_red_' + role for item in list(COLUMNS)[2:]]


class Player:

    def get_first_move(self):
        with open('../data/stats/lol_hero_freqs.pickle', 'rb') as f:
            a, p = pickle.load(f)
            return numpy.random.choice(a, size=1, p=p)[0]

    def get_move(self):
        raise NotImplementedError


class RandomPlayer(Player):

    def __init__(self, draft):
        self.draft = draft
        self.name = 'random'

    def get_move(self):
        """
        decide the next move
        """
        if self.draft.if_first_move():
            return self.get_first_move()
        moves = self.draft.get_moves()
        return random.sample(moves, 1)[0]


class HighestWinRatePlayer(Player):

    def __init__(self, draft):
        self.draft = draft
        self.name = 'hwr'
        with open('../data/stats/lol_win_rate_dict.pickle', 'rb') as f:
            self.win_rate_dict = pickle.load(f)

    def get_move(self):
        """
        decide the next move
        """
        if self.draft.if_first_move():
            return self.get_first_move()
        moves = self.draft.get_moves()
        move_win_rates = [(m, self.win_rate_dict[m]) for m in moves]
        best_move, best_win_rate = sorted(move_win_rates, key=lambda x: x[1])[-1]
        return best_move


class MCTSPlayer(Player):

    def __init__(self, name, draft, maxiters, c, model_path):
        self.draft = draft
        self.name = name + " " + model_path
        self.maxiters = maxiters
        self.c = c
        with open('{}'.format(model_path), 'rb') as f:
            model = pickle.load(f)
        if type(model) == list:
            self.model = model[0]
            self.conf = model[1]
            self.scaler = model[2]
        else:
            self.model = model
            self.conf = state_to_df_vector
            self.scaler = None

    def get_move(self):
        """
        decide the next move
        """
        if self.draft.if_first_move():
            return self.get_first_move()

        root = Node(player=self.draft.player, untried_actions=self.draft.get_moves(), c=self.c)

        for i in range(self.maxiters):
            node = root
            tmp_draft = self.draft.copy()

            # selection - select best child if parent fully expanded and not terminal
            while len(node.untried_actions) == 0 and node.children != []:
                node = node.select()
                tmp_draft.move(node.action)

            # expansion - expand parent to a random untried action
            if len(node.untried_actions) != 0:
                a = random.sample(node.untried_actions, 1)[0]
                tmp_draft.move(a)
                p = tmp_draft.player
                node = node.expand(a, p, tmp_draft.get_moves())

            # simulation - rollout to terminal state from current
            # state using random actions
            while not tmp_draft.end():
                moves = tmp_draft.get_moves()
                a = random.sample(moves, 1)[0]
                tmp_draft.move(a)

            # backpropagation - propagate result of rollout game up the tree
            # reverse the result if player at the node lost the rollout game
            aux_result = self.eval(tmp_draft.state)
            while node is not None:
                if node.player == 0:
                    result = aux_result
                else:
                    result = 1 - aux_result
                node.update(result)
                node = node.parent

        return root.select_final()

    def eval(self, state):
        """
        Evalua la composicion, transformandola a la representacion
        adecuada y escalando si es necesario
        """
        if self.scaler is not None:
            df = self.scaler.transform(self.conf(state))
        else:
            df = self.conf(state)
        blue_team_win_rate = self.model.predict_proba(df)[0, 1]
        return blue_team_win_rate


def state_to_df_vector(state):
    """
    Transforma una composicion a la representacion vector
    """
    df = pd.DataFrame([[0] * len(champs)], columns=champs)
    for i in champs:
        if i in state[0]:
            df[i] = 1
        elif i in state[1]:
            df[i] = -1
        else:
            df[i] = 0
    return df


def state_to_df_global(state):
    """
    Transforma una composicion a la representacion global
    """
    columns = COLUMNS_GLOBAL_BLUE + COLUMNS_GLOBAL_RED
    df = pd.DataFrame([[0] * len(columns)], columns=columns)
    for i in state[0]:
        stats = list(df_stats.loc[df_stats["key"] == i].iloc[0, 2:])
        df[COLUMNS_GLOBAL_BLUE] = df[COLUMNS_GLOBAL_BLUE] + stats
    for i in state[1]:
        stats = list(df_stats.loc[df_stats["key"] == i].iloc[0, 2:])
        df[COLUMNS_GLOBAL_RED] = df[COLUMNS_GLOBAL_RED] + stats
    return df


def state_to_df_roles(state):
    """
    Transforma una composicion a la representacion de roles
    """
    df = pd.DataFrame([[0] * len(COLUMNS_ROLES)], columns=COLUMNS_ROLES)
    roles_blue = find_roles(state[0])
    roles_red = find_roles(state[1])

    for i in range(5):
        # Equipo azul
        stats = list(df_stats.loc[df_stats["key"] == state[0][i]].iloc[0, 2:])
        cols = [item + '_blue_' + roles_blue[i] for item in list(COLUMNS)[2:]]
        df[cols] = stats

        # Equipo rojo
        stats = list(df_stats.loc[df_stats["key"] == state[1][i]].iloc[0, 2:])
        cols = [item + '_red_' + roles_red[i] for item in list(COLUMNS)[2:]]
        df[cols] = stats
    return df
