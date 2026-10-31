from django.shortcuts import render
from django.http import FileResponse, HttpResponse
from .models import Phase, Activity
from .forms import (
    ProjectForm,
    ActivityDeclarationFormSet,
    CustomActivityDeclarationFormSet,
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