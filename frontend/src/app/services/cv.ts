import { API_URL } from './bluewage';

export interface DatosCV {
  nombre: string; telefono: string; email: string; ubicacion: string;
  puesto_objetivo: string; resumen: string; experiencia_laboral: string;
  formacion: string; habilidades: string; certificaciones: string;
  idiomas: string; licencia: string; enlaces: string; disponibilidad: string;
}

export function cvVacio(): DatosCV {
  return {nombre: '', telefono: '', email: '', ubicacion: '', puesto_objetivo: '',
    resumen: '', experiencia_laboral: '', formacion: '', habilidades: '',
    certificaciones: '', idiomas: '', licencia: '', enlaces: '', disponibilidad: ''};
}

export async function solicitarPDF(cv: DatosCV): Promise<Blob> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 20000);
  try {
    let respuesta: Response;
    try {
      respuesta = await fetch(API_URL.replace('/estimar-perfil', '/cv/pdf'), {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(cv), signal: controller.signal,
      });
    } catch { throw new Error('No se pudo descargar el PDF. Comprueba la conexión con el servidor local e inténtalo de nuevo.'); }
    if (!respuesta.ok) {
      if (respuesta.status === 422) {
        throw new Error('Revisa los datos: nombre, teléfono de 7 a 15 dígitos, correo válido (si lo incluyes) y resumen de al menos 20 caracteres.');
      }
      throw new Error('No se pudo generar el PDF. Tus datos siguen aquí; puedes reintentarlo.');
    }
    if (!respuesta.headers.get('content-type')?.includes('application/pdf')) {
      throw new Error('El servidor no devolvió un PDF válido.');
    }
    const pdf = await respuesta.blob();
    if ((await pdf.slice(0, 5).text()) !== '%PDF-') throw new Error('El PDF recibido no es válido.');
    return pdf;
  } finally { clearTimeout(timeout); }
}
