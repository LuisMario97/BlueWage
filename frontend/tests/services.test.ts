import { test } from 'node:test';
import assert from 'node:assert/strict';
import { DATOS_INICIALES, crearPerfilAPI, estimarPerfil } from '../src/app/services/bluewage.ts';

test('Envía seis campos exactos y convierte DC-3 sin sumar cursos', () => {
  assert.deepEqual(crearPerfilAPI(DATOS_INICIALES), {
    puesto: 'Conductores de carga', region: 'CDMX/Edomex', experiencia_anios: 5,
    horas_semana: 48, licencia: 'Sin licencia', tiene_dc3: 0,
  });
  assert.equal(crearPerfilAPI({...DATOS_INICIALES, certificaciones: ['Ninguna']}).tiene_dc3, 0);
  assert.equal(crearPerfilAPI({...DATOS_INICIALES, certificaciones: ['Seguridad e Higiene', 'Manejo Defensivo']}).tiene_dc3, 1);
  assert.equal(crearPerfilAPI({...DATOS_INICIALES, horas: 72}).horas_semana, 72);
});

test('Rechaza entradas fuera de dominio y certificaciones contradictorias', () => {
  for (const cambio of [{horas: 73}, {experiencia: -1}, {puesto: 'Chofer Reparto Local'},
    {region: 'Querétaro/Bajío'}, {licencia: 'Federal Tipo B'},
    {certificaciones: ['Ninguna', 'Seguridad e Higiene']}]) {
    assert.throws(() => crearPerfilAPI({...DATOS_INICIALES, ...cambio}));
  }
});

test('Usa salarios y textos del servidor; rechaza respuesta inválida sin fallback', async t => {
  const respuesta = {
    salario: {piso_p10: 10000.15, mediana_p50: 12500.55, techo_p90: 15000.95},
    moneda: 'MXN', periodicidad: 'mensual', cruce_corregido: false,
    orientacion: {modo: 'gemini', competencias_clave: ['Área 1', 'Área 2', 'Área 3'], extracto_cv: 'Resumen del servidor', recomendaciones: ['Uno', 'Dos', 'Tres']},
  };
  t.mock.method(globalThis, 'fetch', async () => new Response(JSON.stringify(respuesta)));
  const resultado = await estimarPerfil(DATOS_INICIALES);
  assert.equal(resultado.banda.p50, 12500.55);
  assert.equal(resultado.perfil.resumen, 'Resumen del servidor');
  assert.match(resultado.perfil.cv_markdown, /Resumen del servidor/);
  assert.deepEqual(resultado.perfil.recomendaciones.map(r => r.accion), ['Uno','Dos','Tres']);
  respuesta.salario.piso_p10 = 20000;
  await assert.rejects(estimarPerfil(DATOS_INICIALES), /respuesta inválida/);
});

test('Informa desconexión y rechazo HTTP', async t => {
  const mock = t.mock.method(globalThis, 'fetch', async () => { throw new TypeError('Failed to fetch'); });
  await assert.rejects(estimarPerfil(DATOS_INICIALES), /servidor local/);
  mock.mock.mockImplementation(async () => new Response('{}', {status: 422}));
  await assert.rejects(estimarPerfil(DATOS_INICIALES), /rechazó/);
});
