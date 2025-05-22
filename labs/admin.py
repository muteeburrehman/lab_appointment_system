from django.contrib import admin
from .models import Laboratory, LabTest

@admin.register(Laboratory)
class LaboratoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'address', 'created_at')
    search_fields = ('name', 'owner__username')

@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = ('lab', 'test', 'price', 'is_active')
    list_filter = ('lab',)