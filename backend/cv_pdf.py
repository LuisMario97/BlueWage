"""CV formal generado en memoria; no envía datos personales a servicios externos."""
from io import BytesIO
import re
from xml.sax.saxutils import escape

from pydantic import BaseModel, ConfigDict, Field, field_validator
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable


class DatosCV(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    nombre: str = Field(min_length=2, max_length=120)
    telefono: str = Field(min_length=7, max_length=40)
    email: str = Field(default="", max_length=160)
    ubicacion: str = Field(default="", max_length=160)
    puesto_objetivo: str = Field(min_length=2, max_length=160)
    resumen: str = Field(min_length=20, max_length=2000)
    experiencia_laboral: str = Field(default="", max_length=6000)
    formacion: str = Field(default="", max_length=3000)
    habilidades: str = Field(default="", max_length=2000)
    certificaciones: str = Field(default="", max_length=2000)
    idiomas: str = Field(default="", max_length=1000)
    licencia: str = Field(default="", max_length=160)
    enlaces: str = Field(default="", max_length=800)
    disponibilidad: str = Field(default="", max_length=800)

    @field_validator("telefono")
    @classmethod
    def validar_telefono(cls, valor):
        if not re.fullmatch(r"[+\d\s().-]+", valor) or not 7 <= len(re.sub(r"\D", "", valor)) <= 15:
            raise ValueError("Escribe un teléfono válido con 7 a 15 dígitos.")
        return valor

    @field_validator("email")
    @classmethod
    def validar_email(cls, valor):
        if valor and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", valor):
            raise ValueError("Escribe un correo válido o deja el campo vacío.")
        return valor


def generar_cv_pdf(datos: DatosCV) -> bytes:
    """Maquetación A4 con texto seleccionable, secciones omitidas si están vacías."""
    buffer = BytesIO()
    navy = colors.HexColor("#17324D")
    steel = colors.HexColor("#45576A")
    styles = {
        "nombre": ParagraphStyle("Nombre", fontName="Helvetica-Bold", fontSize=25, leading=29, textColor=navy, spaceAfter=7),
        "puesto": ParagraphStyle("Puesto", fontName="Helvetica", fontSize=12, leading=17, textColor=steel, spaceAfter=8),
        "contacto": ParagraphStyle("Contacto", fontName="Helvetica", fontSize=9, leading=14, textColor=steel, spaceAfter=5),
        "titulo": ParagraphStyle("Seccion", fontName="Helvetica-Bold", fontSize=10, leading=14, textColor=navy, spaceBefore=14, spaceAfter=6, keepWithNext=True),
        "cuerpo": ParagraphStyle("Cuerpo", fontName="Helvetica", fontSize=10, leading=15, textColor=colors.HexColor("#24313E"), spaceAfter=5, alignment=TA_LEFT, splitLongWords=True),
    }

    def parrafo(texto, estilo="cuerpo"):
        # El texto del usuario nunca se interpreta como HTML de ReportLab.
        return Paragraph(escape(texto).replace("\n", "<br/>"), styles[estilo])

    story = [parrafo(datos.nombre, "nombre"), parrafo(datos.puesto_objetivo, "puesto")]
    story.append(parrafo(" | ".join(filter(None, [datos.telefono, datos.email, datos.ubicacion])), "contacto"))
    if datos.enlaces:
        story.append(parrafo(datos.enlaces, "contacto"))
    story.extend([Spacer(1, 4 * mm), HRFlowable(width="100%", thickness=1.5, color=navy)])

    secciones = [
        ("PERFIL PROFESIONAL", datos.resumen),
        ("EXPERIENCIA LABORAL", datos.experiencia_laboral),
        ("FORMACIÓN ACADÉMICA", datos.formacion),
        ("HABILIDADES", datos.habilidades),
        ("CURSOS Y CERTIFICACIONES", datos.certificaciones),
        ("LICENCIA DE CONDUCIR", datos.licencia if datos.licencia != "Sin licencia" else ""),
        ("IDIOMAS", datos.idiomas),
        ("DISPONIBILIDAD", datos.disponibilidad),
    ]
    for titulo, contenido in secciones:
        if not contenido.strip():
            continue
        story.append(parrafo(titulo, "titulo"))
        # Cada línea puede fluir a la página siguiente sin arrastrar la sección completa.
        for linea in contenido.strip().splitlines():
            if linea.strip():
                story.append(parrafo(linea))
            else:
                story.append(Spacer(1, 3 * mm))

    def pie(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#DDE4EB"))
        canvas.line(20 * mm, 16 * mm, A4[0] - 20 * mm, 16 * mm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(steel)
        canvas.drawRightString(A4[0] - 20 * mm, 11 * mm, f"Página {doc.page}")
        canvas.restoreState()

    documento = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20 * mm,
                                 leftMargin=20 * mm, topMargin=19 * mm, bottomMargin=23 * mm,
                                 title=f"CV - {datos.nombre}", author=datos.nombre)
    documento.build(story, onFirstPage=pie, onLaterPages=pie)
    return buffer.getvalue()
