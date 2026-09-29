import {mkdirSync, writeFileSync} from 'node:fs';

// Solo una URL pública llega al navegador. Nunca exportar process.env completo.
const configured = process.env.BLUEWAGE_API_URL?.trim();
if (process.env.VERCEL && !configured) {
  throw new Error('Configura BLUEWAGE_API_URL en Vercel con el origen HTTPS de Render.');
}
const url = new URL(configured || 'http://127.0.0.1:8000');
const local = ['127.0.0.1', 'localhost', '[::1]'].includes(url.hostname);
if (url.username || url.password || url.search || url.hash || url.pathname !== '/' ||
    !(url.protocol === 'https:' || (local && url.protocol === 'http:')) ||
    (process.env.VERCEL && local)) {
  throw new Error('BLUEWAGE_API_URL debe ser un origen HTTPS, sin rutas ni credenciales; HTTP solo se permite en local.');
}
mkdirSync(new URL('../public/', import.meta.url), {recursive:true});
writeFileSync(new URL('../public/config.js', import.meta.url),
  `window.BLUEWAGE_CONFIG = ${JSON.stringify({apiBaseUrl:url.origin})};\n`);
console.log('Configuración pública del frontend preparada.');
