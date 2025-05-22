from django.db import models
from django.conf import settings

class Laboratory(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    address = models.TextField()
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='labs')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class LabTest(models.Model):
    lab = models.ForeignKey(Laboratory, on_delete= models.CASCADE, related_name='lab_tests')
    test = models.ForeignKey('tests.Test', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)