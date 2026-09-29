# Backend local BlueWage

El servidor ejecuta el archivo de la Celda 6 y devuelve tres salarios mensuales
en MXN. El CV y las tres recomendaciones se generan con Gemini cuando GEMINI_API_KEY está disponible; si falla, se usa un respaldo local. La interfaz Angular consulta este backend desde http://127.0.0.1:4200.

## 1. Archivos

Desde la carpeta BlueWage:

```text
BlueWage/
  bluewage_pipeline_cuantil.joblib  <-- copia aquí el archivo de Colab
  backend/
    main.py
    requirements.txt
    requirements-dev.txt
    test_api.py
    smoke_model.py
    README.md
```

El archivo del modelo se carga desde la raíz o desde BLUEWAGE_MODEL_PATH. No se incluye
un modelo salarial ficticio como sustituto. Solo abre archivos joblib confiables.

## 2. Instalar (PowerShell, desde BlueWage)

Python 3.12 es una opción para este proyecto. Idealmente usa la misma versión
de Python, scikit-learn, LightGBM, NumPy, pandas y joblib que en Colab.

```powershell
py -3.12 -m venv .venv-backend
.\.venv-backend\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
```

No hace falta activar el entorno ni cambiar la política de PowerShell.
`requirements-dev.txt` añade httpx para las pruebas; para solo ejecutar el
servidor basta `backend/requirements.txt`.

Los rangos de dependencias no certifican compatibilidad con un pickle creado
en otra versión. Si aparece una advertencia de versión al cargar, consulta en
Colab las versiones y ajusta el entorno local antes de confiar en la inferencia:

```python
import sys
from importlib.metadata import version
print(sys.version)
for paquete in ["scikit-learn", "lightgbm", "numpy", "pandas", "joblib"]:
    print(paquete, version(paquete))
```

Para usar un archivo fuera de la raíz, configura su ruta real en la misma terminal:

```powershell
$env:BLUEWAGE_MODEL_PATH = 'C:\ruta\real\bluewage_pipeline_cuantil.joblib'
```

## 3. Iniciar

```powershell
.\.venv-backend\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Se carga una vez por proceso, antes de aceptar solicitudes. `--reload` vuelve
a cargar si cambia el código. Si falta el archivo o está mal formado, el arranque
falla con un mensaje en consola: no devuelve salarios simulados.

## 4. Probar en el navegador

1. Abre http://127.0.0.1:8000/health: debe indicar `modelo_cargado: true`.
2. Abre http://127.0.0.1:8000/docs.
3. Expande `POST /api/estimar-perfil` y pulsa **Try it out**.
4. Deja `incluir_orientacion=true` y usa el ejemplo:

```json
{
  "puesto": "Conductores de carga",
  "region": "Nuevo León",
  "experiencia_anios": 5,
  "horas_semana": 48,
  "licencia": "Federal E",
  "tiene_dc3": 1
}
```

5. Pulsa **Execute**. Debe responder 200 con `salario.piso_p10`,
   `salario.mediana_p50`, `salario.techo_p90`, moneda, periodicidad,
   `cruce_corregido` y `orientacion` (modo, extracto, competencias y tres recomendaciones).
6. Confirma P10 ≤ P50 ≤ P90. Usa exactamente el mismo perfil en Colab para
   comparar números. No existe un salario esperado fijo independiente del modelo.
7. Prueba `horas_semana: 100`: debe responder 422; los nombres de categorías
   desconocidos y campos extra también se rechazan.

`incluir_orientacion=false` devuelve `orientacion: null`. El servidor usa
`np.maximum.accumulate`, igual que la Celda 6, y redondea al final. Puede elevar
P50/P90 cuando hay cruces; no garantiza cobertura estadística.

La API y la inferencia son locales. Swagger carga sus recursos visuales desde
un CDN por defecto; abrir `/docs` por primera vez puede requerir Internet.
Con GEMINI_API_KEY configurada, el perfil y la banda se envían a Google; los modelos salariales siguen siendo locales.

## 5. Verificación automática

```powershell
.\.venv-backend\Scripts\python.exe -m unittest backend.test_api -v
.\.venv-backend\Scripts\python.exe -m unittest backend.test_cv_pdf -v
.\.venv-backend\Scripts\python.exe -m backend.smoke_model
```

La primera prueba verifica validación, CORS y corrección con un artefacto
temporal de prueba. La segunda necesita el modelo real y compara la respuesta
HTTP con sus predicciones directas. No necesitas arrancar uvicorn para esas pruebas.
Esto verifica la integración; no demuestra exactitud en el mercado laboral.

## 6. Conectar después una interfaz local

### CV formal en PDF

`POST /api/cv/pdf` recibe los campos del editor y devuelve `application/pdf`
con nombre de descarga `BlueWage_CV.pdf`. Requiere nombre, teléfono, puesto
objetivo y resumen profesional; correo, ubicación, experiencia laboral,
formación, habilidades, certificaciones, licencia, idiomas, enlaces y
disponibilidad son opcionales. Las secciones vacías se omiten.

El PDF se genera en memoria con ReportLab: no se guarda en el servidor ni se
envían los datos de contacto a Gemini. El usuario revisa y edita el texto antes
de descargar. Salarios, recomendaciones y competencias sugeridas no se añaden
al documento. Los campos permanecen durante la sesión de Angular; recargar la
página los borra. Recalcular actualiza resumen, puesto, licencia y constancias.

### Acceso desde la interfaz

CORS acepta http/https en localhost, 127.0.0.1 y ::1 con cualquier puerto,
incluidos Angular (4200), HTML (5500) y Streamlit (8501). Para HTML, usa un
servidor local en vez de abrir `file://`:

```powershell
.\.venv-backend\Scripts\python.exe -m http.server 5500 --bind 127.0.0.1
```

Desde JavaScript, envía las seis claves exactas (no los nombres anteriores
`experiencia`, `horas` o `certificaciones` de la demo):

```javascript
const respuesta = await fetch('http://127.0.0.1:8000/api/estimar-perfil', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(perfil)
});
if (!respuesta.ok) throw new Error(JSON.stringify(await respuesta.json()));
const estimacion = await respuesta.json();
```

Referencias: [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/)
y [CORS](https://fastapi.tiangolo.com/tutorial/cors/).


## Gemini: configuración y contrato

Instala las dependencias actualizadas y define variables en la misma terminal
que inicia uvicorn. La clave no va en Angular, Git ni en el JSON del trabajador.
Los archivos `.env` no se cargan automáticamente en esta implementación.

```powershell
.\.venv-backend\Scripts\python.exe -m pip install -r backend/requirements.txt
$env:GEMINI_API_KEY = 'TU_CLAVE_PRIVADA'
$env:GEMINI_MODEL = 'gemini-3.8-flash'
.\.venv-backend\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Detén el servidor anterior antes de reiniciarlo desde la terminal con esas variables.
Usa un modelo disponible en tu cuenta que soporte salida estructurada. El valor
por defecto es gemini-3.8-flash; se puede cambiar sin modificar el código.

`backend/llm.py` contiene `generar_perfil_con_llm(datos_trabajador, banda_salarial)`.
La salida tiene `resumen_cv`, 3–4 `competencias_clave`, exactamente 3 elementos en
`plan_upskilling` y un campo adicional `modo` (`gemini` o `fallback`).
`main.py` conserva `extracto_cv` y `recomendaciones` como alias para Angular.
El endpoint es async; LightGBM se ejecuta en un threadpool y Gemini se espera
con await. `incluir_orientacion=false` evita llamar a Gemini.

Se valida tanto el esquema enviado al proveedor como el JSON recibido. Hay un
presupuesto de 30 segundos, menor al timeout del frontend. Ausencia de clave,
cuota, errores de red, bloqueo de contenido, JSON inválido o timeout activan el
respaldo. Los logs muestran solo el tipo de excepción, no claves ni perfiles.
La validación garantiza forma y cardinalidad, no veracidad semántica: el CV debe
revisarse antes de compartirlo. Las competencias son áreas para desarrollar o
validar, no credenciales acreditadas. P90 no es una promesa de salario.

```powershell
.\.venv-backend\Scripts\python.exe -m unittest backend.test_llm backend.test_api -v
```

Las pruebas usan respuestas simuladas del proveedor y no consumen cuota.
Referencia: https://googleapis.github.io/python-genai/

Si GEMINI_MODEL conserva gemini-2.5-flash, el backend lo migra a gemini-3.8-flash porque el proveedor rechaza el anterior para cuentas nuevas. /health informa el modelo efectivo.

Ante HTTP 503 (saturación), se realiza un único intento alternativo con GEMINI_FALLBACK_MODEL (gemini-3.5-flash-lite por defecto), dentro del mismo límite de 30 segundos. El cliente espera hasta 40 segundos. motivo_fallback identifica la causa sin revelar claves.
