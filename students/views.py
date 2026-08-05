import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from accounts.decorators import role_required
from accounts.models import User
from accounts.forms import StaffCreationForm
from reportsapp.utils import export_excel, export_pdf
from .forms import StudentForm, SchoolClassForm
from .models import Requirement, Student, SchoolClass, StudentRequirement
from fees.forms import TermYearFilterForm
from fees.models import TERM_CHOICES


@login_required
def dashboard_redirect(request):
    role_urls = {
        User.Role.HEADTEACHER: "students:headteacher_dashboard",
        User.Role.BURSAR: "fees:bursar_dashboard",
        User.Role.TEACHER: "academics:teacher_dashboard",
    }
    return redirect(role_urls.get(request.user.role, "login"))


@role_required(User.Role.HEADTEACHER)
def headteacher_dashboard(request):
    active_students = Student.objects.select_related("school_class").filter(is_active=True)
    search_query = request.GET.get("q", "").strip()
    students = active_students
    for token in search_query.split():
        students = students.filter(
            Q(admission_number__icontains=token)
            | Q(first_name__icontains=token)
            | Q(last_name__icontains=token)
        )
    context = {
        "students": students,
        "search_query": search_query,
        "total_students": active_students.count(),
        "total_classes": SchoolClass.objects.count(),
    }
    return render(request, "students/headteacher_dashboard.html", context)


@role_required(User.Role.HEADTEACHER)
def register_student(request):
    if request.method == "POST":
        form = StudentForm(request.POST, request.FILES)
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


@role_required(User.Role.HEADTEACHER)
def manage_staff(request):
    if request.method == "POST":
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            staff_member = form.save()
            messages.success(request, f"Teacher {staff_member.get_full_name() or staff_member.username} added.")
            return redirect("students:manage_staff")
    else:
        form = StaffCreationForm()
    staff = User.objects.filter(role=User.Role.TEACHER).prefetch_related("classes_managed").order_by(
        "first_name", "last_name", "username"
    )
    return render(request, "students/manage_staff.html", {"form": form, "staff": staff})


def _requirement_group(school_class):
    if not school_class:
        return None
    name = " ".join(school_class.name.lower().replace("-", " ").split())
    if name.endswith(" class"):
        name = name[:-6].strip()
    nursery_p3 = {
        "baby", "nursery", "middle", "top", "p1", "p 1", "primary 1", "primary one",
        "p2", "p 2", "primary 2", "primary two", "p3", "p 3", "primary 3", "primary three",
    }
    p4_p7 = {
        "p4", "p 4", "primary 4", "primary four", "p5", "p 5", "primary 5", "primary five",
        "p6", "p 6", "primary 6", "primary six", "p7", "p 7", "primary 7", "primary seven",
    }
    if name in nursery_p3:
        return Requirement.ClassGroup.NURSERY_P3
    if name in p4_p7:
        return Requirement.ClassGroup.P4_P7
    return None


@role_required(User.Role.HEADTEACHER)
def requirements_register(request):
    classes = SchoolClass.objects.all()
    class_id = request.POST.get("class_id") if request.method == "POST" else request.GET.get("class_id")
    selected_class = classes.filter(pk=class_id).first() if class_id else classes.first()
    filter_data = (request.POST if request.method == "POST" else request.GET).copy()
    filter_data.setdefault("term", "TERM1")
    filter_data.setdefault("year", datetime.date.today().year)
    scholar_type = filter_data.get("scholar_type", Student.BoardingStatus.DAY)
    if scholar_type not in Student.BoardingStatus.values:
        scholar_type = Student.BoardingStatus.DAY
    filter_form = TermYearFilterForm(filter_data)
    term, year = "TERM1", datetime.date.today().year
    if filter_form.is_valid():
        term = filter_form.cleaned_data["term"]
        year = filter_form.cleaned_data["year"]

    class_group = _requirement_group(selected_class)
    requirements = list(Requirement.objects.filter(
        class_group=class_group, scholar_type=scholar_type, is_active=True
    )) if class_group else []
    students = list(selected_class.students.filter(
        is_active=True, boarding_status=scholar_type
    ).order_by("admission_number")) if selected_class else []

    if request.method == "POST" and selected_class and requirements:
        requirement_ids = {requirement.id for requirement in requirements}
        student_ids = {student.id for student in students}
        checked = set()
        for value in request.POST.getlist("brought"):
            parts = value.split(":", 1)
            if len(parts) != 2 or not all(part.isdigit() for part in parts):
                continue
            student_id, requirement_id = map(int, parts)
            if student_id in student_ids and requirement_id in requirement_ids:
                checked.add((student_id, requirement_id))
        today = timezone.localdate()
        with transaction.atomic():
            for student in students:
                for requirement in requirements:
                    is_brought = (student.id, requirement.id) in checked
                    StudentRequirement.objects.update_or_create(
                        student=student, requirement=requirement, term=term, year=year,
                        defaults={
                            "brought": is_brought,
                            "brought_on": today if is_brought else None,
                            "recorded_by": request.user,
                        },
                    )
        messages.success(request, f"Requirements register saved for {selected_class}.")
        return redirect(
            f"{request.path}?class_id={selected_class.id}&term={term}&year={year}&scholar_type={scholar_type}&saved=1"
        )

    existing = {
        (record.student_id, record.requirement_id): record
        for record in StudentRequirement.objects.filter(
            student__in=students, requirement__in=requirements, term=term, year=year
        )
    }
    rows = [
        {
            "student": student,
            "items": [
                {"requirement": requirement, "record": existing.get((student.id, requirement.id))}
                for requirement in requirements
            ],
            "received": sum(
                1 for requirement in requirements
                if existing.get((student.id, requirement.id)) and existing[(student.id, requirement.id)].brought
            ),
        }
        for student in students
    ]
    return render(request, "students/requirements_register.html", {
        "classes": classes,
        "selected_class": selected_class,
        "filter_form": filter_form,
        "term": term,
        "year": year,
        "scholar_type": scholar_type,
        "scholar_type_choices": Student.BoardingStatus.choices,
        "saved": request.GET.get("saved") == "1",
        "requirements": requirements,
        "rows": rows,
    })


@role_required(User.Role.HEADTEACHER)
def export_requirements_register(request):
    school_class = get_object_or_404(SchoolClass, pk=request.GET.get("class_id"))
    scholar_type = request.GET.get("scholar_type", Student.BoardingStatus.DAY)
    if scholar_type not in Student.BoardingStatus.values:
        scholar_type = Student.BoardingStatus.DAY
    term = request.GET.get("term", "TERM1")
    if term not in dict(TERM_CHOICES):
        term = "TERM1"
    try:
        year = int(request.GET.get("year", datetime.date.today().year))
    except (TypeError, ValueError):
        year = datetime.date.today().year

    class_group = _requirement_group(school_class)
    requirements = list(Requirement.objects.filter(
        class_group=class_group, scholar_type=scholar_type, is_active=True
    )) if class_group else []
    students = list(school_class.students.filter(
        is_active=True, boarding_status=scholar_type
    ).order_by("admission_number"))
    existing = {
        (record.student_id, record.requirement_id): record.brought
        for record in StudentRequirement.objects.filter(
            student__in=students, requirement__in=requirements, term=term, year=year
        )
    }
    headers = ["Admission No.", "Pupil Name"] + [item.name for item in requirements] + ["Received"]
    rows = []
    for student in students:
        statuses = [existing.get((student.id, item.id), False) for item in requirements]
        rows.append([
            student.admission_number,
            student.full_name,
            *["Brought" if status else "Missing" for status in statuses],
            f"{sum(statuses)}/{len(requirements)}",
        ])
    type_label = "Boarding Scholars" if scholar_type == Student.BoardingStatus.BOARDING else "Day Scholars"
    title = f"Requirements - {school_class} - {type_label} - {term} {year}"
    filename = f"requirements_{school_class.name.replace(' ', '_')}_{scholar_type}_{term}_{year}"
    return export_excel(filename, title, headers, rows)


@role_required(User.Role.HEADTEACHER)
def edit_class(request, pk):
    school_class = get_object_or_404(SchoolClass, pk=pk)
    if request.method == "POST":
        form = SchoolClassForm(request.POST, instance=school_class)
        if form.is_valid():
            form.save()
            messages.success(request, f"'{school_class.name}' updated.")
            return redirect("students:manage_classes")
    else:
        form = SchoolClassForm(instance=school_class)
    return render(request, "students/edit_class.html", {"form": form, "school_class": school_class})


@role_required(User.Role.HEADTEACHER, User.Role.BURSAR, User.Role.TEACHER)
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    return render(request, "students/student_detail.html", {"student": student})


@role_required(User.Role.HEADTEACHER)
def export_students(request, filetype):
    students = Student.objects.select_related("school_class").filter(is_active=True)
    headers = ["Admission No.", "Full Name", "Gender", "Class", "Boarding Status", "Guardian", "Guardian Phone", "Date Admitted"]
    rows = [
        [
            s.admission_number,
            s.full_name,
            s.get_gender_display(),
            s.school_class.name if s.school_class else "-",
            s.get_boarding_status_display(),
            s.guardian_name,
            s.guardian_phone,
            s.date_admitted.strftime("%Y-%m-%d"),
        ]
        for s in students
    ]
    if filetype == "pdf":
        return export_pdf("all_students", "All Registered Students", headers, rows, landscape_mode=True)
    return export_excel("all_students", "All Students", headers, rows)
