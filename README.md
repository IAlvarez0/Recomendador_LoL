# Recomendador de campeones en el LoL
Código desarrollado por Iris Álvarez para el TFG: *Sistema de recomendación de campeones del League of Legends: estudio de representaciones de datos y nuevos métodos de evaluación de árboles de Monte Carlo*.

Agradecimientos a Chen et al. por su desarrollo de [DraftArtist](https://github.com/czxttkl/DraftArtist). Su código se emplea como base para desarrollar MCTS UCT.

## Organización de archivos

Las carpetas se organizan de la siguiente forma:
|Carpeta | Contenido
--- | --- 
|data|Bases de datos y ficheros de datos auxiliares|
|NNs|Las redes neuronales entrenadas|
|dataset|Código para la obtención de partidas y su transformación en representaciones|
|champion|Funciones para generar ficheros auxiliares con datos de los campeones|
|NN_train|Código para la optimización de hiperparámatros y entrenamiento de redes neuronales|
|mcts|Implementación del árbol de búsqueda de Monte Carlo, su entrenamiento y pruebas|

El contenido de cada carpeta se explica a continuación.

### data
* `games.zip` cuenta con dos bases de datos. `games.pkl` cuenta con todas las partidas encontradas y `games_roles.pkl` con las partidas que tienen bien los roles.
* `dfs.zip` contiene la base de datos representada como cada una de las configuraciones de datos.
* La carpeta `champion` contiene información de los campeones y el fichero `compositions.pkl`, con las composiciones usadas en una de las pruebas.
* La carpeta `stats` contiene tres ficheros con: la frecuencia con la que se selecciona un campeón, el porcentaje de victoria de cada campeón y las frecuencias con las que un campeón juega en cada rol.

### NNs
Cuenta con tres redes neuronales, una por representación de datos. Los ficheros son: `NN_vector.py`, `NN_global.pkl` y `NN_roles.pkl`.

### dataset
* `collector.py` obtiene partidas usando la API de Riot Games.
* `dataframe.py` contiene las funciones necesarias para transformar las partidas obtenidas.

### champion
* `champs_utils.py` contiene funcionalidad relacionada con los campeones. Tiene funciones para generar el fichero de estadísticas de los campeones, generar el diccionario de frecuencias de roles por campeón y asignar los roles a una composición.
* `hero_freqs_generator.py` genera las frecuencias con las que son seleccionados los campeones.
* `hero_win_rates_generator.py` genera el porcentaje de victorias de cada campeón.

### NN_train
* `tuning.py` optimiza los valores de una MLP mediante validación cruzada.
* `train.py` entrena las tres redes neuronales y obtiene su valor de exactitud. Genera ficheros con la red neuronal, la representación de datos y la transformación usada para escalar los datos. Se necesitan los tres para usar la red neuronal en el árbol.

### mcts
* `node.py` implementa la funcionalidad de un nodo MCTS UCT.
* `player.py` contiene las posibles estrategias de un jugador. Puede elegir aleatoriamente, elegir según el porcentaje de los campeones o usando MCTS UCT. Desarrolla la funcionalidad del árbol de búsqueda.
* `captain_mode_draft.py` implementa la estructura del *draft*.
* `eval.py` evalúa las composiciones según sus coincidencias con las partidas de la base de datos.
* `games_roles_eval.pkl` es el fichero auxiliar que utiliza `eval.py` para realizar los cálculos.
* `experiment.py` enfrenta dos modelos y obtiene el porcentaje de victorias.
* `experiment_compositions.py` enfrenta un modelo consigo mismo para probar las composiciones que genera indicándole distintas composiciones. Aquí se usa el fichero `compositions.pkl`.



