"""Servicios mock sin dependencias externas. Importes ficticios, no datos de mercado."""

PUESTOS = {
    "Chofer Carga Pesada / 5ta rueda": 22000,
    "Chofer Reparto Local": 14000,
    "Montacarguista": 12500,
    "Auxiliar de Almacén/Bodega": 9500,
}
REGIONES = {
    "CDMX/Edomex": 1.08, "Nuevo León": 1.16, "Jalisco": 1.05,
    "Querétaro/Bajío": 1.09, "Frontera Norte": 1.20, "Resto del país": 1.0,
}
LICENCIAS = [
    "Sin licencia", "Estatal Tipo Chofer", "Federal Tipo B", "Federal Tipo C",
    "Federal Tipo E / Materiales Peligrosos",
]
CERTIFICACIONES = [
    "Manejo de Montacargas Contrabalanceado", "Seguridad e Higiene",
    "Manejo Defensivo", "Maniobras de Carga y Descarga", "Ninguna",
]


def validar_datos(datos):
    """Valida el contrato también cuando se llama fuera de la interfaz."""
    for campo, opciones in (("puesto", PUESTOS), ("region", REGIONES),
                             ("licencia", LICENCIAS)):
        if datos.get(campo) not in opciones:
            raise ValueError(f"Valor inválido para {campo}.")
    for campo, minimo, maximo in (("experiencia", 0, 30), ("horas", 20, 70)):
        valor = datos.get(campo)
        if type(valor) is not int or not minimo <= valor <= maximo:
            raise ValueError(f"{campo} debe ser un entero entre {minimo} y {maximo}.")
    certs = datos.get("certificaciones")
    if not isinstance(certs, list) or any(c not in CERTIFICACIONES for c in certs):
        raise ValueError("Certificaciones inválidas.")
    if "Ninguna" in certs and len(certs) > 1:
        raise ValueError('Quita "Ninguna" si seleccionas alguna certificación.')
    return {**datos, "certificaciones": list(dict.fromkeys(c for c in certs if c != "Ninguna"))}


def predecir_banda_salarial(datos_usuario):
    """Mock determinista de cuantiles; reemplazar por inferencia del modelo real.

    No es una regresión entrenada ni un cálculo legal de nómina/horas extra.
    Base mensual ficticia para 48 horas; experiencia con rendimiento decreciente.
    """
    d = validar_datos(datos_usuario)
    experiencia = 1 + min(d["experiencia"], 15) * .018 + max(d["experiencia"] - 15, 0) * .006
    licencia = (LICENCIAS.index(d["licencia"]) * .025
                if d["puesto"].startswith("Chofer") else 0)
    certs = len(d["certificaciones"])
    central = (PUESTOS[d["puesto"]] * REGIONES[d["region"]] * experiencia
               * (1 + licencia + certs * .025) * d["horas"] / 48)
    redondear = lambda valor: int(round(valor / 100) * 100)
    return {
        "p10": redondear(central * .80), "p50": redondear(central),
        "p90": redondear(central * 1.28), "moneda": "MXN",
        "periodicidad": "mensual", "tipo": "bruto", "es_simulacion": True,
        "version": "mock-1.0",
    }


def generar_cv_y_recomendaciones(datos_usuario, sueldo_estimado):
    """Devuelve contenido mock y un payload JSON serializable para un LLM.

    Sustituir solo la generación mock por una llamada al proveedor y validar
    su respuesta contra payload['output_schema']. No se realizan llamadas aquí.
    """
    d = validar_datos(datos_usuario)
    certs = d["certificaciones"]
    experiencia = (f'{d["experiencia"]} años de experiencia práctica en el rol'
                   if d["experiencia"] else "Perfil de ingreso, sin experiencia práctica declarada en el rol")
    resumen = (f'{d["puesto"]} en {d["region"]}. {experiencia}. '
               f'Jornada habitual declarada: {d["horas"]} horas semanales.')
    certificaciones = "\n".join(f"- {c}" for c in certs) or "- Sin certificaciones DC-3 declaradas."
    markdown = (f'# Ficha técnica · {d["puesto"]}\n\n{resumen}\n\n'
                f'## Licencia declarada\n{d["licencia"]}\n\n'
                f'## Certificaciones DC-3 declaradas\n{certificaciones}\n\n'
                'Perfil elaborado con información declarada por la persona; credenciales no verificadas.')
    recomendaciones = []
    if d["puesto"].startswith("Chofer"):
        curso = "Manejo Defensivo"
        if d["licencia"] == "Sin licencia":
            recomendaciones.append({"titulo": "Preparar el trámite de licencia",
                "accion": "Identifica el vehículo y tipo de servicio de tus vacantes objetivo y consulta la categoría y requisitos con la autoridad emisora.",
                "objetivo": "Acreditar la habilitación que requiere el puesto."})
    elif d["puesto"] == "Montacarguista":
        curso = "Manejo de Montacargas Contrabalanceado"
    else:
        curso = "Maniobras de Carga y Descarga"
    for certificacion in dict.fromkeys([curso, "Seguridad e Higiene"]):
        if certificacion not in certs:
            recomendaciones.append({"titulo": f"Capacitarte en {certificacion}",
                "accion": "Solicita a tu empleador capacitación con evaluación práctica y consulta la emisión de la constancia DC-3 correspondiente.",
                "objetivo": "Documentar una competencia relevante para tu rol."})
    recomendaciones.extend([
        {"titulo": "Documentar resultados operativos",
         "accion": "Prepara tres ejemplos verificables: entregas a tiempo, exactitud de inventario o maniobras realizadas, según tu puesto.",
         "objetivo": "Respaldar tu experiencia en entrevistas y negociaciones."},
        {"titulo": "Practicar herramientas de la operación",
         "accion": "Identifica el sistema usado en tus vacantes objetivo y realiza una práctica de captura de entregas o movimientos de inventario.",
         "objetivo": "Ampliar las habilidades demostrables de tu perfil."},
    ])
    recomendaciones = recomendaciones[:3]
    schema = {
        "type": "object", "additionalProperties": False,
        "properties": {
            "resumen": {"type": "string"}, "cv_markdown": {"type": "string"},
            "recomendaciones": {"type": "array", "minItems": 2, "maxItems": 3,
                "items": {"type": "object", "additionalProperties": False,
                    "properties": {k: {"type": "string"} for k in ("titulo", "accion", "objetivo")},
                    "required": ["titulo", "accion", "objetivo"]}},
        }, "required": ["resumen", "cv_markdown", "recomendaciones"],
    }
    payload = {
        "version": "1.0", "locale": "es-MX", "task": "generar_perfil_operativo",
        "instructions": "Redacta un CV con hechos declarados, sin inventar credenciales ni empleos. Propón 2-3 acciones relevantes, sin garantizar incrementos salariales. No presentes los cuantiles simulados como datos de mercado.",
        "input": {"datos_usuario": d, "sueldo_estimado": sueldo_estimado},
        "output_schema": schema,
    }
    return {"resumen": resumen, "cv_markdown": markdown,
            "recomendaciones": recomendaciones, "payload": payload}
