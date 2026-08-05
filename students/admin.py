from django.contrib import admin
from .models import Requirement, Student, SchoolClass, StudentRequirement


@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ("name", "class_teacher")


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("admission_number", "full_name", "school_class", "boarding_status", "guardian_phone", "is_active")
    list_filter = ("school_class", "gender", "boarding_status", "is_active")
    search_fields = ("admission_number", "first_name", "last_name")
    readonly_fields = ("admission_number",)


@admin.register(Requirement)
class RequirementAdmin(admin.ModelAdmin):
    list_display = ("name", "class_group", "scholar_type", "is_active")
    list_filter = ("scholar_type", "class_group", "is_active")


@admin.register(StudentRequirement)
class StudentRequirementAdmin(admin.ModelAdmin):
    list_display = ("student", "requirement", "term", "year", "brought", "brought_on", "recorded_by")
    list_filter = ("term", "year", "brought", "requirement__class_group")
