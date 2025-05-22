from django.contrib import admin
from .models import Appointment

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'lab_test', 'appointment_time', 'status')
    list_filter = ('status', 'appointment_time')
    search_fields = ('user__username', 'lab_test__test__name')

