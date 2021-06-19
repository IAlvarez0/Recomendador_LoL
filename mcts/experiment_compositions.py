import pickle
import warnings
from mcts.eval import get_wrs
import random
import numpy as np
import time
import logging
from captain_mode_draft import Draft


# Modificacion del codigo de DraftArtist. Los cambios del experimento usual:
# Se evaluan distintas composiciones como estado inicial de MCTS
# Se evaluan estados intermedios de MCTS
# Se muestran los porcentajes de victoria, el numero de victorias y derrotas


def experiment(match_id, p0_model_str, p1_model_str, p0_path, p1_path, composition=None):
    """
        Ejecucion de un draft entre dos modelos.
        Se evaluan los estados intermedios y se obtienen los porcentajes
        victoria, numero de partidas ganadas y perdidas
    """
    t1 = time.time()
    d = Draft(p0_path, p1_path, p0_model_str, p1_model_str, composition)  # instantiate board
    eval_intermedias = []
    while not d.end():
        p = d.get_player()
        t2 = time.time()
        a = p.get_move()
        d.move(a)
        d.print_move(match_id=match_id, move_duration=time.time() - t2, move_id=a)
        if sum(d.move_cnt) % 2 == 0 and sum(d.move_cnt) >= 4 and not d.end():
            eval_intermedias.append(list(d.eval(maximo=sum(d.move_cnt))[1:]))  # //2 * 2)

    final_blue_team_win_rates, wins_list, loses_list = d.eval()
    eval_intermedias.append([wins_list, loses_list])
    duration = time.time() - t1
    exp_str = 'match: {}, time: {:.3F}, p0 predicted win rates: {}, wins: {}, loses: {}, eval inter {}, composition: {}' \
        .format(match_id, duration, final_blue_team_win_rates, wins_list, loses_list, eval_intermedias, d.state)
    logger.warning(exp_str)

    return final_blue_team_win_rates, duration, d.state, wins_list, loses_list, eval_intermedias


if __name__ == '__main__':
    random.seed(123)
    np.random.seed(123)

    logger = logging.getLogger('mcts')
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.WARNING)

    path = '../NNs/NN_vector.pkl'
    num_matches = 5

    model1 = 'mcts_200_0.25'
    model1_path = path

    model2 = model1
    model2_path = path

    f = open("mcts_globalvsglobal.txt", "w")
    with open("../data/champion/compositions.pkl", 'rb') as f:
        compositions_by_n_champs = pickle.load(f)

    for c in range(len(compositions_by_n_champs)):
        compositions = compositions_by_n_champs[c]
        for composition in compositions:
            logger.warning("{}, eval {}".format(composition, get_wrs(composition)))
            m1_wr_5, m1_wr_4, m1_wr_3, m1_wr_2, times, final_comps = [], [], [], [], [], []
            final_wins_list, final_loses_list = [0, 0, 0, 0], [0, 0, 0, 0]
            for i in range(num_matches):
                wrs, t, comp, wins_list, loses_list, eval_aux = experiment(i, model1, model2, model1_path, model2_path,
                                                                           composition)
                if wrs[0] is not None:
                    m1_wr_5.append(wrs[0])
                if wrs[1] is not None:
                    m1_wr_4.append(wrs[1])
                if wrs[2] is not None:
                    m1_wr_3.append(wrs[2])
                if wrs[3] is not None:
                    m1_wr_2.append(wrs[3])
                times.append(t)
                if i == 0:
                    final_eval_aux = eval_aux
                else:
                    final_eval_aux = [np.add(final_eval_aux[i], eval_aux[i]).tolist() for i in
                                      range(len(final_eval_aux))]
                final_comps.append(comp)
                final_wins_list = np.add(final_wins_list, wins_list)
                final_loses_list = np.add(final_loses_list, loses_list)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    s = '{} mean predicted win rate: {:.5f} {:.5f} {:.5f} {:.5f}, wins {}, loses {}\n' \
                        .format(model1, np.average(m1_wr_5), np.average(m1_wr_4), np.average(m1_wr_3),
                                np.average(m1_wr_2), final_wins_list, final_loses_list)
                logger.warning(s)

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                texto = '{} matches, model {} vs. model {}. average time {:.5f}, average win rate {:.5f} {:.5f} {' \
                        ':.5f} {:.5f}, wins {}, loses {}'.format(num_matches, model1, model2, np.average(times),
                                                                 np.average(m1_wr_5), np.average(m1_wr_4),
                                                                 np.average(m1_wr_3), np.average(m1_wr_2),
                                                                 final_wins_list, final_loses_list)
            logger.warning(texto)
            texto = 'composicion inicial {}, composiciones finales {}'.format(composition, final_comps)
            logger.warning(texto)
            texto = 'eval intermedias {}\n'.format(final_eval_aux)
            logger.warning(texto)
    f.close()
