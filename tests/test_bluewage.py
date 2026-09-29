import json
import unittest
from pathlib import Path

from services import PUESTOS, REGIONES, generar_cv_y_recomendaciones, predecir_banda_salarial


class ServicesTest(unittest.TestCase):
    def setUp(self):
        self.datos = dict(puesto="Montacarguista", region="CDMX/Edomex", experiencia=5,
                          licencia="Sin licencia", certificaciones=[], horas=48)

    def test_bandas_ordenadas_en_extremos(self):
        for puesto in PUESTOS:
            for region in REGIONES:
                for experiencia, horas in [(0, 20), (30, 70)]:
                    banda = predecir_banda_salarial(dict(self.datos, puesto=puesto, region=region, experiencia=experiencia, horas=horas))
                    self.assertTrue(0 < banda["p10"] < banda["p50"] < banda["p90"])

    def test_credenciales_no_inventadas_y_payload_serializable(self):
        datos = dict(self.datos, experiencia=0)
        perfil = generar_cv_y_recomendaciones(datos, predecir_banda_salarial(datos))
        self.assertIn("sin experiencia práctica", perfil["cv_markdown"])
        self.assertIn("Sin certificaciones DC-3", perfil["cv_markdown"])
        self.assertEqual(len(perfil["recomendaciones"]), 3)
        json.dumps(perfil["payload"], ensure_ascii=False)

    def test_certificaciones_excluyentes(self):
        with self.assertRaises(ValueError):
            predecir_banda_salarial(dict(self.datos, certificaciones=["Ninguna", "Seguridad e Higiene"]))
        self.assertEqual(predecir_banda_salarial(self.datos), predecir_banda_salarial(dict(self.datos, certificaciones=["Ninguna"])))

    def test_limites(self):
        for cambio in [dict(horas=71), dict(experiencia=-1), dict(puesto="Otro")]:
            with self.assertRaises(ValueError):
                predecir_banda_salarial(dict(self.datos, **cambio))


class AppFlowTest(unittest.TestCase):
    def test_flujo_y_recalculo(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run()
        self.assertFalse(app.exception)
        app.button[0].click().run()
        self.assertEqual(app.session_state["paso"], 2)
        banda_anterior = app.session_state["banda"]["p50"]
        app.button[1].click().run()
        self.assertEqual(app.session_state["paso"], 3)
        self.assertFalse(app.exception)
        app.button[1].click().run()
        self.assertEqual(app.slider[0].value, 5)
        app.slider[0].set_value(20)
        app.button[0].click().run()
        self.assertGreater(app.session_state["banda"]["p50"], banda_anterior)
        self.assertIn("20 años", app.session_state["perfil"]["cv_markdown"])
        self.assertFalse(app.exception)


if __name__ == "__main__":
    unittest.main()
