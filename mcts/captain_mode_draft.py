from mcts.eval import get_wrs
from player import RandomPlayer, MCTSPlayer, HighestWinRatePlayer
import logging
import pandas as pd


# Modificacion del codigo de DraftArtist. Se hacen las siguientes modificaciones:
#   Se pueden enfrentar dos monte carlos entre si, cada uno con una red neuronal distinta
#   El estado inicial del arbol se puede indicar
#   La evaluacion del estado final se realiza de la forma indicada en el TFG
#   Los turnos se modifican para el LoL sin vetos


def parse_mcts_maxiter_c(player_str):
    assert player_str.startswith('mcts')
    _, maxiter, c = player_str.split('_')
    return int(maxiter), float(c)


class Draft:
    """
    class handling state of the draft
    """

    def __init__(self, p0_path=None, p1_path=None, p0_model_str=None, p1_model_str=None, estado_inicial=None):
        if p0_model_str and p1_model_str:
            self.state = [[], []]
            champs = sorted(
                list(pd.read_json("../data/champion/champion.json")["data"].apply(lambda champ: int(champ['key']))))
            self.avail_moves = set(champs)
            self.M = len(self.avail_moves)
            self.move_cnt = [0, 0]
            self.player = None  # current player's turn
            self.next_player = 0  # next player turn
            # player 0 will pick first and be blue team; player 1 will pick next and be red team
            self.player_models = [self.construct_player_model(p0_model_str, p0_path),
                                  self.construct_player_model(p1_model_str, p1_path)]
            if estado_inicial is not None:
                for i in estado_inicial[0]:
                    self.avail_moves.remove(i)
                for i in estado_inicial[1]:
                    self.avail_moves.remove(i)
                self.state = [estado_inicial[0][:], estado_inicial[1][:]]
                self.move_cnt = [len(estado_inicial[0]), len(estado_inicial[1])]
                self.next_player = self.decide_player()

    def get_state(self, player):
        return self.state[player]

    def get_player(self):
        return self.player_models[self.next_player]

    def construct_player_model(self, player_model_str, model_path):
        if player_model_str == 'random':
            return RandomPlayer(draft=self)
        elif player_model_str.startswith('mcts'):
            max_iters, c = parse_mcts_maxiter_c(player_model_str)
            return MCTSPlayer(name=player_model_str, draft=self, maxiters=max_iters, c=c, model_path=model_path)
        elif player_model_str == 'hwr':
            return HighestWinRatePlayer(draft=self)
        else:
            raise NotImplementedError

    def eval(self, maximo=10):
        return get_wrs(self.state, maximo)

    def copy(self):
        """
        make copy of the board
        """
        copy = Draft()
        copy.M = self.M
        copy.state = [self.state[0][:], self.state[1][:]]
        copy.avail_moves = set(self.avail_moves)
        copy.move_cnt = self.move_cnt[:]
        copy.player = self.player
        copy.next_player = self.next_player
        copy.player_models = self.player_models
        return copy

    def move(self, move):
        """
        take move of form [x,y] and play
        the move for the current player
        """
        self.player = self.next_player
        self.next_player = self.decide_next_player()
        self.state[self.player].append(move)
        self.avail_moves.remove(move)
        self.move_cnt[self.player] += 1

    def decide_next_player(self):
        """
        determine next player before a move is taken
        """
        move_cnt = self.move_cnt[0] + self.move_cnt[1]
        if move_cnt in [0, 1, 4, 5, 8]:
            return 1
        else:
            return 0

    def decide_player(self):
        """
        determine next player before a move is taken
        """
        move_cnt = self.move_cnt[0] + self.move_cnt[1] - 1
        if move_cnt in [0, 1, 4, 5, 8]:
            return 1
        else:
            return 0

    def if_first_move(self):
        """ whether the next move is the first move """
        if self.move_cnt[0] == 0 and self.move_cnt[1] == 0:
            return True
        return False

    def get_moves(self):
        """
        return remaining possible draft moves
        (i.e., where there are no 1's or -1's)
        """
        if self.end():
            return set([])
        return set(self.avail_moves)

    def end(self):
        """
        return True if all players finish drafting
        """
        if self.move_cnt[0] == 5 and self.move_cnt[1] == 5:
            return True
        return False

    def print_move(self, match_id, move_duration, move_id):
        move_str = 'match {} player {} ({:15s}), {:3d}, move_cnt: {}, duration: {:.3f}' \
            .format(match_id, self.player, self.player_models[self.player].name, move_id,
                    self.move_cnt[self.player], move_duration)
        logger = logging.getLogger('mcts')
        logger.warning(move_str)
        return move_str
