from sklearn.model_selection import KFold
import pandas as pd
from sklearn.model_selection import GridSearchCV
from sklearn.neural_network import MLPClassifier


def multilayer_percepton():
    """
    Funcion que devuelve el modelo MLP y el diccionario con parametros a probar
    """
    model = MLPClassifier(max_iter=1000)
    hidden_layer_sizes = [100, (100, 100), (100, 100, 100), (100, 100, 100, 100)]
    batch_size = [70, 100, 200]
    activation = ['logistic', 'relu']
    p_grid = dict(hidden_layer_sizes=hidden_layer_sizes, batch_size=batch_size, activation=activation)
    return p_grid, model


def cv_10(X, y, p_grid, estimator):
    """
    Funcion para optimizar los hiperparametros de un modelo
    mediante validacion cruzada de 10 iteraciones
    """
    inner_cv = KFold(n_splits=10, shuffle=True, random_state=0)
    clf = GridSearchCV(estimator=estimator, param_grid=p_grid, cv=inner_cv, verbose=3, n_jobs=-2, scoring='f1')
    print(clf.get_params())
    clf.fit(X, y)
    print("Best score: ", clf.best_score_)
    print("Best params: ", clf.best_params_)


if __name__ == '__main__':
    df = pd.read_pickle("../data/df_vector.pkl")
    # Escalar los datos si necesario
    # scaler = StandardScaler()
    # df.iloc[:,:-1] = scaler.fit_transform(df.iloc[:,:-1])

    X = df.iloc[:, :-1]
    y = df.iloc[:, -1]
    p_grid, model = multilayer_percepton()
    cv_10(X, y, p_grid, model)
