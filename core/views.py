from datetime import date
from collections import Counter

from django.shortcuts import render
from django.http import FileResponse, HttpResponse
from .models import Phase, Activity
from .forms import (
    ProjectForm,
    ActivityDeclarationFormSet,
    CustomActivityDeclarationFormSet,
)
from .services import (
    build_declaration,
    build_declaration_pdf,
    get_results,
    get_results_html,
    serialize_declaration,
)

SPANISH_MONTHS = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)


def _document_summary(declarations, phases):
    support_order = ("ALTO", "MEDIO", "BAJO")
    support_counts = Counter(
        declaration["ai_support_level"] for declaration in declarations
    )
    total = len(declarations)
    support_distribution = [
        {
            "name": level,
            "count": support_counts.get(level, 0),
            "percentage": round(support_counts.get(level, 0) * 100 / total)
            if total else 0,
        }
        for level in support_order
    ]
    used_phase_names = {
        getattr(declaration["xp_phase"], "name", declaration["xp_phase"])
        for declaration in declarations
    }
    tool_names = {
        declaration["ai_tool_name"]
        for declaration in declarations
        if declaration.get("ai_tool_name")
    }
    predominant_support = max(
        support_order,
        key=lambda level: support_counts.get(level, 0),
        default="—",
    )

    return {
        "activity_count": total,
        "phase_count": len(used_phase_names),
        "tool_count": len(tool_names),
        "predominant_support": predominant_support,
        "support_distribution": support_distribution,
        "phase_timeline": [
            {"name": phase.name, "used": phase.name in used_phase_names}
            for phase in phases
        ],
    }


def home(request):
    phases = Phase.objects.prefetch_related("activities").all()
    activities = Activity.objects.all()

    activity_formset = ActivityDeclarationFormSet(
        initial=[{} for _ in activities]
    )

    activity_forms = list(zip(activities, activity_formset))
    custom_activity_formsets = {
        phase.id: CustomActivityDeclarationFormSet(
            prefix=f"custom_phase_{phase.id}",
        )
        for phase in phases
    }
    phase_custom_forms = [
        (phase, custom_activity_formsets[phase.id]) for phase in phases
    ]

    return render(
        request,
        'index.html',
        {
            "project_form": ProjectForm(),
            "activity_formset": activity_formset,
            "activity_forms": activity_forms,
            "phases": phases,
            "custom_activity_formsets": custom_activity_formsets,
            "phase_custom_forms": phase_custom_forms,
            "single_ai_tool_enabled": False,
            "current_date": _spanish_date(),
        },
    )    


def _spanish_date():
    today = date.today()
    return f"{today.day} de {SPANISH_MONTHS[today.month - 1]} de {today.year}"

def create_declaration(request):
    phases = Phase.objects.prefetch_related("activities").all()
    activities = Activity.objects.all()
    single_ai_tool_enabled = (
        request.method == "POST"
        and request.POST.get("use_single_ai_tool") == "on"
    )
    custom_activity_formsets = {
        phase.id: CustomActivityDeclarationFormSet(
            request.POST or None,
            prefix=f"custom_phase_{phase.id}",
        )
        for phase in phases
    }
    phase_custom_forms = [
        (phase, custom_activity_formsets[phase.id]) for phase in phases
    ]

    project_form = ProjectForm(request.POST or None)
    global_tool_fields = (
        "global_ai_tool_name",
        "global_type_ai_tool",
        "global_ai_model_name",
    )
    for field_name in global_tool_fields:
        project_form.fields[field_name].required = single_ai_tool_enabled

    selected_activity_ids = set()
    selected_custom_activity_ids = set()
    if request.method == "POST":
        selected_activity_ids = (
            set(request.POST.getlist("added_activities"))
            & set(request.POST.getlist("activities"))
        )
        selected_custom_activity_ids = (
            set(request.POST.getlist("added_custom_activities"))
            & set(request.POST.getlist("custom_activities"))
        )

    activity_formset = ActivityDeclarationFormSet(
        request.POST or None,
        initial=[{} for _ in activities],
    )

    activity_forms = list(zip(activities, activity_formset))

    if single_ai_tool_enabled:
        tool_fields = (
            "ai_tool_name",
            "type_ai_tool",
            "ai_model_name",
            "ai_model_version",
        )
        for activity_form in activity_formset:
            for field_name in tool_fields:
                activity_form.fields[field_name].required = False
        for custom_formset in custom_activity_formsets.values():
            for custom_form in custom_formset:
                for field_name in tool_fields:
                    custom_form.fields[field_name].required = False

    for activity, activity_form in activity_forms:
        activity_form.empty_permitted = str(activity.id) not in (
            selected_activity_ids
        )

    for phase in phases:
        custom_formset = custom_activity_formsets[phase.id]
        for index, custom_form in enumerate(custom_formset):
            custom_form.empty_permitted = (
                f"{phase.id}-{index}" not in selected_custom_activity_ids
            )

    declarations = []
    result_text = ""
    result_html = ""
    form_errors = None

    if request.method == "POST":
        project_is_valid = project_form.is_valid()
        formset_is_valid = activity_formset.is_valid()
        custom_formsets_are_valid = all(
            formset.is_valid()
            for formset in custom_activity_formsets.values()
        )
        if not selected_activity_ids and not selected_custom_activity_ids:
            project_form.add_error(
                None,
                "Agrega al menos una actividad asistida con IAG antes de generar la declaración.",
            )
        use_single_ai_tool = project_form.cleaned_data.get(
            "use_single_ai_tool",
            False,
        )

        if use_single_ai_tool:
            global_tool_fields = (
                "global_ai_tool_name",
                "global_type_ai_tool",
                "global_ai_model_name",
            )
            for field_name in global_tool_fields:
                if not project_form.cleaned_data.get(field_name):
                    project_form.add_error(
                        field_name,
                        "Este campo es obligatorio cuando se utiliza una sola herramienta.",
                    )
        else:
            for activity, activity_form in activity_forms:
                if str(activity.id) in selected_activity_ids:
                    for field_name in (
                        "ai_tool_name",
                        "type_ai_tool",
                        "ai_model_name",
                    ):
                        if not activity_form.cleaned_data.get(field_name):
                            activity_form.add_error(
                                field_name,
                                "Este campo es obligatorio para la actividad seleccionada.",
                            )

            for phase in phases:
                custom_formset = custom_activity_formsets[phase.id]
                for index, custom_form in enumerate(custom_formset):
                    if f"{phase.id}-{index}" in selected_custom_activity_ids:
                        for field_name in (
                            "ai_tool_name",
                            "type_ai_tool",
                            "ai_model_name",
                        ):
                            if not custom_form.cleaned_data.get(field_name):
                                custom_form.add_error(
                                    field_name,
                                    "Este campo es obligatorio para la actividad seleccionada.",
                                )

        project_is_valid = project_is_valid and not project_form.errors
        formset_is_valid = formset_is_valid and all(
            not activity_form.errors
            for activity, activity_form in activity_forms
        )
        custom_formsets_are_valid = custom_formsets_are_valid and all(
            not formset.errors
            for formset in custom_activity_formsets.values()
        )

        if project_is_valid and formset_is_valid and custom_formsets_are_valid:
            global_tool_data = None
            if use_single_ai_tool:
                global_tool_data = {
                    "ai_tool_name": project_form.cleaned_data["global_ai_tool_name"],
                    "type_ai_tool": project_form.cleaned_data["global_type_ai_tool"],
                    "ai_model_name": project_form.cleaned_data["global_ai_model_name"],
                    "ai_model_version": project_form.cleaned_data["global_ai_model_version"],
                }

            for activity, activity_form in activity_forms:
                if str(activity.id) not in selected_activity_ids:
                    continue

                declaration = build_declaration (
                    project_form,
                    activity,
                    activity_form,
                    tool_data=global_tool_data,
                )
                declaration["activity_key"] = f"activities:{activity.id}"

                declarations.append(declaration)

            for phase in phases:
                custom_formset = custom_activity_formsets[phase.id]
                for index, custom_form in enumerate(custom_formset):
                    if f"{phase.id}-{index}" not in selected_custom_activity_ids:
                        continue

                    declaration = build_declaration(
                        project_form,
                        custom_form.cleaned_data["activity_name"],
                        custom_form,
                        phase=phase,
                        tool_data=global_tool_data,
                    )
                    declaration["activity_key"] = (
                        f"custom_activities:{phase.id}-{index}"
                    )
                    declarations.append(declaration)

            declarations.sort(
                key=lambda declaration: declaration["xp_phase"].order
            )
            result_text = get_results(declarations)
            result_html = get_results_html(declarations)
            request.session["declarations"] = [
                serialize_declaration(declaration)
                for declaration in declarations
            ]
        else:
            request.session.pop("declarations", None)
            form_errors = {
                "project_errors": project_form.errors,
                "formset_errors": activity_formset.errors,
                "custom_formset_errors": {
                    phase_id: formset.errors
                    for phase_id, formset in custom_activity_formsets.items()
                },
            }

    return render(
        request,
        "index.html",
        {
            "project_form": project_form,
            "activity_formset": activity_formset,
            "activity_forms": activity_forms,
            "phases": phases,
            "declarations": declarations,
            "result_text": result_text,
            "result_html": result_html,
            "current_date": _spanish_date(),
            "document_summary": _document_summary(declarations, phases),
            "form_errors": form_errors,
            "selected_activity_ids": selected_activity_ids,
            "selected_custom_activity_ids": selected_custom_activity_ids,
            "custom_activity_formsets": custom_activity_formsets,
            "phase_custom_forms": phase_custom_forms,
            "single_ai_tool_enabled": single_ai_tool_enabled,
        },
    )

def download_declaration_pdf(request):
    declarations = request.session.get("declarations")

    if not declarations:
        return HttpResponse(
            "No hay declaraciones para descargar.",
            status=400,
        )

    pdf_buffer = build_declaration_pdf(declarations)

    return FileResponse(
        pdf_buffer,
        as_attachment=True,
        filename="declaraciones-xp.pdf"
    )