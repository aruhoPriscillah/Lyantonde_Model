from django.contrib import messages
from django.shortcuts import render, redirect
from django.core.exceptions import PermissionDenied

from accounts.decorators import role_required
from accounts.models import User
from reportsapp.utils import export_excel, export_pdf
from students.models import SchoolClass
from .forms import ResultForm
from .models import Result


def _get_teacher_class(user):
    """A teacher is assumed to be in charge of at most one class."""
    return SchoolClass.objects.filter(class_teacher=user).first()


@role_required(User.Role.TEACHER)
def teacher_dashboard(request):
    school_class = _get_teacher_class(request.user)
    students = school_class.students.filter(is_active=True) if school_class else []
    return render(
        request,
        "academics/teacher_dashboard.html",
        {"school_class": school_class, "students": students},
    )


@role_required(User.Role.TEACHER)
def add_result(request):
    school_class = _get_teacher_class(request.user)
    if not school_class:
        messages.error(request, "You are not currently assigned to a class.")
        return redirect("academics:teacher_dashboard")

    if request.method == "POST":
        form = ResultForm(request.POST, teacher_class=school_class)
        if form.is_valid():
            result = form.save(commit=False)
            if result.student.school_class_id != school_class.id:
                raise PermissionDenied("You can only add results for students in your class.")
            result.recorded_by = request.user
            result.save()
            messages.success(request, f"Result saved for {result.student.full_name}.")
            return redirect("academics:teacher_dashboard")
    else:
        form = ResultForm(teacher_class=school_class)
    return render(request, "academics/add_result.html", {"form": form, "school_class": school_class})


@role_required(User.Role.TEACHER)
def class_results(request):
    school_class = _get_teacher_class(request.user)
    results = (
        Result.objects.select_related("student", "subject")
        .filter(student__school_class=school_class)
        if school_class
        else Result.objects.none()
    )
    return render(
        request, "academics/class_results.html", {"results": results, "school_class": school_class}
    )


@role_required(User.Role.TEACHER, User.Role.HEADTEACHER)
def export_results(request, filetype):
    if request.user.role == User.Role.TEACHER:
        school_class = _get_teacher_class(request.user)
        results = Result.objects.select_related("student", "subject").filter(
            student__school_class=school_class
        )
        title = f"Results - {school_class}" if school_class else "Results"
    else:
        results = Result.objects.select_related("student", "subject").all()
        title = "All Results"

    headers = ["Admission No.", "Name", "Subject", "Term", "Year", "Score", "Grade", "Remarks"]
    rows = [
        [
            r.student.admission_number,
            r.student.full_name,
            r.subject.name,
            r.get_term_display(),
            r.year,
            r.score,
            r.grade(),
            r.remarks,
        ]
        for r in results
    ]
    fname = "results_report"
    if filetype == "pdf":
        return export_pdf(fname, title, headers, rows, landscape_mode=True)
    return export_excel(fname, title, headers, rows)
