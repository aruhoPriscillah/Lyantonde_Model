import datetime
import re
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied

from accounts.decorators import role_required
from accounts.models import User
from reportsapp.utils import (
    export_excel,
    export_nursery_report_card_pdf,
    export_pdf,
    export_progressive_report_card_pdf,
    export_report_card_pdf,
)
from students.models import SchoolClass, Student
from fees.forms import TermYearFilterForm
from fees.models import fee_status_for_student, TERM_CHOICES
from .forms import AcademicTermForm, ResultForm, GradingScaleForm, BulkResultFilterForm, SubjectForm
from .models import AcademicTerm, Result, Subject, GradingScale, term_is_closed
from .subject_sets import is_lower_primary_class, is_nursery_class, is_upper_primary_class
from .subject_sets import NURSERY_SUBJECT_NAMES
from .subject_sets import subject_names_for_class

CURRENT_YEAR = datetime.date.today().year
DEFAULT_TERM = "TERM1"


@role_required(User.Role.HEADTEACHER)
def manage_terms(request):
    if request.method == "POST":
        form = AcademicTermForm(request.POST)
        if form.is_valid():
            values = form.cleaned_data
            AcademicTerm.objects.update_or_create(
                term=values["term"], year=values["year"],
                defaults={
                    "opens_on": values["opens_on"],
                    "closes_on": values["closes_on"],
                    "is_closed": values["is_closed"],
                },
            )
            messages.success(request, "Academic term saved.")
            return redirect("academics:manage_terms")
    else:
        form = AcademicTermForm(initial={"term": DEFAULT_TERM, "year": CURRENT_YEAR})
    return render(request, "academics/manage_terms.html", {
        "form": form,
        "terms": AcademicTerm.objects.all(),
    })

LOWER_PRIMARY_SUBJECTS = (
    ("Mathematics", {"mathematics", "math", "maths"}),
    ("English", {"english"}),
    ("Literacy I", {"literacy i", "literacy 1"}),
    ("Literacy II (Reading)", {"literacy ii", "literacy 2", "literacy ii (reading)", "reading"}),
    ("Religious Education", {"religious education", "re", "r.e"}),
    ("Luganda", {"luganda"}),
)
UPPER_PRIMARY_SUBJECTS = (
    ("MATH", {"mathematics", "math", "maths"}),
    ("ENG", {"english"}),
    ("SST", {"sst", "social studies"}),
    ("SCIE", {"science", "integrated science"}),
)


@role_required(User.Role.HEADTEACHER)
def manage_subjects(request):
    if request.method == "POST":
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Subject added.")
            return redirect("academics:manage_subjects")
    else:
        form = SubjectForm()
    subjects = Subject.objects.all().order_by("name")
    return render(request, "academics/manage_subjects.html", {"form": form, "subjects": subjects})


@role_required(User.Role.HEADTEACHER)
def delete_subject(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == "POST":
        subject.delete()
        messages.success(request, f"'{subject.name}' deleted.")
        return redirect("academics:manage_subjects")
    return render(request, "academics/confirm_delete_subject.html", {"subject": subject})

def _get_teacher_class(user):
    return SchoolClass.objects.filter(class_teacher=user).first()


def pivot_class_results(school_class, term, year, students_qs=None):
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
def export_class_list(request, filetype):
    school_class = _get_teacher_class(request.user)
    if not school_class:
        messages.error(request, "You are not currently assigned to a class.")
        return redirect("academics:teacher_dashboard")

    students = school_class.students.filter(is_active=True)
    headers = ["Admission No.", "Full Name", "Gender", "Boarding Status", "Guardian", "Guardian Phone"]
    rows = [
        [
            s.admission_number,
            s.full_name,
            s.get_gender_display(),
            s.get_boarding_status_display(),
            s.guardian_name,
            s.guardian_phone,
        ]
        for s in students
    ]

    title = f"Class List - {school_class}"
    fname = f"class_list_{school_class.name.replace(' ', '_')}"
    if filetype == "pdf":
        return export_pdf(fname, title, headers, rows, landscape_mode=True)
    return export_excel(fname, title, headers, rows)

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
            if term_is_closed(result.term, result.year):
                form.add_error(None, "This term is closed. Results cannot be changed.")
            else:
                result.recorded_by = request.user
                result.save()
                messages.success(request, f"Result saved for {result.student.full_name}.")
                return redirect(f"/teacher/academics/results/?term={result.term}&year={result.year}")
    else:
        form = ResultForm(teacher_class=school_class)
    return render(request, "academics/add_result.html", {"form": form, "school_class": school_class})

@role_required(User.Role.TEACHER)
def bulk_add_results(request):
    school_class = _get_teacher_class(request.user)
    if not school_class:
        messages.error(request, "You are not currently assigned to a class.")
        return redirect("academics:teacher_dashboard")

    students = list(school_class.students.filter(is_active=True))
    data = request.POST if request.method == "POST" else (request.GET or {"term": DEFAULT_TERM, "year": CURRENT_YEAR})
    filter_form = BulkResultFilterForm(data, teacher_class=school_class)

    subject = None
    term, year = DEFAULT_TERM, CURRENT_YEAR
    if filter_form.is_valid():
        subject = filter_form.cleaned_data.get("subject")
        term = filter_form.cleaned_data["term"]
        year = filter_form.cleaned_data["year"]

    if request.method == "POST":
        if not subject:
            messages.error(request, "Please choose a subject before saving.")
        elif term_is_closed(term, year):
            messages.error(request, "This term is closed. Results cannot be changed.")
        else:
            saved_count = 0
            for student in students:
                score_raw = request.POST.get(f"score_{student.id}", "").strip()
                if score_raw == "":
                    continue
                try:
                    score_value = float(score_raw)
                except ValueError:
                    continue
                remarks = request.POST.get(f"remarks_{student.id}", "").strip()
                Result.objects.update_or_create(
                    student=student, subject=subject, term=term, year=year,
                    defaults={"score": score_value, "remarks": remarks, "recorded_by": request.user},
                )
                saved_count += 1
            messages.success(request, f"Saved results for {saved_count} pupil(s) in {subject.name} ({term} {year}).")
            return redirect(f"/teacher/academics/results/?term={term}&year={year}")
    existing = {}
    if subject:
        existing = {
            r.student_id: r for r in Result.objects.filter(
                student__in=students, subject=subject, term=term, year=year
            )
        }
    rows = [(student, existing.get(student.id)) for student in students]

    return render(request, "academics/bulk_add_results.html", {
        "school_class": school_class,
        "filter_form": filter_form,
        "rows": rows,
        "subject": subject,
        "term": term,
        "year": year,
    })


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
        class_id = request.GET.get("class_id")
        school_class = SchoolClass.objects.filter(id=class_id).first() if class_id else None
        title = f"Mark Sheet - {school_class or 'All Classes'} - {term} {year}"
        if school_class:
            subjects, rows = pivot_class_results(school_class, term, year)
        else:
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


@role_required(User.Role.HEADTEACHER)
def all_results(request):
    """Headteacher view: pick any class, see its mark sheet for a term/year."""
    classes = SchoolClass.objects.all()
    class_id = request.GET.get("class_id")
    selected_class = classes.filter(id=class_id).first() if class_id else classes.first()

    filter_form = TermYearFilterForm(request.GET or {"term": DEFAULT_TERM, "year": CURRENT_YEAR})
    term, year = DEFAULT_TERM, CURRENT_YEAR
    if filter_form.is_valid():
        term = filter_form.cleaned_data["term"]
        year = filter_form.cleaned_data["year"]

    subjects, rows = pivot_class_results(selected_class, term, year) if selected_class else ([], [])

    return render(
        request,
        "academics/all_results.html",
        {
            "classes": classes,
            "selected_class": selected_class,
            "subjects": subjects,
            "rows": rows,
            "filter_form": filter_form,
            "term": term,
            "year": year,
        },
    )


def student_report_data(student, term, year):
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


def nursery_report_rows(student, term, year):
    results = (
        Result.objects.select_related("subject", "recorded_by")
        .filter(student=student, term=term, year=year)
    )
    lookup = {result.subject.name.lower().strip(): result for result in results}
    rows = []
    for subject_name in NURSERY_SUBJECT_NAMES:
        result = lookup.get(subject_name.lower())
        rows.append({
            "subject": subject_name,
            "score": result.score if result else None,
            "remarks": result.get_remarks_display() if result and result.remarks else "",
            "initials": (
                (result.recorded_by.get_full_name() or result.recorded_by.username)[:1].upper()
                if result and result.recorded_by else ""
            ),
        })
    return rows


def lower_primary_report_rows(student, term, year):
    results = Result.objects.select_related("subject", "recorded_by").filter(
        student=student, term=term, year=year
    )
    lookup = {result.subject.name.lower().strip(): result for result in results}
    rows = []
    for label, aliases in LOWER_PRIMARY_SUBJECTS:
        result = next((lookup[alias] for alias in aliases if alias in lookup), None)
        rows.append({
            "subject": label,
            "score": result.score if result else None,
            "remarks": result.get_remarks_display() if result and result.remarks else "",
            "initials": (
                (result.recorded_by.get_full_name() or result.recorded_by.username)[:1].upper()
                if result and result.recorded_by else ""
            ),
        })
    return rows


def progressive_report_rows(student, term, year):
    results = Result.objects.select_related("subject", "recorded_by").filter(
        student=student, term=term, year=year
    )
    lookup = {result.subject.name.lower().strip(): result for result in results}
    rows = []
    for label, aliases in UPPER_PRIMARY_SUBJECTS:
        result = next((lookup[alias] for alias in aliases if alias in lookup), None)
        grade = result.grade() if result else ""
        grade_match = re.search(r"(\d+)$", grade)
        rows.append({
            "subject": label,
            "score": result.score if result else None,
            "aggregate": int(grade_match.group(1)) if grade_match else None,
            "remarks": result.get_remarks_display() if result and result.remarks else "",
            "initials": (
                (result.recorded_by.get_full_name() or result.recorded_by.username)[:1].upper()
                if result and result.recorded_by else ""
            ),
        })
    return rows


def progressive_division(rows):
    aggregates = [row["aggregate"] for row in rows if row["aggregate"] is not None]
    if len(aggregates) != len(UPPER_PRIMARY_SUBJECTS):
        return "-"
    total = sum(aggregates)
    if total <= 12:
        return "Division 1"
    if total <= 24:
        return "Division 2"
    if total <= 28:
        return "Division 3"
    if total <= 32:
        return "Division 4"
    return "Ungraded"


def _can_view_student(user, student):
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
    nursery_report = is_nursery_class(student.school_class)
    nursery_rows = nursery_report_rows(student, term, year) if nursery_report else []
    nursery_scores = [row["score"] for row in nursery_rows if row["score"] is not None]
    lower_primary_report = is_lower_primary_class(student.school_class)
    upper_primary_report = is_upper_primary_class(student.school_class)
    progressive_rows = progressive_report_rows(student, term, year) if upper_primary_report else []
    progressive_scores = [row["score"] for row in progressive_rows if row["score"] is not None]
    if nursery_report:
        template_name = "academics/nursery_report_card.html"
    elif lower_primary_report:
        template_name = "academics/lower_primary_report_card.html"
    elif upper_primary_report:
        template_name = "academics/progressive_report_card.html"
    else:
        template_name = "academics/report_card.html"

    return render(
        request,
        template_name,
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
            "nursery_rows": nursery_rows,
            "nursery_total": sum(nursery_scores),
            "lower_primary_rows": lower_primary_report_rows(student, term, year) if lower_primary_report else [],
            "progressive_rows": progressive_rows,
            "division": progressive_division(progressive_rows) if upper_primary_report else "-",
            "progressive_total": sum(progressive_scores),
            "progressive_average": (
                sum(progressive_scores) / len(progressive_scores) if progressive_scores else None
            ),
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
    if is_nursery_class(student.school_class):
        return export_nursery_report_card_pdf(
            fname,
            student,
            term_label,
            year,
            nursery_report_rows(student, term, year),
            position,
            class_size,
            fee_status,
        )
    if is_lower_primary_class(student.school_class):
        return export_nursery_report_card_pdf(
            fname,
            student,
            term_label,
            year,
            lower_primary_report_rows(student, term, year),
            position,
            class_size,
            fee_status,
        )
    if is_upper_primary_class(student.school_class):
        rows = progressive_report_rows(student, term, year)
        return export_progressive_report_card_pdf(
            fname, student, term_label, year, rows, progressive_division(rows), fee_status
        )
    return export_report_card_pdf(
        fname, student, term_label, year, subject_rows, total, average, position, class_size, fee_status
    )


@role_required(User.Role.HEADTEACHER)
def manage_grading_scale(request):
    if request.method == "POST":
        form = GradingScaleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Grade band saved.")
            return redirect("academics:manage_grading_scale")
    else:
        form = GradingScaleForm()
    bands = GradingScale.objects.order_by("-min_score")
    return render(request, "academics/manage_grading_scale.html", {"form": form, "bands": bands})


@role_required(User.Role.HEADTEACHER)
def edit_grading_scale(request, pk):
    band = get_object_or_404(GradingScale, pk=pk)
    if request.method == "POST":
        form = GradingScaleForm(request.POST, instance=band)
        if form.is_valid():
            form.save()
            messages.success(request, f"Grade band '{band.grade}' updated.")
            return redirect("academics:manage_grading_scale")
    else:
        form = GradingScaleForm(instance=band)
    return render(request, "academics/edit_grading_scale.html", {"form": form, "band": band})


@role_required(User.Role.HEADTEACHER)
def delete_grading_scale(request, pk):
    band = get_object_or_404(GradingScale, pk=pk)
    if request.method == "POST":
        band.delete()
        messages.success(request, f"Grade band '{band.grade}' deleted.")
        return redirect("academics:manage_grading_scale")
    return render(request, "academics/confirm_delete_grading_scale.html", {"band": band})
