import {test, expect} from '@playwright/test';
import type {Route} from '@playwright/test';

async function inferenciaSinProveedor(route: Route) {
  const response = await route.fetch({url: route.request().url() + '?incluir_orientacion=false'});
  const datos = await response.json();
  // Conserva los salarios reales; solo el texto usa una respuesta de prueba.
  datos.orientacion = {modo:'fallback', extracto_cv:'Perfil de prueba para validar la navegación.',
    competencias_clave:['Área A','Área B','Área C'], recomendaciones:['Acción A','Acción B','Acción C']};
  await route.fulfill({response, json:datos});
}

test('Carga, fallo de conexión y reintento sin resultados anteriores', async ({page}) => {
  await page.goto('/');
  await page.getByRole('button', {name:'Soy empleado', exact:true}).click();
  let liberar!: () => void;
  const bloqueo = new Promise<void>(resolve => { liberar = resolve; });
  await page.route('**/api/estimar-perfil', async route => { await bloqueo; await route.abort(); });
  await page.getByRole('button', {name: 'Explorar mi banda salarial'}).click();
  await expect(page.getByRole('button', {name: 'Calculando'})).toBeDisabled();
  await expect(page.getByLabel('Puesto / oficio')).toBeDisabled();
  liberar();
  await expect(page.getByRole('alert')).toContainText('servidor local');
  await expect(page.locator('.kpi')).toHaveCount(0);
  await page.unroute('**/api/estimar-perfil');
  await page.route('**/api/estimar-perfil', inferenciaSinProveedor);
  await page.getByRole('button', {name: 'Explorar mi banda salarial'}).click();
  await expect(page.locator('.kpi')).toHaveCount(3);
  await page.getByRole('button', {name: 'Editar mis datos'}).click();
  await page.route('**/api/estimar-perfil', route => route.fulfill({status: 500, body: '{}'}));
  await page.getByRole('button', {name: 'Explorar mi banda salarial'}).click();
  await expect(page.getByRole('alert')).toContainText('no pudo calcular');
  await expect(page.locator('.kpi')).toHaveCount(0);
});

test('Las cuatro ocupaciones y los límites de horas consultan la API', async ({page}) => {
  // Valida la inferencia real sin depender de latencia ni cuota del proveedor de texto.
  await page.route('**/api/estimar-perfil', inferenciaSinProveedor);
  await page.goto('/');
  await page.getByRole('button', {name:'Soy empleado', exact:true}).click();
  for (const puesto of ['Conductores de carga', 'Personal de control de almacén',
    'Operadores de maquinaria para mover mercancías', 'Personal de carga y descarga']) {
    await page.getByLabel('Puesto / oficio').selectOption(puesto);
    await page.getByLabel('Horas semanales habituales').fill('72');
    const response = page.waitForResponse(r => r.url().includes('/api/estimar-perfil') && r.request().method() === 'POST');
    await page.getByRole('button', {name:'Explorar mi banda salarial'}).click();
    expect((await response).status()).toBe(200);
    await expect(page.locator('.kpi')).toHaveCount(3);
    await page.getByRole('button', {name:'Editar mis datos'}).click();
  }
});
