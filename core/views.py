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
    serialize_declaration,
)

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
        },
    )    

def create_declaration(request):
    phases = Phase.objects.prefetch_related("activities").all()
    activities = Activity.objects.all()
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
    single_ai_tool_enabled = (
        request.method == "POST"
        and request.POST.get("use_single_ai_tool") == "on"
    )
    selected_activity_ids = (
        set(request.POST.getlist("activities"))
        if request.method == "POST"
        else set()
    )
    selected_custom_activity_ids = (
        set(request.POST.getlist("custom_activities"))
        if request.method == "POST"
        else set()
    )

    activity_formset = ActivityDeclarationFormSet(
        request.POST or None,
        initial=[{} for _ in activities],
    )

    activity_forms = list(zip(activities, activity_formset))

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
    form_errors = None

    if request.method == "POST":
        project_is_valid = project_form.is_valid()
        formset_is_valid = activity_formset.is_valid()
        custom_formsets_are_valid = all(
            formset.is_valid()
            for formset in custom_activity_formsets.values()
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
                "global_ai_model_version",
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
                        "ai_model_version",
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
                            "ai_model_version",
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

                declarations.append(declaration)

            for phase in phases:
                custom_formset = custom_activity_formsets[phase.id]
                for index, custom_form in enumerate(custom_formset):
                    if f"{phase.id}-{index}" not in selected_custom_activity_ids:
                        continue

                    declarations.append(
                        build_declaration(
                            project_form,
                            custom_form.cleaned_data["activity_name"],
                            custom_form,
                            phase=phase,
                            tool_data=global_tool_data,
                        )
                    )

            result_text = get_results(declarations)
            request.session["declarations"] = [
                serialize_declaration(declaration)
                for declaration in declarations
            ]
        else:
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