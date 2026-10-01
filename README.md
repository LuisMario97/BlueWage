# BlueWage · Angular y FastAPI local

Para subir a GitHub y desplegar Angular en Vercel y FastAPI en Render, sigue
[DESPLIEGUE.md](DESPLIEGUE.md). Incluye Docker, variables de entorno y verificación.

La interfaz consulta el pipeline cuantílico real a través de FastAPI. El modelo
fue entrenado con datos sintéticos anclados en medianas ENOE. El CV y las tres recomendaciones
usan Gemini cuando se configura GEMINI_API_KEY; ante fallos se usa un respaldo local.
Consulta backend/README.md para habilitarlo. El perfil y la banda se envían a Google
únicamente cuando se solicita orientación con Gemini habilitado.

## Iniciar ambos servidores

Desde la raíz de BlueWage, en dos terminales PowerShell:

```powershell
.\.venv-backend\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

```powershell
npm.cmd start
```

Abre http://127.0.0.1:4200 para el formulario y http://127.0.0.1:8000/docs
para Swagger. Las instrucciones de instalación y del archivo joblib están en
[backend/README.md](backend/README.md). La dependencia scikit-learn está fijada
al 1.6.1 usado para exportar el modelo actual.

## Recorrido

Al entrar se elige «Soy empleado» o «Soy empresa». El flujo de empleado conserva
el cuestionario y el CV en PDF. En empresa, los seis campos describen requisitos
de una vacante: se consulta el mismo modelo con `incluir_orientacion=false` y se
prepara una descripción editable que puede copiarse. El borrador usa los datos
declarados, sin llamar a Gemini ni inventar empresa, prestaciones o funciones.
La banda incluida es una referencia; la empresa confirma el sueldo ofrecido.
Cambiar de rol inicia un cuestionario limpio. Recalcular sustituye el borrador.

1. Elige ocupación, región, experiencia, jornada, licencia y constancias DC-3.
2. Consulta la banda: los botones se bloquean mientras llega la respuesta. Un
   error conserva los campos y permite reintentar, sin mostrar cifras antiguas.
3. Revisa P10, P50 y P90 con centavos, iguales a los de la respuesta de Swagger.
4. Pulsa «Crear mi CV en PDF», completa nombre y teléfono, y edita el resumen,
   experiencia, estudios, habilidades y certificaciones. Revisa la vista previa
   y descarga el PDF para compartir por WhatsApp o correo.
   Experiencia y escolaridad se capturan con cuestionarios: puedes agregar o
   eliminar empleos y estudios, indicar años y marcar trabajo actual o estudios
   en curso. Los registros vacíos se omiten y se validan los periodos antes de descargar.
5. Edita el perfil y vuelve a consultar para actualizar todos los resultados.

El cliente transforma experiencia/horas a `experiencia_anios`/`horas_semana`.
Una o varias constancias DC-3 se envían como `tiene_dc3=1`; vacío o Ninguna,
como 0. Los nombres de cursos permanecen en la ficha local; el modelo recibe
solo el indicador binario. La jornada acepta 20–72 horas. Las categorías son
exactamente las del backend. No se aplica una fórmula salarial adicional.

La URL se genera desde `BLUEWAGE_API_URL` al ejecutar `npm start` o `npm run build`.
Sin esa variable se utiliza el backend local. En Vercel es obligatoria.
El cliente valida la respuesta, conserva el orden de los cuantiles y muestra
mensajes ante desconexión, espera superior a 40 segundos o error del servidor.
La corrección de cruces se realiza en FastAPI.

## Pruebas

```powershell
npm.cmd test
npm.cmd run build
npm.cmd run test:e2e
```

Las pruebas E2E requieren FastAPI activo con el joblib real. Playwright levanta
Angular si hace falta y usa Microsoft Edge instalado. Verifica el payload, la
igualdad entre salarios de API y UI, cuatro ocupaciones, recálculo, descargas,
móvil y recuperación de errores. La inferencia se verifica sin llamar a Gemini;
las pruebas del editor simulan la orientación y descargan un PDF real.
`test-results/` contiene capturas.

```powershell
.\.venv-backend\Scripts\python.exe -m unittest backend.test_api -v
.\.venv-backend\Scripts\python.exe -m backend.smoke_model
```

La primera prueba Python utiliza un artefacto temporal de prueba; la segunda
compara la API con las predicciones directas del modelo real.

## Archivos principales

- `src/app/services/bluewage.ts`: catálogos, contrato HTTP y adaptación de respuesta.
- `src/app/app.component.ts`: estados, navegación, consulta y descargas.
- `src/app/app.component.html`: formulario, banda y editor de CV.
- `src/app/services/cv.ts`: solicitud y descarga del PDF.
- `backend/cv_pdf.py`: validación de datos y maquetación A4 con ReportLab.
- `backend/main.py`: validación, inferencia y orientación local.

Los archivos de Streamlit permanecen como referencia del prototipo anterior.
Vercel publica Angular y Render ejecuta FastAPI mediante Docker; consulta
DESPLIEGUE.md para configurar los dominios HTTPS y CORS.
