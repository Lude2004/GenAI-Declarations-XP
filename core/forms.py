from django import forms
from django.forms import formset_factory

AI_TOOL_CHOICES = [
    ("CHAT IA", "CHAT IA"),
    ("CLI IA", "CLI IA"),
    ("IDE IA", "IDE IA"),
]

class ProjectForm(forms.Form):
    required_css_class = "required"
    label_suffix = ""

    project_name = forms.CharField(
        max_length=150,
        label="Nombre",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Ej. Sistema de gestión de inventario",
            }
        )
    )

    use_single_ai_tool = forms.BooleanField(
        required=False,
        label="Utilicé una sola herramienta de IAG para todas las actividades",
    )

    global_ai_tool_name = forms.CharField(
        max_length=20,
        label="Nombre",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Ej. ChatGPT",
            }
        )
    )

    global_type_ai_tool = forms.ChoiceField(
        choices=AI_TOOL_CHOICES,
        widget=forms.RadioSelect,
        label="Tipo de herramienta",
    )

    global_ai_model_name = forms.CharField(
        max_length=20,
        label="Modelo de IA",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Ej. GPT 6.1",
            }
        )
    )

    global_ai_model_version = forms.CharField(
        max_length=10,
        label="Versión",
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Ej. Sol",
            }
        )
    )

class ActivityDeclarationForm(forms.Form):
    required_css_class = "required"
    label_suffix = ""

    ai_tool_name = forms.CharField(
        max_length=20,
        label="Nombre",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Ej. ChatGPT",
            }
        )
    )

    type_ai_tool = forms.ChoiceField(
        choices=AI_TOOL_CHOICES,
        widget=forms.RadioSelect,
        label="Tipo de herramienta",
    )

    ai_model_name = forms.CharField(
        max_length=20,
        label="Modelo de IA",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Ej. GPT 6.1",
            }
        )
    )

    ai_model_version = forms.CharField(
        max_length=10,
        label="Versión",
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Ej. Sol",
            }
        )
    )

    input_data = forms.CharField(
        max_length=100,
        required=False,
        label="Datos de entrada compartidos",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Ej. Documentación del proyecto",
            }
        )
    )

    description_process = forms.CharField(
        max_length=200,
        label="Descripción de uso",
        widget=forms.Textarea(
            attrs={
                "placeholder": "Ej. Generar código de la interfaz de usuario",
                "rows": 3,
            }
        )
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
        widget=forms.Textarea(
            attrs={
                "placeholder": "Ej. Revisión del código y modificaciones por parte del equipo de desarrollo",
                "rows": 3,
            }
        )
    )


class CustomActivityDeclarationForm(ActivityDeclarationForm):
    required_css_class = "required"
    label_suffix = ""

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