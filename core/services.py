from datetime import date
from collections import Counter
from html import escape

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

SPANISH_MONTHS = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)

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


def _format_usage_declaration(declaration):
    description = declaration["description_process"]
    human_verification = declaration["human_verification"]
    support_level = declaration["ai_support_level"]
    input_data = (declaration.get("input_data") or "").strip()

    if input_data:
        return (
            f"Se proporcionó {input_data} para {description}, "
            f"con verificación humana {human_verification}, "
            f"y nivel de apoyo {support_level}."
        )

    return (
        f"Para {description}, con verificación humana "
        f"{human_verification}, y nivel de apoyo {support_level}."
    )


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
        _format_usage_declaration(declaration),
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
        content.extend([f"Fase: {phase_name.upper()}", ""])
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

def get_results_html(declarations) -> str:
    lines = get_results(declarations).splitlines()
    formatted_lines = []
    for line in lines:
        escaped_line = escape(line)
        if line.startswith("Fase: "):
            escaped_line = f"<strong>{escaped_line}</strong>"
        formatted_lines.append(f"<div>{escaped_line or '&nbsp;'}</div>")
    return "".join(formatted_lines)

def build_declaration_pdf(declarations):
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="Declaración de uso de IAG",
    )
    styles = getSampleStyleSheet()
    text_color = colors.HexColor("#1d2638")
    panel_color = colors.HexColor("#202b58")
    blue_color = colors.HexColor("#3154c5")
    light_panel = colors.HexColor("#f4f6fb")

    def paragraph_style(name, **kwargs):
        return ParagraphStyle(name, parent=styles["Normal"], **kwargs)

    body_style = paragraph_style(
        "DocumentBody",
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=text_color,
        alignment=TA_JUSTIFY,
    )
    small_style = paragraph_style(
        "DocumentSmall",
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=text_color,
    )
    heading_style = paragraph_style(
        "DocumentHeading",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=text_color,
    )
    white_heading_style = paragraph_style(
        "DocumentWhiteHeading",
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=17,
        textColor=colors.white,
    )
    white_small_style = paragraph_style(
        "DocumentWhiteSmall",
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#dce5ff"),
    )

    def pdf_text(value):
        return escape(str(value or "")).replace("\n", "<br/>")

    def tag(value):
        return Paragraph(
            f"<font color='#ffffff'><b>{pdf_text(value)}</b></font>",
            small_style,
        )

    phase_colors = {
        "Planificación": colors.HexColor("#3154c5"),
        "Diseño": colors.HexColor("#9333ea"),
        "Codificación": colors.HexColor("#16a34a"),
        "Pruebas": colors.HexColor("#f97316"),
    }
    phase_groups = {}
    for declaration in declarations:
        phase_groups.setdefault(_phase_name(declaration), []).append(declaration)

    phase_count = len(phase_groups)
    tool_count = len({
        declaration.get("ai_tool_name")
        for declaration in declarations
        if declaration.get("ai_tool_name")
    })
    support_counts = Counter(
        declaration.get("ai_support_level") for declaration in declarations
    )
    predominant_support = max(
        ("ALTO", "MEDIO", "BAJO"),
        key=lambda level: support_counts.get(level, 0),
        default="—",
    )
    story = []

    header = Table(
        [[
            Paragraph(
                "Declaración de uso de Inteligencia Artificial Generativa · "
                "Extreme Programming (XP)",
                white_small_style,
            ),
            Paragraph(pdf_text(declarations[0]["project_name"]), white_heading_style),
            Paragraph(
                f"{date.today().day} de "
                f"{SPANISH_MONTHS[date.today().month - 1]} de "
                f"{date.today().year}",
                white_small_style,
            ),
        ]],
        colWidths=[document.width],
    )
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), blue_color),
        ("LEFTPADDING", (0, 0), (-1, -1), 18),
        ("RIGHTPADDING", (0, 0), (-1, -1), 18),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ]))
    story.extend([header, Spacer(1, 14)])

    metrics = [
        ("Actividades", len(declarations)),
        ("Fases", phase_count),
        ("Herramientas", tool_count),
        ("Apoyo predominante", predominant_support),
    ]
    metric_cells = [
        [
            Paragraph(
                f"<font color='#ffffff' size='16'><b>{pdf_text(value)}</b></font>"
                f"<br/><font color='#ffffff' size='7'>{label}</font>",
                ParagraphStyle(
                    f"Metric{index}",
                    parent=small_style,
                    alignment=TA_CENTER,
                    textColor=colors.white,
                ),
            )
        ]
        for index, (label, value) in enumerate(metrics)
    ]
    metrics_table = Table([metric_cells], colWidths=[document.width / 4] * 4)
    metrics_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), panel_color),
        ("BOX", (0, 0), (-1, -1), 0, panel_color),
        ("INNERGRID", (0, 0), (-1, -1), 4, colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    story.extend([
        Paragraph("Resumen del uso de IAG en el proyecto", heading_style),
        metrics_table,
        Spacer(1, 14),
        Paragraph(
            "El/los autor(es) declara(n) que las herramientas de inteligencia "
            "artificial generativa especificadas en este documento fueron utilizadas "
            "como apoyo en las tareas indicadas de la metodología XP durante el "
            "desarrollo del proyecto.",
            body_style,
        ),
        Spacer(1, 12),
    ])

    if declarations[0].get("use_single_ai_tool"):
        tool_content = Table([[
            Paragraph(
                f"<b>{pdf_text(declarations[0]['ai_tool_name'])}</b>",
                small_style,
            ),
            tag(declarations[0]["type_ai_tool"]),
            tag(
                f"{declarations[0]['ai_model_name']} "
                f"{declarations[0].get('ai_model_version', '')}".strip()
            ),
        ]], colWidths=[document.width * 0.45, document.width * 0.25, document.width * 0.30])
        tool_content.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), panel_color),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#334276")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.extend([
            Paragraph("Herramienta utilizada", heading_style),
            tool_content,
            Spacer(1, 14),
        ])

    for phase_name, phase_declarations in phase_groups.items():
        phase_color = phase_colors.get(phase_name, blue_color)
        phase_heading = Table([[
            Paragraph(pdf_text(phase_name), heading_style)
        ]], colWidths=[document.width])
        phase_heading.setStyle(TableStyle([
            ("LINEBEFORE", (0, 0), (0, 0), 4, phase_color),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.extend([phase_heading, Spacer(1, 3)])

        for declaration in phase_declarations:
            activity_text = (
                f"En la actividad <b>{pdf_text(_activity_name(declaration))}</b> "
                "se utilizó:"
            )
            tool_text = (
                f"<b>{pdf_text(declaration['ai_tool_name'])}</b> · "
                f"{pdf_text(declaration['type_ai_tool'])} · modelo "
                f"{pdf_text(declaration['ai_model_name'])} "
                f"{pdf_text(declaration.get('ai_model_version', ''))}"
            )
            usage_text = (
                f"{'Se proporcionó ' + pdf_text(declaration['input_data']) + '. ' if declaration.get('input_data') else ''}"
                f"La verificación humana consistió en {pdf_text(declaration['human_verification'])}. "
                f"El nivel de apoyo de la IAG fue "
                f"<b>{pdf_text(declaration['ai_support_level'])}</b>."
            )
            activity = Table([
                [Paragraph(activity_text, body_style)],
                [Paragraph(tool_text, small_style)],
                [Paragraph(usage_text, body_style)],
            ], colWidths=[document.width])
            activity.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), light_panel),
                ("LINEBEFORE", (0, 0), (0, 0), 2, colors.HexColor("#9aa1ae")),
                ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#d9dcd5")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.extend([activity, Spacer(1, 7)])

    story.extend([
        Spacer(1, 8),
        Paragraph("Responsabilidad", heading_style),
        Table([[
            Paragraph(
                "Todas las salidas generadas por IA fueron revisadas, validadas y, "
                "cuando fue necesario, modificadas por los miembros del equipo para "
                "asegurar su calidad, precisión y alineación con los objetivos del "
                "proyecto. La responsabilidad del contenido final recae íntegramente "
                "en el/los autor/es. Las herramientas de IA generativa no figuran "
                "como autores y no asumen responsabilidad alguna por los resultados "
                "finales.",
                body_style,
            )
        ]], colWidths=[document.width], style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#dcfce7")),
            ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#86efac")),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ])),
    ])

    document.build(story)
    buffer.seek(0)
    return buffer