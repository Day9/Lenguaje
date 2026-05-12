from django.db import models

class Servicio(models.Model):
    name = models.CharField(max_length=255)
    price = models.FloatField()
    quantify = models.IntegerField()
    image = models.CharField(max_length=2083)
    # Nuevos campos
    description = models.TextField(null=True, blank=True)
    specialist = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name