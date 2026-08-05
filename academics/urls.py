from django.urls import path
from . import views

app_name = "academics"

urlpatterns = [
    path("", views.teacher_dashboard, name="teacher_dashboard"),
    path("results/add/", views.add_result, name="add_result"),
    path("results/", views.class_results, name="class_results"),
    path("export/<str:filetype>/", views.export_results, name="export_results"),
    path("all-results/", views.all_results, name="all_results"),
    path("report-card/<int:pk>/", views.report_card, name="report_card"),
    path("report-card/<int:pk>/export/", views.export_report_card, name="export_report_card"),
    path("grading-scale/", views.manage_grading_scale, name="manage_grading_scale"),
    path("grading-scale/<int:pk>/edit/", views.edit_grading_scale, name="edit_grading_scale"),
    path("grading-scale/<int:pk>/delete/", views.delete_grading_scale, name="delete_grading_scale"),
    path("class-list/export/<str:filetype>/", views.export_class_list, name="export_class_list"),
    path("results/bulk-add/", views.bulk_add_results, name="bulk_add_results"),
    path("subjects/", views.manage_subjects, name="manage_subjects"),
    path("subjects/<int:pk>/delete/", views.delete_subject, name="delete_subject"),
]
