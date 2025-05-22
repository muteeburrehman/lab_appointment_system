from django.contrib import admin
from .models import Test

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration_minutes')
    search_fields = ('name',)
