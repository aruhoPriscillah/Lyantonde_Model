from django.urls import path
from . import views

app_name = "fees"

urlpatterns = [
    path("", views.bursar_dashboard, name="bursar_dashboard"),
    path("payment/new/", views.record_payment, name="record_payment"),
    path("structure/", views.manage_fee_structure, name="manage_fee_structure"),
    path("structure/<int:pk>/edit/", views.edit_fee_structure, name="edit_fee_structure"),
    path("students/<int:pk>/", views.student_fee_detail, name="student_fee_detail"),
    path("payment/<int:pk>/edit/", views.edit_payment, name="edit_payment"),
    path("payment/<int:pk>/delete/", views.delete_payment, name="delete_payment"),
    path("defaulters/", views.defaulters_list, name="defaulters_list"),
    path("export/<str:filetype>/", views.export_fees_report, name="export_fees_report"),
]
