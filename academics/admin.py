from django.contrib import admin
from .models import Subject, Result, GradingScale


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(GradingScale)
class GradingScaleAdmin(admin.ModelAdmin):
    list_display = ("grade", "min_score")
    ordering = ("-min_score",)


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ("student", "subject", "term", "year", "score", "recorded_by")
    list_filter = ("term", "year", "subject")
    search_fields = ("student__admission_number", "student__first_name", "student__last_name")