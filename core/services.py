from datetime import date
import textwrap

from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def build_declaration(
    project_form,
    activity,
    activity_form,
    phase=None,
    tool_data=None,
):
    tool_data = tool_data or {
        "ai_tool_name": activity_form.cleaned_data["ai_tool_name"],
        "type_ai_tool": activity_form.cleaned_data["type_ai_tool"],
        "ai_model_name": activity_form.cleaned_data["ai_model_name"],
        "ai_model_version": activity_form.cleaned_data["ai_model_version"],
    }
    return {
        "project_name": project_form.cleaned_data["project_name"],
        "use_single_ai_tool": project_form.cleaned_data.get(
            "use_single_ai_tool",
            False,
        ),
        "xp_phase": phase or activity.phase,
        "activity": activity,
        **tool_data,
        "input_data": activity_form.cleaned_data["input_data"],
        "description_process": activity_form.cleaned_data["description_process"],
        "ai_support_level": activity_form.cleaned_data["ai_support_level"],
        "human_verification": activity_form.cleaned_data["human_verification"],
    }


def serialize_declaration(declaration):
    return {
        **declaration,
        "xp_phase": declaration["xp_phase"].name,
        "activity": getattr(
            declaration["activity"],
            "name",
            declaration["activity"],
        ),
    }


def _phase_name(declaration):
    return getattr(declaration["xp_phase"], "name", declaration["xp_phase"])


def _activity_name(declaration):
    return getattr(declaration["activity"], "name", declaration["activity"])


def format_activity_declaration(declaration) -> list[str]:
    content = [f"Actividad: {_activity_name(declaration)}", ""]
    if not declaration.get("use_single_ai_tool"):
        content.extend([
            "Herramienta de IAG",
            f"- Nombre: {declaration['ai_tool_name']}",
            f"- Tipo: {declaration['type_ai_tool']}",
            (
                f"- Modelo: {declaration['ai_model_name']} "
                f"{declaration['ai_model_version']}"
            ),
            "",
        ])
    content.extend([
        "Proceso del uso de la IAG",
        f"- Datos de entrada: {declaration['input_data']}",
        (
            "- Descripción: "
            f"{declaration['description_process']}"
        ),
        "",
        "Intervención de la herramienta",
        f"- Nivel de apoyo: {declaration['ai_support_level']}",
        "",
        "Verificación humana",
        f"- {declaration['human_verification']}",
    ])
    return content

def format_grouped_declarations(declarations) -> list[str]:
    content = []
    phases = {}
    phase_order = []
    for declaration in declarations:
        phase_name = _phase_name(declaration)
        if phase_name not in phases:
            phases[phase_name] = []
            phase_order.append(phase_name)
        phases[phase_name].append(declaration)

    for phase_index, phase_name in enumerate(phase_order):
        if phase_index:
            content.extend(["", "-" * 60, ""])
        content.extend([f"FASE: {phase_name.upper()}", ""])
        for declaration in phases[phase_name]:
            content.extend(format_activity_declaration(declaration))
            content.append("")
    return content

def get_results(declarations) -> str:
    if not declarations:
        return ""

    data = declarations[0]
    content = []

    # Heading
    content.append("Declaración de Uso de Inteligencia Artificial Generativa")
    content.append("")
    formatted_date = date.today().strftime("%d de %B de %Y")
    content.append(f"Fecha: {formatted_date}")
    content.append("")

    # Introduction
    content.append(
        "El/los autor/es declara/n que las herramientas de inteligencia artificial"
        "generativa especificadas en este documento fueron utilizadas como apoyo en las "
        f"tareas indicadas de la metodología XP durante el desarrollo del proyecto {data['project_name']}."
    )
    content.append("")

    # Declaration
    if data.get("use_single_ai_tool"):
        content.extend([
            "Herramienta de IAG utilizada en todas las actividades",
            f"- Nombre: {data['ai_tool_name']}",
            f"- Tipo: {data['type_ai_tool']}",
            (
                f"- Modelo: {data['ai_model_name']} "
                f"{data['ai_model_version']}"
            ),
            "",
        ])
    content.extend(format_grouped_declarations(declarations))


    content.append(
        "Todas las salidas generadas por IA fueron revisadas, validadas y, cuando fue necesario, "
        "modificadas por los miembros del equipo para asegurar su calidad, precisión y "
        "alineación con los objetivos del proyecto."
    )
    content.append("")

    content.append("La responsabilidad del contenido final recae íntegramente en el/los autor/es.")
    content.append("")

    content.append(            
        "Las herramientas de IA generativa no figuran como autores y no asumen responsabilidad "
        "alguna por los resultados finales."
    )
    content.append("")

    return "\n".join(content)

def build_declaration_pdf(declarations):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)

    width, height = letter
    left_margin = 50
    top_margin = height - 50
    bottom_margin = 50
    y = top_margin
    text = pdf.beginText(left_margin, y)
    text.setFont("Helvetica", 10)
    text.setLeading(14)

    def write_line(line):
        nonlocal text, y
        text.textLine(line)
        y -= 14
        if y < bottom_margin:
            pdf.drawText(text)
            pdf.showPage()
            y = top_margin
            text = pdf.beginText(left_margin, y)
            text.setFont("Helvetica", 10)
            text.setLeading(14)

    write_line("Declaración de Uso de Inteligencia Artificial Generativa")
    write_line("")

    write_line(f"Proyecto: {declarations[0]['project_name']}")
    if declarations[0].get("use_single_ai_tool"):
        write_line("Herramienta de IAG utilizada en todas las actividades")
        write_line(f"- Nombre: {declarations[0]['ai_tool_name']}")
        write_line(f"- Tipo: {declarations[0]['type_ai_tool']}")
        write_line(
            f"- Modelo: {declarations[0]['ai_model_name']} "
            f"{declarations[0]['ai_model_version']}"
        )
        write_line("")

    for line in format_grouped_declarations(declarations):
        wrapped_lines = textwrap.wrap(
            line,
            width=95,
            break_long_words=True,
            break_on_hyphens=False,
        ) or [""]
        for wrapped_line in wrapped_lines:
            write_line(wrapped_line)

    pdf.drawText(text)

    pdf.save()
    buffer.seek(0)

    return buffer