import { test, expect } from '@playwright/test';

// Orientación controlada para probar CV sin consumir cuota de Gemini.
test.beforeEach(async ({page}) => {
  await page.route('**/api/estimar-perfil', route => route.fulfill({json: {
    salario: {piso_p10:18336.43, mediana_p50:22197.51, techo_p90:25615.21},
    moneda:'MXN', periodicidad:'mensual', cruce_corregido:false,
    orientacion:{modo:'gemini', extracto_cv:'Conductora con experiencia declarada en distribución de mercancías y operaciones de transporte.',
      competencias_clave:['Validar conducción segura','Validar inspección','Validar sujeción'],
      recomendaciones:['Practica conducción defensiva.','Revisa procedimientos de inspección.','Documenta logros verificables.']},
  }}));
});

test('CV: datos personales, revisión, PDF real y conservación al navegar', async ({page}) => {
  await page.goto('/');
  await page.getByRole('checkbox', {name:'Seguridad e Higiene', exact:true}).check();
  await page.getByRole('button', {name:'Explorar mi banda salarial'}).click();
  await expect(page.locator('.kpi.featured .amount')).toHaveText('$22,197.51');
  await page.getByRole('button', {name:'Crear mi CV en PDF'}).click();
  await page.getByLabel('Nombre completo').fill('María López García');
  await page.getByLabel('Teléfono / WhatsApp').fill('+52 55 0000 0000');
  await page.getByLabel('Correo electrónico').fill('maria@example.com');
  await page.getByLabel('Ciudad y estado').fill('Monterrey, Nuevo León');
  const empleo = page.getByRole('group', {name:'Empleo 1', exact:true});
  await empleo.getByLabel('Empresa', {exact:true}).fill('Empresa de ejemplo');
  await empleo.getByLabel('Puesto desempeñado').fill('Conductora');
  await empleo.getByLabel('Año de inicio').fill('2021');
  await empleo.getByLabel('Actualmente trabajo aquí').check();
  await empleo.getByLabel('Funciones y logros').fill('Distribución de mercancías.');
  const estudio = page.getByRole('group', {name:'Estudio 1', exact:true});
  await estudio.getByLabel('Nivel de escolaridad').selectOption('Bachillerato / Preparatoria');
  await estudio.getByLabel('Escuela o institución').fill('Escuela de ejemplo');
  await estudio.getByLabel('Estado de los estudios').selectOption('Concluido');
  await estudio.getByLabel('Año de inicio').fill('2015');
  await estudio.getByLabel('Año de término').fill('2018');
  await page.getByRole('button', {name:'Agregar otro empleo'}).click();
  const segundo = page.getByRole('group', {name:'Empleo 2', exact:true});
  await segundo.getByLabel('Empresa', {exact:true}).fill('Transportes de ejemplo');
  await segundo.getByLabel('Puesto desempeñado').fill('Auxiliar');
  await segundo.getByLabel('Año de inicio').fill('2018');
  await segundo.getByLabel('Año de término').fill('2020');
  await page.getByRole('button', {name:'Agregar otro estudio'}).click();
  const otro = page.getByRole('group', {name:'Estudio 2', exact:true});
  await otro.getByLabel('Nivel de escolaridad').selectOption('Carrera técnica');
  await otro.getByLabel('Escuela o institución').fill('Instituto técnico');
  await otro.getByLabel('Estado de los estudios').selectOption('En curso');
  await otro.getByLabel('Año de inicio').fill('2025');
  await page.getByLabel('Habilidades que dominas', {exact:true}).fill('Registro de entregas');
  await expect(page.locator('.cv-preview')).toContainText('María López García');
  await expect(page.locator('.cv-preview')).not.toContainText('Validar conducción');
  const respuesta = page.waitForResponse('**/api/cv/pdf');
  const download = page.waitForEvent('download');
  await page.getByRole('button', {name:'Descargar CV en PDF',exact:true}).click();
  const api = await respuesta;
  expect(api.status()).toBe(200);
  expect(api.headers()['content-type']).toContain('application/pdf');
  expect(api.request().postDataJSON().nombre).toBe('María López García');
  expect(api.request().postDataJSON().experiencia_laboral).toContain('Auxiliar | Transportes de ejemplo\n2018 - 2020');
  expect(api.request().postDataJSON().experiencia_laboral).toContain('2021 - Actualidad');
  expect(api.request().postDataJSON().formacion).toContain('Instituto técnico\n2025 - Actualidad\nEn curso');
  expect(api.request().postDataJSON()).not.toHaveProperty('salario');
  const archivo = await download;
  expect(archivo.suggestedFilename()).toBe('BlueWage_CV.pdf');
  await archivo.saveAs('test-results/cv-descargado.pdf');
  await expect(page.getByRole('status')).toContainText('CV descargado');
  await page.getByRole('button', {name:'Ver banda salarial'}).click();
  await page.getByRole('button', {name:'Crear mi CV en PDF'}).click();
  await expect(page.getByLabel('Nombre completo')).toHaveValue('María López García');
  await expect(segundo.getByLabel('Empresa', {exact:true})).toHaveValue('Transportes de ejemplo');
  await page.getByRole('button', {name:'Eliminar empleo 1', exact:true}).click();
  await expect(page.getByRole('group', {name:'Empleo 1', exact:true}).getByLabel('Empresa', {exact:true})).toHaveValue('Transportes de ejemplo');
  await page.getByRole('button', {name:'Eliminar estudio 1', exact:true}).click();
  await expect(page.locator('.cv-preview')).not.toContainText('Escuela de ejemplo');
  await expect(page.locator('.cv-preview')).toContainText('Instituto técnico');
});

test('CV: cuestionario incompleto y fechas invertidas impiden descargar', async ({page}) => {
  await page.goto('/');
  await page.getByRole('button', {name:'Explorar mi banda salarial'}).click();
  await page.getByRole('button', {name:'Crear mi CV en PDF'}).click();
  await page.getByLabel('Nombre completo').fill('Ana Prueba');
  await page.getByLabel('Teléfono / WhatsApp').fill('5551234567');
  const empleo = page.getByRole('group', {name:'Empleo 1', exact:true});
  await empleo.getByLabel('Empresa', {exact:true}).fill('Empresa de ejemplo');
  await page.getByRole('button', {name:'Descargar CV en PDF',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('Empleo 1: completa');
  await empleo.getByLabel('Puesto desempeñado').fill('Auxiliar');
  await empleo.getByLabel('Año de inicio').fill('2024');
  await empleo.getByLabel('Año de término').fill('2020');
  await page.getByRole('button', {name:'Descargar CV en PDF',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('no puede ser anterior');
  await empleo.getByLabel('Actualmente trabajo aquí').check();
  const download = page.waitForEvent('download');
  await page.getByRole('button', {name:'Descargar CV en PDF',exact:true}).click();
  await download;
});

test('CV: errores de validación y red permiten reintentar sin perder datos', async ({page}) => {
  await page.goto('/');
  await page.getByRole('button', {name:'Explorar mi banda salarial'}).click();
  await page.getByRole('button', {name:'Crear mi CV en PDF'}).click();
  await page.getByLabel('Nombre completo').fill('Ana Prueba');
  await page.getByLabel('Teléfono / WhatsApp').fill('abc1234');
  await page.getByRole('button', {name:'Descargar CV en PDF',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('Revisa los datos');
  await page.getByLabel('Teléfono / WhatsApp').fill('5551234567');
  await page.route('**/api/cv/pdf', route => route.abort());
  await page.getByRole('button', {name:'Descargar CV en PDF',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('conexión');
  await expect(page.getByLabel('Nombre completo')).toHaveValue('Ana Prueba');
  await page.unroute('**/api/cv/pdf');
  const download = page.waitForEvent('download');
  await page.getByRole('button', {name:'Descargar CV en PDF',exact:true}).click();
  await download;
  await expect(page.getByRole('status')).toContainText('CV descargado');
});

test('Editor de CV móvil sin desbordamiento', async ({page}) => {
  await page.setViewportSize({width:390,height:844});
  await page.goto('/');
  await page.getByRole('button', {name:'Explorar mi banda salarial'}).click();
  await page.getByRole('button', {name:'Crear mi CV en PDF'}).click();
  await page.getByLabel('Nombre completo').fill('María López García');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({path:'test-results/cv-editor-mobile.png',fullPage:true});
});
