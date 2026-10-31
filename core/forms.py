from django import forms
from django.forms import formset_factory

AI_TOOL_CHOICES = [
    ("CHAT IA", "CHAT IA"),
    ("CLI IA", "CLI IA"),
    ("IDE IA", "IDE IA"),
]

class ProjectForm(forms.Form):
    project_name = forms.CharField(
        max_length=150,
        label="Nombre del proyecto de software",
    )
    use_single_ai_tool = forms.BooleanField(
        required=False,
        label="Utilicé una sola herramienta de IAG para todas las actividades",
    )
    global_ai_tool_name = forms.CharField(
        max_length=20,
        required=False,
        label="Nombre de la herramienta",
    )
    global_type_ai_tool = forms.ChoiceField(
        choices=AI_TOOL_CHOICES,
        required=False,
        widget=forms.RadioSelect,
        label="Tipo de herramienta",
    )
    global_ai_model_name = forms.CharField(
        max_length=20,
        required=False,
        label="Nombre del modelo de IA",
    )
    global_ai_model_version = forms.CharField(
        max_length=10,
        required=False,
        label="Versión",
    )

class ActivityDeclarationForm(forms.Form):
    ai_tool_name = forms.CharField(
        max_length=20,
        required=False,
        label="Nombre",
    )

    type_ai_tool = forms.ChoiceField(
        choices=AI_TOOL_CHOICES,
        required=False,
        widget=forms.RadioSelect,
        label="Tipo de herramienta",
    )

    ai_model_name = forms.CharField(
        max_length=20,
        required=False,
        label="Modelo de IA",
    )

    ai_model_version = forms.CharField(
        max_length=10,
        required=False,
        label="Versión",
    )

    input_data = forms.CharField(
        max_length=100,
        label="Datos de entrada compartidos",
        required=False,
    )

    description_process = forms.CharField(
        max_length=200,
        label="Descripción de uso",
    )

    ai_support_level = forms.ChoiceField(
        choices=[
            ("BAJO", "BAJO"),
            ("MEDIO", "MEDIO"),
            ("ALTO", "ALTO"),
        ],
        widget=forms.RadioSelect,
        label="Nivel de apoyo de la herramienta de IAG",
    )

    human_verification = forms.CharField(
        max_length=200,
        label="Proceso de validación humana",
        required=False,
    )


class CustomActivityDeclarationForm(ActivityDeclarationForm):
    activity_name = forms.CharField(
        max_length=200,
        label="Nombre de la actividad realizada",
    )


ActivityDeclarationFormSet = formset_factory(
    ActivityDeclarationForm,
    extra=0,
)

CustomActivityDeclarationFormSet = formset_factory(
    CustomActivityDeclarationForm,
    extra=0,
)