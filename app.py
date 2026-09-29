"""Interfaz BlueWage. Ejecutar: python -m streamlit run app.py."""
import json
from pathlib import Path

import streamlit as st

from services import (CERTIFICACIONES, LICENCIAS, PUESTOS, REGIONES,
                      generar_cv_y_recomendaciones, predecir_banda_salarial)

st.set_page_config(page_title="BlueWage · Tu experiencia tiene valor", page_icon="🔷", layout="wide")
st.markdown(f'<style>{(Path(__file__).parent / "assets/styles.css").read_text(encoding="utf-8")}</style>', unsafe_allow_html=True)


def ir_a(paso):
    st.session_state.paso = paso


def mxn(valor):
    return f"${valor:,.0f}"


st.session_state.setdefault("paso", 1)
st.session_state.setdefault("datos", {
    "puesto": next(iter(PUESTOS)), "region": next(iter(REGIONES)),
    "experiencia": 5, "licencia": "Sin licencia", "certificaciones": [], "horas": 48,
})
paso = st.session_state.paso
st.markdown('<div class="brand"><span class="brand-mark">///</span> BlueWage</div>', unsafe_allow_html=True)
st.markdown('''<div class="hero"><div class="tag">Logística y transporte · México</div>
<h1>Tu experiencia tiene valor.<br>Descubre tu siguiente paso.</h1>
<p>Transparencia salarial y perfilamiento técnico para el sector operativo de logística y transporte</p></div>''', unsafe_allow_html=True)
st.caption("DEMO INTERACTIVA · Estimaciones simuladas · Sin registro")
st.markdown('<div class="steps">' + ''.join(
    f'<div class="step {"active" if paso == n else ""}"><b>0{n}</b>{titulo}</div>'
    for n, titulo in enumerate(["Tu experiencia", "Tu banda salarial", "Tu perfil técnico"], 1)
) + '</div>', unsafe_allow_html=True)

if paso == 1:
    st.subheader("Cuéntanos sobre tu trabajo")
    st.write("Seis datos para explorar tu banda salarial y construir tu ficha técnica.")
    d = st.session_state.datos
    with st.form("formulario_operador"):
        izquierda, derecha = st.columns(2, gap="large")
        with izquierda:
            puesto = st.selectbox("Puesto / oficio", list(PUESTOS), index=list(PUESTOS).index(d["puesto"]))
            experiencia = st.slider("Años de experiencia práctica en el rol", 0, 30, d["experiencia"], format="%d años")
            licencia = st.selectbox("Licencia de conducir", LICENCIAS, index=LICENCIAS.index(d["licencia"]))
        with derecha:
            region = st.selectbox("Estado / región de trabajo", list(REGIONES), index=list(REGIONES).index(d["region"]))
            horas = st.slider("Horas semanales habituales de trabajo", 20, 70, d["horas"], format="%d horas")
            certificaciones = st.multiselect("Certificaciones DC-3", CERTIFICACIONES, default=d["certificaciones"], placeholder="Selecciona tus certificaciones")
        st.caption('Selecciona solo credenciales que ya tienes. Puedes dejar las certificaciones vacías o elegir "Ninguna".')
        calcular = st.form_submit_button("Explorar mi banda salarial →", type="primary", use_container_width=True)
    if calcular:
        datos = dict(puesto=puesto, region=region, experiencia=experiencia, horas=horas,
                     licencia=licencia, certificaciones=certificaciones)
        try:
            banda = predecir_banda_salarial(datos)
            perfil = generar_cv_y_recomendaciones(datos, banda)
        except ValueError as error:
            st.error(str(error))
        else:
            st.session_state.update(datos=datos, banda=banda, perfil=perfil, paso=2)
            st.rerun()
    st.markdown('<p class="note">01 · Comparte tu experiencia &nbsp; / &nbsp; 02 · Explora el rango &nbsp; / &nbsp; 03 · Llévate tu perfil</p>', unsafe_allow_html=True)

elif paso == 2:
    d, banda = st.session_state.datos, st.session_state.banda
    st.subheader("Una referencia para tu siguiente paso")
    st.write(f'{d["puesto"]} · {d["region"]} · {d["experiencia"]} años de experiencia')
    st.caption(f'Pesos mexicanos · Ingreso mensual bruto simulado · Jornada declarada: {d["horas"]} h/semana')
    for columna, clave, titulo in zip(st.columns(3), ["p10", "p50", "p90"],
                                     ["P10 · Piso", "P50 · Mediana / justo", "P90 · Banda superior"]):
        with columna:
            st.markdown(f'<div class="kpi {"featured" if clave == "p50" else ""}"><div class="label">{titulo}</div><div class="amount">{mxn(banda[clave])}</div><div class="unit">MXN / mes · bruto</div></div>', unsafe_allow_html=True)
    posicion = 100 * (banda["p50"] - banda["p10"]) / (banda["p90"] - banda["p10"])
    st.markdown(f'''<div class="range"><b>Tu rango salarial simulado</b>
<div class="track"><span class="marker" style="left:{posicion}%"></span></div>
<div class="range-labels"><span>P10 · {mxn(banda['p10'])}</span><span>P50 · {mxn(banda['p50'])}</span><span>P90 · {mxn(banda['p90'])}</span></div></div>''', unsafe_allow_html=True)
    st.info("Estas cifras son ficticias: ilustran la salida de un modelo cuantílico. P50 representa la mediana simulada; P90 es una referencia superior, no una oferta ni un aumento garantizado por certificarse.")
    with st.expander("¿Cómo se calcula esta demo?"):
        st.write("Usamos bases ficticias por puesto, factores regionales, experiencia, licencia y certificaciones. Ajustamos proporcionalmente por horas respecto a 48 h/semana. P10 = 80% de P50 y P90 = 128% de P50, redondeados a $100. No hay un modelo entrenado ni datos de mercado conectados.")
        st.caption("No calcula impuestos, prestaciones, horas extra ni cumplimiento de mínimos legales. Un modelo real deberá aprender cada cuantil y validar su cobertura con datos representativos.")
    c1, c2 = st.columns(2)
    c1.button("← Editar mis datos", on_click=ir_a, args=(1,), use_container_width=True)
    c2.button("Crear mi ficha técnica →", type="primary", on_click=ir_a, args=(3,), use_container_width=True)

else:
    perfil = st.session_state.perfil
    st.subheader("Tu experiencia, lista para compartir")
    st.write("Una ficha clara para acompañar tu próxima postulación.")
    izquierda, derecha = st.columns([1.35, 1], gap="large")
    with izquierda:
        with st.container(border=True):
            st.markdown(perfil["cv_markdown"])
        st.download_button("↓ Descargar ficha (.md)", perfil["cv_markdown"], "BlueWage_ficha_tecnica.md", "text/markdown", use_container_width=True)
        with st.expander("Copiar para WhatsApp"):
            st.caption("Usa el icono de copiar del bloque y pega el texto en tu conversación.")
            whatsapp = perfil["cv_markdown"].replace("# Ficha técnica ·", "Ficha técnica ·").replace("## ", "")
            st.code(whatsapp, language=None, wrap_lines=True)
    with derecha:
        st.markdown("#### Acércate a tu siguiente oportunidad")
        st.caption("Acciones para fortalecer tu perfil hacia la banda superior. No garantizan alcanzar P90.")
        for i, recomendacion in enumerate(perfil["recomendaciones"], 1):
            with st.container(border=True):
                st.markdown(f'**0{i} · {recomendacion["titulo"]}**')
                st.write(recomendacion["accion"])
                st.caption(recomendacion["objetivo"])
    with st.expander("Integración de IA · payload JSON"):
        st.caption("Contrato independiente del proveedor. La demo genera el contenido localmente; no envía datos a ninguna API.")
        st.json(perfil["payload"])
        st.download_button("Descargar payload JSON", json.dumps(perfil["payload"], ensure_ascii=False, indent=2), "bluewage_payload.json", "application/json")
    c1, c2 = st.columns(2)
    c1.button("← Ver banda salarial", on_click=ir_a, args=(2,), use_container_width=True)
    c2.button("Editar mi perfil", on_click=ir_a, args=(1,), use_container_width=True)

st.markdown('<div class="footer">BLUEWAGE &nbsp; / &nbsp; Ciencia de datos aplicada al trabajo operativo &nbsp; · &nbsp; Prototipo académico</div>', unsafe_allow_html=True)
