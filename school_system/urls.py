from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from students.views import dashboard_redirect
from accounts.forms import StyledAuthenticationForm

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", dashboard_redirect, name="home"),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html", authentication_form=StyledAuthenticationForm), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
    path("headteacher/students/", include("students.urls")),
    path("bursar/fees/", include("fees.urls")),
    path("teacher/academics/", include("academics.urls")),
]
