from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied

from accounts.decorators import role_required
from accounts.models import User
from reportsapp.utils import export_excel, export_pdf, export_report_card_pdf
from students.models import SchoolClass, Student
from fees.forms import TermYearFilterForm
from fees.models import fee_status_for_student
from .forms import ResultForm
from .models import Result, Subject
from fees.models import TERM_CHOICES

import datetime

CURRENT_YEAR = datetime.date.today().year
DEFAULT_TERM = "TERM1"


def _get_teacher_class(user):
    """A teacher is assumed to be in charge of at most one class."""
    return SchoolClass.objects.filter(class_teacher=user).first()


def pivot_class_results(school_class, term, year, students_qs=None):
    """
    Build a mark-sheet-style table: one row per student, one column per subject.
    """
    if school_class is None:
        return [], []

    students = students_qs if students_qs is not None else school_class.students.filter(is_active=True)

    results = (
        Result.objects.select_related("subject", "student")
        .filter(student__school_class=school_class, term=term, year=year)
    )

    subject_ids_with_results = sorted(
        {r.subject_id for r in results},
        key=lambda sid: next(r.subject.name for r in results if r.subject_id == sid),
    )
    subjects = list(Subject.objects.filter(id__in=subject_ids_with_results).order_by("name"))

    lookup = {(r.student_id, r.subject_id): r for r in results}

    rows = []
    for student in students:
        scores = []
        total = 0
        count = 0
        for subject in subjects:
            result = lookup.get((student.id, subject.id))
            if result is not None:
                scores.append(result)
                total += result.score
                count += 1
            else:
                scores.append(None)
        average = (total / count) if count else None
        rows.append({"student": student, "scores": scores, "total": total, "average": average})

    return subjects, rows


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

    filter_form = TermYearFilterForm(request.GET or {"term": DEFAULT_TERM, "year": CURRENT_YEAR})
    term, year = DEFAULT_TERM, CURRENT_YEAR
    if filter_form.is_valid():
        term = filter_form.cleaned_data["term"]
        year = filter_form.cleaned_data["year"]

    subjects, rows = pivot_class_results(school_class, term, year)

    return render(
        request,
        "academics/class_results.html",
        {
            "school_class": school_class,
            "subjects": subjects,
            "rows": rows,
            "filter_form": filter_form,
            "term": term,
            "year": year,
        },
    )


@role_required(User.Role.TEACHER, User.Role.HEADTEACHER)
def export_results(request, filetype):
    term = request.GET.get("term", DEFAULT_TERM)
    year = int(request.GET.get("year", CURRENT_YEAR))

    if request.user.role == User.Role.TEACHER:
        school_class = _get_teacher_class(request.user)
        title = f"Mark Sheet - {school_class} - {term} {year}" if school_class else "Mark Sheet"
        subjects, rows = pivot_class_results(school_class, term, year)
    else:
        title = f"Mark Sheet - All Classes - {term} {year}"
        all_results = Result.objects.select_related("student", "subject").filter(term=term, year=year)
        subject_ids = sorted(
            {r.subject_id for r in all_results},
            key=lambda sid: next(r.subject.name for r in all_results if r.subject_id == sid),
        )
        subjects = list(Subject.objects.filter(id__in=subject_ids).order_by("name"))
        lookup = {(r.student_id, r.subject_id): r for r in all_results}
        students = {r.student for r in all_results}
        rows = []
        for student in sorted(students, key=lambda s: s.admission_number):
            scores = []
            total = 0
            count = 0
            for subject in subjects:
                result = lookup.get((student.id, subject.id))
                if result is not None:
                    scores.append(result)
                    total += result.score
                    count += 1
                else:
                    scores.append(None)
            average = (total / count) if count else None
            rows.append({"student": student, "scores": scores, "total": total, "average": average})

    headers = ["Admission No.", "Name"] + [s.name for s in subjects] + ["Total", "Average"]
    export_rows = []
    for row in rows:
        line = [row["student"].admission_number, row["student"].full_name]
        for result in row["scores"]:
            line.append(f"{result.score:.1f} ({result.grade()})" if result else "-")
        line.append(f"{row['total']:.1f}")
        line.append(f"{row['average']:.1f}" if row["average"] is not None else "-")
        export_rows.append(line)

    fname = f"mark_sheet_{term}_{year}"
    if filetype == "pdf":
        return export_pdf(fname, title, headers, export_rows, landscape_mode=True)
    return export_excel(fname, title, headers, export_rows)

def student_report_data(student, term, year):
    """
    One pupil's results for a term/year, plus their rank within their class
    (by average score) if their classmates also have recorded results.
    """
    school_class = student.school_class
    subjects, class_rows = pivot_class_results(school_class, term, year) if school_class else ([], [])

    own_row = next((r for r in class_rows if r["student"].id == student.id), None)
    subject_rows = []
    total = 0
    average = None
    if own_row:
        total = own_row["total"]
        average = own_row["average"]
        for subject, result in zip(subjects, own_row["scores"]):
            if result is not None:
                subject_rows.append((subject.name, float(result.score), result.grade()))

    ranked = sorted(
        [r for r in class_rows if r["average"] is not None],
        key=lambda r: r["average"],
        reverse=True,
    )
    position = None
    class_size = len(ranked)
    for idx, r in enumerate(ranked, start=1):
        if r["student"].id == student.id:
            position = idx
            break

    return subject_rows, total, average, position, class_size


def _can_view_student(user, student):
    """Headteacher/Bursar can view any student; a Teacher only their own class."""
    if user.role in (User.Role.HEADTEACHER, User.Role.BURSAR):
        return True
    if user.role == User.Role.TEACHER:
        return student.school_class_id and student.school_class.class_teacher_id == user.id
    return False


@role_required(User.Role.TEACHER, User.Role.HEADTEACHER, User.Role.BURSAR)
def report_card(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if not _can_view_student(request.user, student):
        raise PermissionDenied("You do not have access to this pupil's report.")

    filter_form = TermYearFilterForm(request.GET or {"term": DEFAULT_TERM, "year": CURRENT_YEAR})
    term, year = DEFAULT_TERM, CURRENT_YEAR
    if filter_form.is_valid():
        term = filter_form.cleaned_data["term"]
        year = filter_form.cleaned_data["year"]

    subject_rows, total, average, position, class_size = student_report_data(student, term, year)
    fee_status = fee_status_for_student(student, term, year) if student.school_class else None

    return render(
        request,
        "academics/report_card.html",
        {
            "student": student,
            "term": term,
            "year": year,
            "filter_form": filter_form,
            "subject_rows": subject_rows,
            "total": total,
            "average": average,
            "position": position,
            "class_size": class_size,
            "fee_status": fee_status,
        },
    )


@role_required(User.Role.TEACHER, User.Role.HEADTEACHER, User.Role.BURSAR)
def export_report_card(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if not _can_view_student(request.user, student):
        raise PermissionDenied("You do not have access to this pupil's report.")

    term = request.GET.get("term", DEFAULT_TERM)
    year = int(request.GET.get("year", CURRENT_YEAR))
    term_label = dict(TERM_CHOICES).get(term, term)

    subject_rows, total, average, position, class_size = student_report_data(student, term, year)
    fee_status = fee_status_for_student(student, term, year) if student.school_class else None

    fname = f"report_card_{student.admission_number}_{term}_{year}"
    return export_report_card_pdf(
        fname, student, term_label, year, subject_rows, total, average, position, class_size, fee_status
    )