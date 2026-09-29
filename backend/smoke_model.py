"""Compara el endpoint con predicciones directas del artefacto REAL."""
import os
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from backend.main import EXAMPLE, ROOT, cargar_pipeline, crear_app


def main():
    ruta = Path(os.environ.get("BLUEWAGE_MODEL_PATH", str(ROOT / "bluewage_pipeline_cuantil.joblib")))
    pipeline = cargar_pipeline(ruta)
    entrada = pd.DataFrame([EXAMPLE])[pipeline["feature_names"]]
    matriz = pipeline["preprocessor"].transform(entrada)
    crudos = [float(pipeline[f"model_{q}"].predict(matriz)[0]) for q in ("p10", "p50", "p90")]
    esperados = np.round(np.maximum.accumulate(crudos), 2)
    with TestClient(crear_app(ruta)) as cliente:
        respuesta = cliente.post("/api/estimar-perfil", json=EXAMPLE)
        respuesta.raise_for_status()
        banda = respuesta.json()["salario"]
    recibidos = [banda[k] for k in ("piso_p10", "mediana_p50", "techo_p90")]
    np.testing.assert_allclose(recibidos, esperados, rtol=0, atol=0.01)
    print("Predicciones crudas:", crudos)
    print("API:", banda)
    print("OK: API y modelo real coinciden después de corregir cruces.")


if __name__ == "__main__":
    main()
