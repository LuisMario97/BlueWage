import asyncio
import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from backend.llm import PerfilGenerado, generar_perfil_con_llm, perfil_base
from backend.llm import _consultar_gemini
from backend.main import EXAMPLE

BANDA = {"piso_p10": 18336.43, "mediana_p50": 22197.51, "techo_p90": 25615.21}


class LlmTest(unittest.IsolatedAsyncioTestCase):
    async def test_esquema_sdk_y_alternativa_por_saturacion(self):
        saturado = RuntimeError("saturación de prueba")
        saturado.code = 503
        generar = AsyncMock(side_effect=[saturado, SimpleNamespace(text='{}')])
        contexto = AsyncMock()
        contexto.__aenter__.return_value = SimpleNamespace(models=SimpleNamespace(generate_content=generar))
        with patch("google.genai.Client", return_value=SimpleNamespace(aio=contexto)), patch.dict("os.environ", {"GEMINI_MODEL": "gemini-2.5-flash", "GEMINI_FALLBACK_MODEL": "gemini-3.5-flash-lite"}):
            self.assertEqual(await _consultar_gemini("clave-ficticia", "{}"), '{}')
        self.assertEqual(generar.await_count, 2)
        self.assertEqual(generar.call_args_list[0].kwargs['model'], 'gemini-3.8-flash')
        self.assertEqual(generar.call_args_list[1].kwargs['model'], 'gemini-3.5-flash-lite')
        esquema = generar.call_args.kwargs['config'].response_schema
        self.assertNotIn('additionalProperties', esquema)
        self.assertEqual(esquema['properties']['plan_upskilling']['minItems'], 3)

    async def test_sin_clave_no_llama_api(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": ""}), patch("backend.llm._consultar_gemini", new_callable=AsyncMock) as api:
            resultado = await generar_perfil_con_llm(EXAMPLE, BANDA)
        api.assert_not_awaited()
        self.assertEqual(resultado.pop("modo"), "fallback")
        PerfilGenerado.model_validate({k: v for k, v in resultado.items() if k != "motivo_fallback"})
        self.assertIn("5 años", resultado["resumen_cv"])

    async def test_exito_y_payload_limitado(self):
        contenido = perfil_base(EXAMPLE).model_dump_json()
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-no-real"}), patch("backend.llm._consultar_gemini", new_callable=AsyncMock, return_value=contenido) as api:
            resultado = await generar_perfil_con_llm({**EXAMPLE, "email": "no-compartir"}, BANDA)
        self.assertEqual(resultado["modo"], "gemini")
        self.assertNotIn("email", json.loads(api.call_args.args[1])["trabajador"])

    async def test_fallos_y_json_invalido(self):
        for fallo in (RuntimeError("cuota"), TimeoutError(), "", "{}", "no-json"):
            with self.subTest(fallo=repr(fallo)), patch.dict("os.environ", {"GEMINI_API_KEY": "test-no-real"}):
                api = AsyncMock(side_effect=fallo) if isinstance(fallo, Exception) else AsyncMock(return_value=fallo)
                with patch("backend.llm._consultar_gemini", api):
                    resultado = await generar_perfil_con_llm(EXAMPLE, BANDA)
                self.assertEqual(resultado.pop("modo"), "fallback")
                PerfilGenerado.model_validate({k: v for k, v in resultado.items() if k != "motivo_fallback"})

    async def test_timeout_total(self):
        async def lento(*args):
            await asyncio.sleep(1)
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-no-real"}), patch("backend.llm.TIMEOUT_SECONDS", 0.01), patch("backend.llm._consultar_gemini", lento):
            self.assertEqual((await generar_perfil_con_llm(EXAMPLE, BANDA))["modo"], "fallback")

    async def test_cantidad_incorrecta_no_llega_al_cliente(self):
        for campo, valores in (("plan_upskilling", ["Uno", "Dos"]), ("competencias_clave", ["Uno"]), ("plan_upskilling", ["Igual"] * 3)):
            contenido = perfil_base(EXAMPLE).model_dump()
            contenido[campo] = valores
            with patch.dict("os.environ", {"GEMINI_API_KEY": "test-no-real"}), patch("backend.llm._consultar_gemini", new_callable=AsyncMock, return_value=json.dumps(contenido)):
                self.assertEqual((await generar_perfil_con_llm(EXAMPLE, BANDA))["modo"], "fallback")

    def test_cero_experiencia_y_cuatro_roles(self):
        for puesto in ("Conductores de carga", "Personal de control de almacén", "Operadores de maquinaria para mover mercancías", "Personal de carga y descarga"):
            perfil = perfil_base({**EXAMPLE, "puesto": puesto, "experiencia_anios": 0, "tiene_dc3": 0})
            self.assertIn("sin experiencia", perfil.resumen_cv)
            self.assertEqual(len(perfil.plan_upskilling), 3)
