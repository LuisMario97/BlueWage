"""Pruebas del contrato con un artefacto temporal; no validan el modelo real."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import joblib
import numpy as np
from fastapi.testclient import TestClient

from backend.main import EXAMPLE, FEATURES, crear_app


class PreprocessorPrueba:
    def transform(self, entrada):
        assert list(entrada.columns) == FEATURES
        return np.zeros((len(entrada), 1))


class ModeloPrueba:
    def __init__(self, valor):
        self.valor = valor

    def predict(self, entrada):
        return np.full(len(entrada), self.valor)


@patch.dict("os.environ", {"GEMINI_API_KEY": "", "FRONTEND_ORIGINS": "https://bluewage-test.vercel.app"})
class ApiTest(unittest.TestCase):
    def test_contrato_correccion_validacion_y_cors(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "prueba.joblib"
            joblib.dump({
                "preprocessor": PreprocessorPrueba(), "feature_names": FEATURES,
                "model_p10": ModeloPrueba(12000),
                "model_p50": ModeloPrueba(11000),
                "model_p90": ModeloPrueba(15000),
            }, ruta)
            with TestClient(crear_app(ruta)) as cliente:
                self.assertEqual(cliente.get("/health").status_code, 200)
                self.assertEqual(cliente.get("/docs").status_code, 200)
                respuesta = cliente.post("/api/estimar-perfil", json=EXAMPLE)
                self.assertEqual(respuesta.status_code, 200)
                datos = respuesta.json()
                self.assertEqual(datos["salario"], {
                    "piso_p10": 12000, "mediana_p50": 12000, "techo_p90": 15000})
                self.assertTrue(datos["cruce_corregido"])
                self.assertEqual(len(datos["orientacion"]["recomendaciones"]), 3)
                self.assertIsNone(cliente.post("/api/estimar-perfil?incluir_orientacion=false",
                                               json=EXAMPLE).json()["orientacion"])
                for invalido in ({**EXAMPLE, "horas_semana": 100},
                                 {**EXAMPLE, "puesto": "desconocido"},
                                 {**EXAMPLE, "salario_mensual": 20000}):
                    self.assertEqual(cliente.post("/api/estimar-perfil", json=invalido).status_code, 422)
                for origen in ("http://localhost:4200", "http://127.0.0.1:8501", "https://bluewage-test.vercel.app"):
                    cors = cliente.options("/api/estimar-perfil", headers={
                        "Origin": origen, "Access-Control-Request-Method": "POST",
                        "Access-Control-Request-Headers": "content-type"})
                    self.assertEqual(cors.headers["access-control-allow-origin"], origen)
                cors = cliente.options("/api/estimar-perfil", headers={
                    "Origin": "https://example.com", "Access-Control-Request-Method": "POST"})
                self.assertNotIn("access-control-allow-origin", cors.headers)

    def test_modelo_ausente(self):
        with tempfile.TemporaryDirectory() as carpeta:
            with self.assertRaises(FileNotFoundError):
                with TestClient(crear_app(Path(carpeta) / "ausente.joblib")):
                    pass


if __name__ == "__main__":
    unittest.main()
