from django.contrib import admin
from .models import FeeStructure, Payment


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ("school_class", "term", "year", "boarding_status", "amount")
    list_filter = ("term", "year", "boarding_status")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("student", "term", "year", "amount", "method", "date_paid", "received_by")
    list_filter = ("term", "year", "method")
    search_fields = ("student__admission_number", "student__first_name", "student__last_name")
