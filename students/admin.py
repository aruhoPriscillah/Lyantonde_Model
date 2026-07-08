from django.contrib import admin
from .models import Student, SchoolClass


@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ("name", "class_teacher")


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("admission_number", "full_name", "school_class", "boarding_status", "guardian_phone", "is_active")
    list_filter = ("school_class", "gender", "boarding_status", "is_active")
    search_fields = ("admission_number", "first_name", "last_name")
    readonly_fields = ("admission_number",)

