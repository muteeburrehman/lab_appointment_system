from django.db import models
from django.conf import settings
from labs.models import LabTest

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('booked', 'Booked'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.CASCADE)
    lab_test = models.ForeignKey(LabTest, on_delete= models.CASCADE)
    appointment_time = models.DateTimeField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='booked')
    created_at = models.DateTimeField(auto_now_add=True)