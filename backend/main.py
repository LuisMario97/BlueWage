"""API local. Ejecutar desde la raíz: python -m uvicorn backend.main:app."""

from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path
from typing import Literal

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from backend.cv_pdf import DatosCV, generar_cv_pdf
from pydantic import BaseModel, ConfigDict, Field
from starlette.concurrency import run_in_threadpool
from backend.llm import generar_perfil_con_llm, modelo_gemini

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = Path(__file__).resolve().parent / 'models' / 'bluewage_pipeline_cuantil.joblib'
FEATURES = ["puesto", "region", "experiencia_anios", "horas_semana", "licencia", "tiene_dc3"]
EXAMPLE = {
    "puesto": "Conductores de carga", "region": "Nuevo León",
    "experiencia_anios": 5, "horas_semana": 48,
    "licencia": "Federal E", "tiene_dc3": 1,
}


class Perfil(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False,
                              json_schema_extra={"examples": [EXAMPLE]})
    puesto: Literal["Conductores de carga", "Personal de control de almacén",
                    "Operadores de maquinaria para mover mercancías", "Personal de carga y descarga"]
    region: Literal["CDMX/Edomex", "Nuevo León", "Jalisco", "Bajío", "Frontera Norte", "Resto del país"]
    experiencia_anios: float = Field(ge=0, le=30)
    horas_semana: float = Field(ge=20, le=72)
    licencia: Literal["Federal B", "Federal C", "Federal E", "Estatal Chofer", "Sin licencia"]
    tiene_dc3: Literal[0, 1]


class Banda(BaseModel):
    piso_p10: float
    mediana_p50: float
    techo_p90: float


class Orientacion(BaseModel):
    modo: Literal["gemini", "fallback"]
    motivo_fallback: str | None = None
    extracto_cv: str
    recomendaciones: list[str] = Field(min_length=3, max_length=3)
    resumen_cv: str
    competencias_clave: list[str] = Field(min_length=3, max_length=4)
    plan_upskilling: list[str] = Field(min_length=3, max_length=3)


class Estimacion(BaseModel):
    salario: Banda
    moneda: Literal["MXN"] = "MXN"
    periodicidad: Literal["mensual"] = "mensual"
    cruce_corregido: bool
    orientacion: Orientacion | None


def cargar_pipeline(ruta: Path) -> dict:
    if not ruta.is_file():
        raise FileNotFoundError(
            f"No se encontró el modelo en {ruta}. Copia bluewage_pipeline_cuantil.joblib "
            "a backend/models/ o configura BLUEWAGE_MODEL_PATH."
        )
    # Solo artefactos propios/confiables: joblib deserializa objetos Python.
    pipeline = joblib.load(ruta)
    requeridas = {"preprocessor", "model_p10", "model_p50", "model_p90"}
    if not isinstance(pipeline, dict) or not requeridas.issubset(pipeline):
        raise ValueError("El archivo no tiene el formato exportado en la Celda 6.")
    columnas = pipeline.get("feature_names")
    if columnas is None:
        columnas = getattr(pipeline["preprocessor"], "feature_names_in_", FEATURES)
    columnas = list(columnas)
    if len(columnas) != len(FEATURES) or set(columnas) != set(FEATURES):
        raise ValueError("feature_names debe contener las seis columnas originales.")
    pipeline["feature_names"] = columnas
    return pipeline


def inferir(pipeline: dict, perfil: Perfil) -> tuple[Banda, bool]:
    entrada = pd.DataFrame([perfil.model_dump()])[pipeline["feature_names"]]
    matriz = pipeline["preprocessor"].transform(entrada)
    crudos = np.array([pipeline[f"model_{q}"].predict(matriz)[0]
                       for q in ("p10", "p50", "p90")], dtype=float)
    if not np.isfinite(crudos).all() or (crudos <= 0).any():
        raise ValueError("El modelo devolvió salarios no válidos.")
    corregidos = np.maximum.accumulate(crudos)
    banda = Banda(**dict(zip(
        ("piso_p10", "mediana_p50", "techo_p90"),
        [round(float(x), 2) for x in corregidos],
    )))
    return banda, bool(np.any(crudos != corregidos))


def crear_app(ruta_modelo: Path | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        ruta = ruta_modelo or Path(os.environ.get(
            "BLUEWAGE_MODEL_PATH", str(MODEL_PATH)))
        app.state.pipeline = cargar_pipeline(ruta)
        yield
        del app.state.pipeline

    app = FastAPI(title="BlueWage — API local", version="1.0.0", lifespan=lifespan)
    # Puertos arbitrarios de interfaces servidas en loopback; sin credenciales.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origen.strip().rstrip('/') for origen in
                       os.environ.get('FRONTEND_ORIGINS', '').split(',') if origen.strip()],
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?",
        allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["*"],
    )

    @app.get("/health")
    def health():
        return {"status": "ok", "modelo_cargado": True,
                "gemini_clave_configurada": bool(os.environ.get("GEMINI_API_KEY", "").strip()),
                "gemini_modelo": modelo_gemini()}

    @app.post("/api/estimar-perfil", response_model=Estimacion)
    async def estimar(perfil: Perfil, request: Request, incluir_orientacion: bool = True):
        try:
            banda, corregido = await run_in_threadpool(inferir, request.app.state.pipeline, perfil)
        except Exception as exc:
            logging.exception("Fallo de inferencia BlueWage")
            raise HTTPException(status_code=500, detail="Error al ejecutar el modelo; revisa la consola del servidor.") from exc
        orientacion = None
        if incluir_orientacion:
            generado = await generar_perfil_con_llm(perfil.model_dump(), banda.model_dump())
            orientacion = Orientacion(
                **generado,
                # Alias para conservar el contrato de la interfaz existente.
                extracto_cv=generado["resumen_cv"],
                recomendaciones=generado["plan_upskilling"],
            )
        return Estimacion(salario=banda, cruce_corregido=corregido, orientacion=orientacion)

    @app.post("/api/cv/pdf", response_class=Response,
              responses={200: {"content": {"application/pdf": {}}, "description": "CV en PDF"}})
    def descargar_cv(datos: DatosCV):
        return Response(content=generar_cv_pdf(datos), media_type="application/pdf",
                        headers={"Content-Disposition": 'attachment; filename="BlueWage_CV.pdf"',
                                 "Cache-Control": "no-store"})

    return app


app = crear_app()
