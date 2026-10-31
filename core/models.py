from django.db import models

class Phase(models.Model):
    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveSmallIntegerField(unique=True)

    class Meta:
        ordering = ["order"]
        verbose_name = "Fase"
        verbose_name_plural = "Fases"

    def __str__(self):
        return self.name


class Activity(models.Model): 
    phase = models.ForeignKey(
        Phase,
        on_delete=models.CASCADE,
        related_name="activities"
    )

    name = models.CharField(max_length=200)
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["phase__order", "order"]
        constraints = [
            models.UniqueConstraint(
                fields=["phase", "name"],
                name="unique_activity_per_phase",
            ),
            models.UniqueConstraint(
                fields=["phase", "order"],
                name="unique_activity_order_per_phase"
            ),
        ]
        verbose_name = "Actividad"
        verbose_name_plural = "Actividades"

    def __str__(self):
        return self.name