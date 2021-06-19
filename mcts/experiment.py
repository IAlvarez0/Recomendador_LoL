import random
import warnings

import numpy as np
import time
import logging
from captain_mode_draft import Draft


# Modificacion del codigo de DraftArtist. Se realizan los cambios:
# Se modifica la evaluacion, pues ahora se recoge un vector de porcentajes de victoria
# El codigo permite tanto optimizar el parametro c como enfrentar dos modelos


def experiment(match_id, p0_model_str, p1_model_str, p0_path, p1_path):
    """
    Ejecucion de un draft entre dos modelos.
    Se obtienen los porcentajes de victoria
    """
    t1 = time.time()
    d = Draft(p0_path, p1_path, p0_model_str, p1_model_str)

    while not d.end():
        p = d.get_player()
        t2 = time.time()
        a = p.get_move()
        d.move(a)
        d.print_move(match_id=match_id, move_duration=time.time() - t2, move_id=a)

    final_blue_team_win_rates = d.eval()[0]
    duration = time.time() - t1
    exp_str = 'match: {}, time: {:.3F}, compositions: {}, p0 predicted win rates: {}' \
        .format(match_id, duration, d.state, final_blue_team_win_rates)
    logger.warning(exp_str)

    return final_blue_team_win_rates, duration


if __name__ == '__main__':
    random.seed(123)
    np.random.seed(123)

    logger = logging.getLogger('mcts')
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.WARNING)

    c = [2 ** -5, 2 ** -4, 2 ** -3, 2 ** -2, 2 ** -1, 3 * 2 ** -1]

    path = '../NNs/NN_vector.pkl'
    num_matches = 30

    # Strings posibles: random, hwr, mcts_maxiter_c
    model1 = 'mcts_300_1'
    model1_path = path

    models = ['mcts_300_' + str(j) for j in c]
    model2_path = path

    for model2 in range(len(models)):
        m1_wr_5, m1_wr_4, m1_wr_3, m1_wr_2, times = [], [], [], [], []
        for i in range(num_matches):
            if i < num_matches // 2:
                wrs, t = experiment(i, model1, models[model2], model1_path, model2_path)
                if wrs[0] is not None:
                    m1_wr_5.append(wrs[0])
                if wrs[1] is not None:
                    m1_wr_4.append(wrs[1])
                if wrs[2] is not None:
                    m1_wr_3.append(wrs[2])
                if wrs[3] is not None:
                    m1_wr_2.append(wrs[3])
            else:
                wrs, t = experiment(i, models[model2], model1, model2_path, model1_path)
                if wrs[0] is not None:
                    m1_wr_5.append(1 - wrs[0])
                if wrs[1] is not None:
                    m1_wr_4.append(1 - wrs[1])
                if wrs[2] is not None:
                    m1_wr_3.append(1 - wrs[2])
                if wrs[3] is not None:
                    m1_wr_2.append(1 - wrs[3])
            times.append(t)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                s = '{} mean predicted win rate: {:.5f} {:.5f} {:.5f} {:.5f}\n' \
                    .format(model1, np.average(m1_wr_5), np.average(m1_wr_4), np.average(m1_wr_3), np.average(m1_wr_2))
            logger.warning(s)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            texto = '{} matches, model {} vs. model {}. average time {:.5f}, average of first model win rate {:.5f} {:.5f} {:.5f} {:.5f}, std {:.5f} {:.5f} {:.5f} {:.5f}' \
                .format(num_matches, model1, models[model2], np.average(times), np.average(m1_wr_5),
                        np.average(m1_wr_4), np.average(m1_wr_3), np.average(m1_wr_2),
                        np.std(m1_wr_5), np.std(m1_wr_4), np.std(m1_wr_3), np.std(m1_wr_2))
        logger.warning(texto)
