from django.urls import path
from . import views

app_name = "students"

urlpatterns = [
    path("", views.headteacher_dashboard, name="headteacher_dashboard"),
    path("register/", views.register_student, name="register_student"),
    path("classes/", views.manage_classes, name="manage_classes"),
    path("<int:pk>/", views.student_detail, name="student_detail"),
    path("export/<str:filetype>/", views.export_students, name="export_students"),
]
