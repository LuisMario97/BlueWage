/** Contrato de la API local y adaptación para las vistas de BlueWage. */
export const PUESTOS = ['Conductores de carga', 'Personal de control de almacén',
  'Operadores de maquinaria para mover mercancías', 'Personal de carga y descarga'];
export const REGIONES = ['CDMX/Edomex', 'Nuevo León', 'Jalisco', 'Bajío', 'Frontera Norte', 'Resto del país'];
export const LICENCIAS = ['Sin licencia', 'Estatal Chofer', 'Federal B', 'Federal C', 'Federal E'];
export const CERTIFICACIONES = ['Manejo de Montacargas Contrabalanceado', 'Seguridad e Higiene',
  'Manejo Defensivo', 'Maniobras de Carga y Descarga', 'Otra constancia DC-3', 'Ninguna'];
const configuracion = typeof window === 'undefined' ? undefined
  : (window as Window & {BLUEWAGE_CONFIG?: {apiBaseUrl: string}}).BLUEWAGE_CONFIG;
export const API_URL = `${configuracion?.apiBaseUrl || 'http://127.0.0.1:8000'}/api/estimar-perfil`;

export interface DatosUsuario {
  puesto: string; region: string; experiencia: number; licencia: string;
  certificaciones: string[]; horas: number;
}
export interface PerfilAPI {
  puesto: string; region: string; experiencia_anios: number; horas_semana: number;
  licencia: string; tiene_dc3: 0 | 1;
}
export interface RespuestaAPI {
  salario: { piso_p10: number; mediana_p50: number; techo_p90: number };
  moneda: 'MXN'; periodicidad: 'mensual'; cruce_corregido: boolean;
  orientacion: { modo: 'gemini' | 'fallback'; extracto_cv: string; recomendaciones: string[]; competencias_clave: string[] };
}
export interface BandaSalarial { p10: number; p50: number; p90: number }
export interface Recomendacion { titulo: string; accion: string; objetivo: string }
export interface Perfil {
  resumen: string; cv_markdown: string; recomendaciones: Recomendacion[];
  payload: { input: { datos_usuario: DatosUsuario; perfil_api: PerfilAPI }; respuesta_api: RespuestaAPI };
}
export const DATOS_INICIALES: DatosUsuario = {
  puesto: PUESTOS[0], region: REGIONES[0], experiencia: 5,
  licencia: 'Sin licencia', certificaciones: [], horas: 48,
};

export function validarDatos(datos: DatosUsuario): DatosUsuario {
  if (!datos || !PUESTOS.includes(datos.puesto)) throw new Error('Selecciona un puesto válido.');
  if (!REGIONES.includes(datos.region)) throw new Error('Selecciona una región válida.');
  if (!LICENCIAS.includes(datos.licencia)) throw new Error('Selecciona una licencia válida.');
  if (!Number.isInteger(datos.experiencia) || datos.experiencia < 0 || datos.experiencia > 30)
    throw new Error('La experiencia debe ser un entero entre 0 y 30 años.');
  if (!Number.isInteger(datos.horas) || datos.horas < 20 || datos.horas > 72)
    throw new Error('La jornada debe ser un entero entre 20 y 72 horas.');
  if (!Array.isArray(datos.certificaciones) || datos.certificaciones.some(c => !CERTIFICACIONES.includes(c)))
    throw new Error('Certificaciones inválidas.');
  if (datos.certificaciones.includes('Ninguna') && datos.certificaciones.length > 1)
    throw new Error('Quita “Ninguna” si seleccionas alguna certificación.');
  return { ...datos, certificaciones: [...new Set(datos.certificaciones.filter(c => c !== 'Ninguna'))] };
}

export function crearPerfilAPI(datos: DatosUsuario): PerfilAPI {
  const d = validarDatos(datos);
  return { puesto: d.puesto, region: d.region, experiencia_anios: d.experiencia,
    horas_semana: d.horas, licencia: d.licencia, tiene_dc3: d.certificaciones.length ? 1 : 0 };
}

function validarRespuesta(valor: unknown): asserts valor is RespuestaAPI {
  const r = valor as RespuestaAPI | null;
  const s = r?.salario;
  const valores = [s?.piso_p10, s?.mediana_p50, s?.techo_p90];
  if (!s || valores.some(v => typeof v !== 'number' || !Number.isFinite(v) || v <= 0)
      || s.piso_p10 > s.mediana_p50 || s.mediana_p50 > s.techo_p90
      || r?.moneda !== 'MXN' || r.periodicidad !== 'mensual'
      || typeof r.cruce_corregido !== 'boolean' || !['gemini', 'fallback'].includes(r.orientacion?.modo)
      || !Array.isArray(r.orientacion.competencias_clave) || r.orientacion.competencias_clave.length < 3 || r.orientacion.competencias_clave.length > 4
      || r.orientacion.competencias_clave.some(x => typeof x !== 'string' || !x.trim())
      || typeof r.orientacion.extracto_cv !== 'string' || !r.orientacion.extracto_cv.trim()
      || !Array.isArray(r.orientacion.recomendaciones) || r.orientacion.recomendaciones.length !== 3
      || r.orientacion.recomendaciones.some(x => typeof x !== 'string' || !x.trim())) {
    throw new Error('El servidor devolvió una respuesta inválida. Vuelve a intentarlo.');
  }
}

export async function estimarPerfil(datos: DatosUsuario): Promise<{ banda: BandaSalarial; perfil: Perfil }> {
  const d = validarDatos(datos);
  const entrada = crearPerfilAPI(d);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 40_000);
  try {
    let respuesta: Response;
    try {
      respuesta = await fetch(API_URL, { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(entrada), signal: controller.signal });
    } catch {
      throw new Error(controller.signal.aborted
        ? 'La consulta tardó demasiado. Vuelve a intentarlo.'
        : 'No pudimos conectar con el servidor local. Comprueba que FastAPI esté activo en el puerto 8000 y vuelve a intentarlo.');
    }
    if (!respuesta.ok) throw new Error(respuesta.status === 422
      ? 'El servidor rechazó los datos. Revisa los campos y vuelve a intentarlo.'
      : 'El servidor no pudo calcular la banda. Vuelve a intentarlo.');
    let resultado: unknown;
    try { resultado = await respuesta.json(); }
    catch { throw new Error('El servidor devolvió una respuesta inválida. Vuelve a intentarlo.'); }
    validarRespuesta(resultado);
    const banda = { p10: resultado.salario.piso_p10, p50: resultado.salario.mediana_p50, p90: resultado.salario.techo_p90 };
    const certificados = d.certificaciones.map(c => `- ${c}`).join('\n') || '- Sin certificaciones DC-3 declaradas.';
    const recomendaciones = resultado.orientacion.recomendaciones.map((accion, i) => ({
      titulo: `Recomendación ${i + 1}`, accion, objetivo: '',
    }));
    const cv_markdown = `# Ficha técnica · ${d.puesto}\n\n${resultado.orientacion.extracto_cv}\n\n## Licencia declarada\n${d.licencia}\n\n## Certificaciones DC-3 declaradas\n${certificados}\n\n## Áreas por desarrollar o validar\n${resultado.orientacion.competencias_clave.map(c => `- ${c}`).join('\n')}\n\n## Recomendaciones\n${recomendaciones.map(r => `- ${r.accion}`).join('\n')}\n\nPerfil elaborado con información declarada; credenciales no verificadas. Orientación: ${resultado.orientacion.modo === 'gemini' ? 'generada con Gemini, revisar antes de compartir' : 'respuesta local de contingencia'}.`;
    return { banda, perfil: { resumen: resultado.orientacion.extracto_cv, cv_markdown, recomendaciones,
      payload: { input: { datos_usuario: d, perfil_api: entrada }, respuesta_api: resultado } } };
  } finally { clearTimeout(timeout); }
}
