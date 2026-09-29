from io import BytesIO
from pathlib import Path
import unittest

from pydantic import ValidationError
from pypdf import PdfReader
from backend.cv_pdf import DatosCV, generar_cv_pdf


EJEMPLO_CV = {
    "nombre": "María López García",
    "telefono": "+52 55 0000 0000",
    "email": "maria@example.com",
    "ubicacion": "Monterrey, Nuevo León",
    "puesto_objetivo": "Conductora de carga",
    "resumen": "Conductora con cinco años de experiencia en transporte de mercancías. Interés en operaciones de distribución y seguridad vial.",
    "experiencia_laboral": "Conductora de reparto | Empresa de ejemplo\nMonterrey | Enero 2021 - Actualidad\nDistribución de mercancías y revisión de documentos de entrega.\nInspección diaria del vehículo y registro de incidencias.",
    "formacion": "Bachillerato concluido | Institución de ejemplo | 2018",
    "habilidades": "Inspección preventiva del vehículo\nRegistro de entregas\nPlaneación de recorridos",
    "certificaciones": "Manejo defensivo | Institución de ejemplo | 2024",
    "licencia": "Federal E",
    "idiomas": "Español: nativo",
    "disponibilidad": "Disponibilidad para viajar y trabajar en turnos.",
}


class CVTest(unittest.TestCase):
    def test_pdf_contacto_texto_y_secciones(self):
        pdf = generar_cv_pdf(DatosCV(**EJEMPLO_CV))
        lector = PdfReader(BytesIO(pdf))
        texto = '\n'.join(p.extract_text() for p in lector.pages)
        self.assertEqual(len(lector.pages), 1)
        for valor in (EJEMPLO_CV['nombre'], EJEMPLO_CV['telefono'], EJEMPLO_CV['email'], 'EXPERIENCIA LABORAL', 'FORMACIÓN ACADÉMICA'):
            self.assertIn(valor, texto)
        self.assertNotIn('P90', texto)
        self.assertNotIn('Recomendación', texto)

    def test_omite_vacios_y_escapa_markup(self):
        datos = DatosCV(nombre='Ana <b>Prueba</b>', telefono='5551234567', puesto_objetivo='Almacén', resumen='Persona interesada en trabajar en un almacén.')
        texto = PdfReader(BytesIO(generar_cv_pdf(datos))).pages[0].extract_text()
        self.assertIn('<b>Prueba</b>', texto)
        self.assertNotIn('EXPERIENCIA LABORAL', texto)
        self.assertNotIn('FORMACIÓN ACADÉMICA', texto)

    def test_multipagina_sin_perder_texto(self):
        datos = DatosCV(**{**EJEMPLO_CV, 'experiencia_laboral': ('Registro de ejemplo: labores y resultados declarados.\n' * 80) + 'MARCADOR FINAL'})
        lector = PdfReader(BytesIO(generar_cv_pdf(datos)))
        self.assertGreater(len(lector.pages), 1)
        self.assertIn('Registro de ejemplo', lector.pages[0].extract_text())
        self.assertIn('MARCADOR FINAL', ''.join(p.extract_text() for p in lector.pages))

    def test_validacion(self):
        for cambio in ({'nombre': ''}, {'telefono': 'abc1234'}, {'email': 'no-correo'}, {'resumen': 'Hola'}):
            with self.assertRaises(ValidationError):
                DatosCV(**{**EJEMPLO_CV, **cambio})


if __name__ == '__main__':
    # Archivos de QA, solo datos ilustrativos, no currículums de usuarios reales.
    carpeta = Path('tmp/pdfs')
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / 'cv-ejemplo.pdf').write_bytes(generar_cv_pdf(DatosCV(**EJEMPLO_CV)))
    largo = {**EJEMPLO_CV, 'experiencia_laboral': ('Registro de ejemplo: labores y resultados declarados.\n' * 80) + 'MARCADOR FINAL'}
    (carpeta / 'cv-largo.pdf').write_bytes(generar_cv_pdf(DatosCV(**largo)))
    unittest.main()
