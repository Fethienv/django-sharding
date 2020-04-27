from django.contrib import admin
from .models import Databases

@admin.register(Databases)
class DatabasesAdmin(admin.ModelAdmin):
    list_display = ('model_name',"number", 'count')