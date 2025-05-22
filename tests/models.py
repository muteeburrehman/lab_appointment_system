from django.db import models

class Test(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    duration_minutes= models.PositiveIntegerField(default=30)

    def __str__(self):
        return self.name
