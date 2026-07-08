from django.urls import path
from . import views

app_name = "academics"

urlpatterns = [
    path("", views.teacher_dashboard, name="teacher_dashboard"),
    path("results/add/", views.add_result, name="add_result"),
    path("results/", views.class_results, name="class_results"),
    path("export/<str:filetype>/", views.export_results, name="export_results"),
]
