import os
import joblib
from sklearn.tree import DecisionTreeClassifier

def crear_arbol_coneval_simulado():
    X_train = [
        [800.0, 0.9, 5.0, 1.0],
        [1200.0, 0.8, 4.0, 1.0],
        [2500.0, 0.5, 3.0, 0.0],
        [3200.0, 0.6, 4.0, 0.0],
        [7000.0, 0.3, 2.0, 0.0],
        [9000.0, 0.2, 2.0, 0.0],
    ]
    y_train = [2, 2, 1, 1, 0, 0]

    clf = DecisionTreeClassifier(max_depth=3, random_state=42)
    clf.fit(X_train, y_train)

    ruta_destino = os.path.join('modeloML', 'modelos_preentrenados', 'clasificador_coneval.joblib')
    os.makedirs(os.path.dirname(ruta_destino), exist_ok=True)
    
    joblib.dump(clf, ruta_destino)
    print("¡Modelo preentrenado guardado exitosamente!")

if __name__ == '__main__':
    crear_arbol_coneval_simulado()
