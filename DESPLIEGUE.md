# Publicar BlueWage: GitHub → Render + Vercel

Los archivos están preparados; todavía debes crear los servicios y configurar sus dominios.
La API key nunca se guarda en el repositorio ni en Angular.

## 1. Subir a GitHub

En GitHub Desktop usa File → Add local repository y selecciona esta carpeta BlueWage.
Revisa Changes, crea el primer commit y pulsa Publish repository.
Conserva activada la opción de repositorio privado.

El repositorio incluye el modelo `backend/models/bluewage_pipeline_cuantil.joblib` (aprox. 421 KiB).
`.gitignore` excluye entornos virtuales, secretos, dependencias, PDFs de prueba y temporales.
`.env.example` es una referencia vacía: no pegues ahí una clave real.

## 2. Backend en Render

1. New → Web Service → conecta el repositorio privado.
2. Runtime: Docker. Raíz: carpeta raíz. Dockerfile: `./Dockerfile`.
3. Health Check Path: `/health`. Revisa el precio del plan elegido.
4. En Environment configura:

| Variable | Valor |
| --- | --- |
| GEMINI_API_KEY | Tu clave privada de Google |
| GEMINI_MODEL | gemini-3.8-flash (modelo usado localmente) |
| GEMINI_FALLBACK_MODEL | gemini-3.5-flash-lite |
| FRONTEND_ORIGINS | Se completa con el dominio de Vercel en el paso 4 |

Los modelos de Gemini deben estar disponibles en tu cuenta. No configures la
clave en variables del frontend. El Dockerfile usa Python 3.12, instala libgomp1
y las versiones directas de `backend/requirements-production.txt`, incluye el
modelo y arranca Uvicorn en `0.0.0.0:$PORT` sin reload.

5. Despliega y copia el origen público real, por ejemplo `https://mi-api.onrender.com`.
6. Abre `/health`: comprueba `modelo_cargado: true`.
7. Abre `/docs` y prueba `POST /api/estimar-perfil` con su ejemplo.

No se ha comprobado todavía el contenedor en Linux: revisa los logs del primer
build y arranque. Las versiones directas se tomaron del entorno Windows probado;
las dependencias transitivas se resuelven durante el build.

## 3. Frontend en Vercel

1. Add New → Project → importa el mismo repositorio.
2. Framework: Angular. Root Directory: raíz. Node.js: 22.x.
3. Install: `npm ci`. Build: `npm run build`. Output: `dist/bluewage/browser`.
4. En Environment Variables agrega `BLUEWAGE_API_URL` con el origen real de
   Render, por ejemplo `https://mi-api.onrender.com`, sin `/api` ni otras rutas.
   Selecciona Production; si usarás Preview, configura también ese entorno.
5. Pulsa Deploy y copia el origen real, por ejemplo `https://mi-web.vercel.app`.

`npm run build` genera `frontend/public/config.js` con esta URL pública; ningún secreto
se exporta. En Vercel la compilación falla si falta la variable o apunta a localhost.
Al cambiarla, haz Redeploy para que el navegador reciba la nueva configuración.
`.vercelignore` excluye backend y modelo del despliegue del frontend.

## 4. Autorizar el frontend

En Render configura `FRONTEND_ORIGINS=https://mi-web.vercel.app`, usando tu URL
real. Guarda y redespliega. Se aceptan varios orígenes exactos separados por comas.
Para previews de Vercel debes agregar su URL exacta; no se autorizan todos los
dominios vercel.app. Las interfaces localhost siguen funcionando.

## 5. Validar

- Desde Vercel calcula una banda y revisa la orientación Gemini o su fallback.
- Completa nombre, teléfono, varios empleos y estudios. Descarga y abre el PDF.
- Prueba desde un celular sin depender de los servidores de tu computadora.
- Si hay error CORS, revisa FRONTEND_ORIGINS. Si falla la conexión, revisa
  BLUEWAGE_API_URL y `/health`. Consulta los logs de Render para problemas de carga.

La inferencia sigue siendo local al backend; Gemini solo recibe el perfil
operativo y la banda. El PDF se genera en memoria en FastAPI.

## Desarrollo local

`npm ci` y `npm start` preparan automáticamente la URL `http://127.0.0.1:8000`
cuando BLUEWAGE_API_URL no está definida. No uses `ng serve` directamente.
Las variables del panel cloud no se transfieren a tu PowerShell, ni los archivos
`.env` se cargan automáticamente. Arranca FastAPI con el comando del README.

Comprobaciones: `npm test`, `npm run build` y
`.\.venv-backend\Scripts\python.exe -m unittest backend.test_api backend.test_llm backend.test_cv_pdf`.

Referencias: https://render.com/docs/docker y https://vercel.com/docs/environment-variables
