from django.contrib import admin
from .models import Subject, Result


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ("student", "subject", "term", "year", "score", "recorded_by")
    list_filter = ("term", "year", "subject")
    search_fields = ("student__admission_number", "student__first_name", "student__last_name")
