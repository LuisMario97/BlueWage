import {API_URL, crearPerfilAPI, validarDatos} from './bluewage';
import type {BandaSalarial, DatosUsuario} from './bluewage';

/** Usa el mismo modelo salarial; no solicita orientación de CV al proveedor. */
export async function estimarVacante(datos: DatosUsuario): Promise<BandaSalarial> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 40000);
  try {
    const respuesta = await fetch(`${API_URL}?incluir_orientacion=false`, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify(crearPerfilAPI(datos)), signal:controller.signal,
    });
    if (!respuesta.ok) throw new Error(respuesta.status === 422
      ? 'Revisa los requisitos de la vacante.' : 'No se pudo estimar la banda. Inténtalo de nuevo.');
    const r = await respuesta.json();
    const s = r?.salario;
    if (!s || [s.piso_p10, s.mediana_p50, s.techo_p90].some(v => typeof v !== 'number' || !Number.isFinite(v) || v <= 0)
        || s.piso_p10 > s.mediana_p50 || s.mediana_p50 > s.techo_p90 || r.moneda !== 'MXN' || r.periodicidad !== 'mensual')
      throw new Error('El servidor devolvió una banda inválida.');
    return {p10:s.piso_p10, p50:s.mediana_p50, p90:s.techo_p90};
  } catch (error) {
    if (controller.signal.aborted) throw new Error('La consulta tardó demasiado. Espera un momento y vuelve a intentarlo.');
    if (error instanceof TypeError) throw new Error('No pudimos conectar con el servidor. Espera un momento y vuelve a intentarlo.');
    throw error;
  } finally { clearTimeout(timeout); }
}

/** Borrador basado solo en requisitos declarados: no inventa prestaciones ni empresa. */
export function describirVacante(datos: DatosUsuario, banda: BandaSalarial): string {
  const d = validarDatos(datos);
  const moneda = (n: number) => new Intl.NumberFormat('es-MX', {style:'currency', currency:'MXN'}).format(n);
  return [
    `VACANTE: ${d.puesto}`,
    `Buscamos personal para el puesto de ${d.puesto} en la región ${d.region}.`,
    `REQUISITOS\n${d.experiencia === 0 ? 'Sin experiencia previa requerida.' : `Experiencia requerida en el rol: ${d.experiencia} años.`}\n${d.licencia === 'Sin licencia' ? 'No se requiere licencia de conducir.' : `Licencia requerida: ${d.licencia}.`}\n${d.certificaciones.length ? `Constancias DC-3 requeridas: ${d.certificaciones.join(', ')}.` : 'Sin constancias DC-3 requeridas.'}`,
    `JORNADA\n${d.horas} horas semanales.`,
    `REFERENCIA SALARIAL\nBanda mensual estimada: ${moneda(banda.p10)} a ${moneda(banda.p90)} MXN.\nMediana de referencia: ${moneda(banda.p50)} MXN.\nEstimación orientativa; la empresa debe confirmar el sueldo ofrecido.`,
  ].join('\n\n');
}
