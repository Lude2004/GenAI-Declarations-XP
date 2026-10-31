from django.core.management.base import BaseCommand

from core.models import Activity, Phase


class Command(BaseCommand):
    def handle(self, *args, **options):
        catalog = {
            "Planificación": [
                "Gestión de los objetivos y alcance del proyecto.",
                "Gestión de historias de usuario.",
                "Gestión de criterios de aceptación.",
                "Priorización de historias de usuario.",
                "Estimación del esfuerzo (cantidad de trabajo/tiempo) de las historias de usuario.",
                "Planificación de entregas.",
                "Planificación de iteraciones.",
            ],
            "Diseño": [
                "Modelo de dominio preliminar.",
                "Gestión de tarjetas CRC (Clase-Responsabilidad-Colaboradores).",
                "Exploración de problemas mediante Spike Solutions.",
                "Diseño de prototipos.",
            ],
            "Desarrollo": [
                "Codificación colaborativa (autocompletado).",
                "Refactorización.",
                "Integración continua.",
                "Aplicación de estándares de codificación.",
            ],
            "Pruebas": [
                "Diseño y/o ejecución de pruebas unitarias.",
                "Diseño y/o ejecución de pruebas de integración.",
                "Diseño de pruebas de aceptación.",
            ],
        }

        for phase_order, (phase_name, activities) in enumerate(
            catalog.items(), start=1
        ):
            phase, _ = Phase.objects.update_or_create(
                name=phase_name,
                defaults={"order": phase_order},
            )

            for activity_order, activity_name in enumerate(activities, start=1):
                Activity.objects.update_or_create(
                    phase=phase,
                    name=activity_name,
                    defaults={"order": activity_order},
                )

        self.stdout.write(
            self.style.SUCCESS("Catálogo de XP cargado correctamente.")
        )