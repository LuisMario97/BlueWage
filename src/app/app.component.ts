import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { JsonPipe } from '@angular/common';
import { CERTIFICACIONES, DATOS_INICIALES, LICENCIAS, PUESTOS, REGIONES,
  estimarPerfil } from './services/bluewage';
import type { BandaSalarial, DatosUsuario, Perfil } from './services/bluewage';
import { cvVacio, solicitarPDF } from './services/cv';
import type { DatosCV } from './services/cv';

interface EmpleoCV { empresa: string; puesto: string; inicio: number | null; fin: number | null; actual: boolean; funciones: string }
interface EstudioCV { nivel: string; institucion: string; especialidad: string; inicio: number | null; fin: number | null; estado: string }

@Component({
  selector: 'app-root', standalone: true, imports: [FormsModule, JsonPipe],
  templateUrl: './app.component.html',
})
export class AppComponent {
  readonly puestos = PUESTOS;
  readonly regiones = REGIONES;
  readonly licencias = LICENCIAS;
  readonly certificaciones = CERTIFICACIONES;
  readonly pasos = ['Tu experiencia', 'Tu banda salarial', 'Tu currículum'];
  readonly seccionesCV = [
    {clave: 'resumen', titulo: 'Perfil profesional', ayuda: 'Revisa el texto propuesto y conserva solo hechos reales.', max: 2000},
    {clave: 'experiencia_laboral', titulo: 'Experiencia laboral', ayuda: 'Por cada empleo: puesto, empresa, ciudad, fechas y funciones o logros. Separa empleos con una línea en blanco.', max: 6000},
    {clave: 'formacion', titulo: 'Formación académica', ayuda: 'Nivel de estudios, institución, fechas y estado (concluido o en curso).', max: 3000},
    {clave: 'habilidades', titulo: 'Habilidades que dominas', ayuda: 'Incluye únicamente habilidades reales: equipos, inventarios, herramientas o procedimientos. Una por línea.', max: 2000},
    {clave: 'certificaciones', titulo: 'Cursos y certificaciones', ayuda: 'Nombre del curso, institución y fecha, si los conoces. No incluyas cursos que solo planeas tomar.', max: 2000},
    {clave: 'idiomas', titulo: 'Idiomas', ayuda: 'Idioma y nivel real de dominio.', max: 1000},
    {clave: 'disponibilidad', titulo: 'Disponibilidad', ayuda: 'Opcional: turnos, incorporación, viajes o cambio de residencia.', max: 800},
  ] as const;
  readonly metricas = [
    { clave: 'p10', titulo: 'P10 · Piso' }, { clave: 'p50', titulo: 'P50 · Mediana' },
    { clave: 'p90', titulo: 'P90 · Banda superior' },
  ] as const;
  paso = signal(1);
  error = signal('');
  cargando = signal(false);
  datos: DatosUsuario = { ...DATOS_INICIALES, certificaciones: [] };
  banda: BandaSalarial | null = null;
  perfil: Perfil | null = null;
  cv: DatosCV = cvVacio();
  readonly anioActual = new Date().getFullYear();
  readonly nivelesEstudio = ['Primaria', 'Secundaria', 'Bachillerato / Preparatoria', 'Carrera técnica', 'Técnico superior universitario', 'Licenciatura / Ingeniería', 'Posgrado', 'Otro'];
  empleos: EmpleoCV[] = [];
  estudios: EstudioCV[] = [];
  constructor() { this.agregarEmpleo(); this.agregarEstudio(); }

  agregarEmpleo(): void {
    this.empleos.push({empresa:'', puesto:'', inicio:null, fin:null, actual:false, funciones:''});
  }
  agregarEstudio(): void {
    this.estudios.push({nivel:'', institucion:'', especialidad:'', inicio:null, fin:null, estado:''});
  }
  get empleosCompletados(): EmpleoCV[] {
    return this.empleos.filter(e => e.empresa.trim() || e.puesto.trim() || e.inicio !== null || e.fin !== null || e.actual || e.funciones.trim());
  }
  get estudiosCompletados(): EstudioCV[] {
    return this.estudios.filter(e => e.nivel || e.institucion.trim() || e.especialidad.trim() || e.inicio !== null || e.fin !== null || e.estado);
  }
  get cvCompleto(): DatosCV {
    return {...this.cv,
      experiencia_laboral: this.empleosCompletados.map(e => [
        [e.puesto.trim(), e.empresa.trim()].filter(Boolean).join(' | '),
        [e.inicio, e.actual ? 'Actualidad' : e.fin].filter(v => v !== null).join(' - '),
        e.funciones.trim(),
      ].filter(Boolean).join('\n')).join('\n\n'),
      formacion: this.estudiosCompletados.map(e => [
        [e.nivel, e.especialidad.trim(), e.institucion.trim()].filter(Boolean).join(' | '),
        [e.inicio, e.estado === 'En curso' ? 'Actualidad' : e.fin].filter(v => v !== null).join(' - '),
        e.estado,
      ].filter(Boolean).join('\n')).join('\n\n'),
    };
  }
  private validarTrayectoria(): void {
    const anioValido = (n: number | null) => n !== null && Number.isInteger(n) && n >= 1900 && n <= this.anioActual;
    for (const [i, e] of this.empleosCompletados.entries()) {
      if (!e.empresa.trim() || !e.puesto.trim() || !anioValido(e.inicio) || (!e.actual && !anioValido(e.fin)))
        throw new Error(`Empleo ${i + 1}: completa empresa, puesto y años, o marca que trabajas ahí actualmente.`);
      if (!e.actual && e.fin! < e.inicio!) throw new Error(`Empleo ${i + 1}: el año de término no puede ser anterior al de inicio.`);
    }
    for (const [i, e] of this.estudiosCompletados.entries()) {
      if (!e.nivel || !e.institucion.trim() || !e.estado || !anioValido(e.inicio) || (e.estado !== 'En curso' && !anioValido(e.fin)))
        throw new Error(`Estudio ${i + 1}: completa nivel, institución, estado y años.`);
      if (e.estado !== 'En curso' && e.fin! < e.inicio!) throw new Error(`Estudio ${i + 1}: el año de término no puede ser anterior al de inicio.`);
    }
    if (this.cvCompleto.experiencia_laboral.length > 6000 || this.cvCompleto.formacion.length > 3000)
      throw new Error('Resume tu trayectoria: se permiten hasta 6,000 caracteres de experiencia y 3,000 de estudios.');
  }
  generandoPDF = signal(false);
  errorPDF = signal('');
  mensajePDF = signal('');

  async calcular(): Promise<void> {
    if (this.cargando()) return;
    this.cargando.set(true);
    this.error.set('');
    this.banda = null;
    this.perfil = null;
    try {
      const { banda, perfil } = await estimarPerfil(this.datos);
      this.banda = banda;
      this.perfil = perfil;
      this.cv.puesto_objetivo = perfil.payload.input.datos_usuario.puesto;
      this.cv.resumen = perfil.resumen;
      this.cv.licencia = this.datos.licencia === 'Sin licencia' ? '' : this.datos.licencia;
      this.cv.certificaciones = perfil.payload.input.datos_usuario.certificaciones.join('\n');
      this.mensajePDF.set('');
      this.errorPDF.set('');
      this.error.set('');
      this.irA(2);
    } catch (error) {
      this.error.set(error instanceof Error ? error.message : 'No se pudo generar el perfil.');
    } finally { this.cargando.set(false); }
  }

  alternarCertificacion(cert: string, checked: boolean): void {
    this.datos.certificaciones = checked
      ? [...this.datos.certificaciones, cert] : this.datos.certificaciones.filter(c => c !== cert);
    this.error.set('');
  }

  irA(paso: number): void {
    if (paso !== 1 && (!this.banda || !this.perfil)) return;
    this.paso.set(paso);
    // El foco acompaña el cambio de vista para usuarios de teclado y lectores de pantalla.
    setTimeout(() => document.getElementById('titulo-paso')?.focus());
  }

  mxn(valor: number): string {
    return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(valor);
  }

  get posicionMediana(): number {
    return this.banda && this.banda.p90 > this.banda.p10
      ? (this.banda.p50 - this.banda.p10) / (this.banda.p90 - this.banda.p10) * 100 : 50;
  }
  async descargarPDF(): Promise<void> {
    if (this.generandoPDF()) return;
    this.generandoPDF.set(true);
    this.errorPDF.set('');
    this.mensajePDF.set('');
    try {
      this.validarTrayectoria();
      const blob = await solicitarPDF(this.cvCompleto);
      const url = URL.createObjectURL(blob);
      const enlace = document.createElement('a');
      enlace.href = url;
      enlace.download = 'BlueWage_CV.pdf';
      enlace.click();
      setTimeout(() => URL.revokeObjectURL(url), 10000);
      this.mensajePDF.set('CV descargado. Ya puedes compartir el PDF por correo o WhatsApp.');
    } catch (error) {
      this.errorPDF.set(error instanceof Error ? error.message : 'No se pudo generar el PDF.');
    } finally { this.generandoPDF.set(false); }
  }

  descargar(tipo: 'json'): void {
    if (!this.perfil) return;
    const contenido = JSON.stringify(this.perfil.payload, null, 2);
    const archivo = 'bluewage_payload.json';
    const blob = new Blob([contenido], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const enlace = document.createElement('a');
    enlace.href = url;
    enlace.download = archivo;
    enlace.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
}
