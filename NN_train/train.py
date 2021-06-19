import pickle
import pandas as pd
from sklearn.model_selection import KFold, cross_val_score
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from mcts.player import state_to_df_vector, state_to_df_global, state_to_df_roles

if __name__ == '__main__':
    cv = KFold(n_splits=10, shuffle=True, random_state=1)

    # VECTOR
    conf = state_to_df_vector
    scaler = None
    df = pd.read_pickle("../data/df_vector.pkl")
    X = df.iloc[:, :-1]
    y = df.iloc[:, -1]
    # Aqui introducimos los hiperparametros optimos
    model = MLPClassifier()
    scores = cross_val_score(model, X, y, cv=cv)
    print(scores.mean())
    model.fit(X, y)
    # Guardamos el modelo, la configuracion de datos y la transformacion aplicada a los datos
    NN_lista = [model, conf, scaler]
    with open("../NNs/NN_vector.pkl", 'wb') as f:
        pickle.dump(NN_lista, f)

    # GLOBAL
    conf = state_to_df_global
    df = pd.read_pickle("../data/df_global.pkl")
    scaler = StandardScaler()
    df.iloc[:, :-1] = scaler.fit_transform(df.iloc[:, :-1])
    X = df.iloc[:, :-1]
    y = df.iloc[:, -1]
    # Aqui introducimos los hiperparametros optimos
    model = MLPClassifier()
    scores = cross_val_score(model, X, y, cv=cv)
    print(scores.mean())
    model.fit(X, y)
    # Guardamos el modelo, la configuracion de datos y la transformacion aplicada a los datos
    NN_lista = [model, conf, scaler]
    with open("../NNs/NN_global.pkl", 'wb') as f:
        pickle.dump(NN_lista, f)

    # ROLES
    conf = state_to_df_roles
    df = pd.read_pickle("../data/df_roles.pkl")
    scaler = StandardScaler()
    df.iloc[:, :-1] = scaler.fit_transform(df.iloc[:, :-1])
    X = df.iloc[:, :-1]
    y = df.iloc[:, -1]
    # Aqui introducimos los hiperparametros optimos
    model = MLPClassifier()
    scores = cross_val_score(model, X, y, cv=cv)
    print(scores.mean())
    model.fit(X, y)
    # Guardamos el modelo, la configuracion de datos y la transformacion aplicada a los datos
    NN_lista = [model, conf, scaler]
    with open("../NNs/NN_roles.pkl", 'wb') as f:
        pickle.dump(NN_lista, f)
