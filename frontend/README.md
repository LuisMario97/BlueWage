# Frontend Angular

Pantallas de empleado/empresa, cuestionarios, banda salarial, editor de CV y
descripción de empleo. `src/app/services` contiene los clientes HTTP de FastAPI.

Ejecuta desde la raíz del repositorio: `npm ci`, `npm start`, `npm run build`.
Las configuraciones de npm, Angular y Vercel permanecen en la raíz.
La salida sigue siendo `dist/bluewage/browser`; no cambies Root Directory en Vercel.

`npm test` ejecuta pruebas de servicios; `npm run test:e2e` necesita FastAPI en
el puerto 8000. La URL pública se configura con BLUEWAGE_API_URL en Vercel.
