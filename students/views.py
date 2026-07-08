from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from accounts.decorators import role_required
from accounts.models import User
from reportsapp.utils import export_excel, export_pdf
from .forms import StudentForm, SchoolClassForm
from .models import Student, SchoolClass


@login_required
def dashboard_redirect(request):
    """Send a logged-in user to the dashboard for their role."""
    role_urls = {
        User.Role.HEADTEACHER: "students:headteacher_dashboard",
        User.Role.BURSAR: "fees:bursar_dashboard",
        User.Role.TEACHER: "academics:teacher_dashboard",
    }
    return redirect(role_urls.get(request.user.role, "login"))


@role_required(User.Role.HEADTEACHER)
def headteacher_dashboard(request):
    students = Student.objects.select_related("school_class").filter(is_active=True)
    context = {
        "students": students,
        "total_students": students.count(),
        "total_classes": SchoolClass.objects.count(),
    }
    return render(request, "students/headteacher_dashboard.html", context)


@role_required(User.Role.HEADTEACHER)
def register_student(request):
    if request.method == "POST":
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            student.registered_by = request.user
            student.save()
            messages.success(
                request,
                f"{student.full_name} registered successfully. "
                f"Admission Number: {student.admission_number}",
            )
            return redirect("students:headteacher_dashboard")
    else:
        form = StudentForm()
    return render(request, "students/register_student.html", {"form": form})


@role_required(User.Role.HEADTEACHER)
def manage_classes(request):
    if request.method == "POST":
        form = SchoolClassForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Class saved.")
            return redirect("students:manage_classes")
    else:
        form = SchoolClassForm()
    classes = SchoolClass.objects.select_related("class_teacher").all()
    return render(request, "students/manage_classes.html", {"form": form, "classes": classes})


@role_required(User.Role.HEADTEACHER, User.Role.BURSAR, User.Role.TEACHER)
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    return render(request, "students/student_detail.html", {"student": student})


@role_required(User.Role.HEADTEACHER)
def export_students(request, filetype):
    students = Student.objects.select_related("school_class").filter(is_active=True)
    headers = ["Admission No.", "Full Name", "Gender", "Class", "Guardian", "Guardian Phone", "Date Admitted"]
    rows = [
        [
            s.admission_number,
            s.full_name,
            s.get_gender_display(),
            s.school_class.name if s.school_class else "-",
            s.guardian_name,
            s.guardian_phone,
            s.date_admitted.strftime("%Y-%m-%d"),
        ]
        for s in students
    ]
    if filetype == "pdf":
        return export_pdf("all_students", "All Registered Students", headers, rows, landscape_mode=True)
    return export_excel("all_students", "All Students", headers, rows)
