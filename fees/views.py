import datetime
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from accounts.decorators import role_required
from accounts.models import User
from reportsapp.utils import export_excel, export_pdf
from students.models import Student
from .forms import PaymentForm, FeeStructureForm, TermYearFilterForm
from .models import all_defaulters, fee_status_for_student, FeeStructure, Payment



CURRENT_YEAR = datetime.date.today().year
DEFAULT_TERM = "TERM1"


@role_required(User.Role.BURSAR, User.Role.HEADTEACHER)
def bursar_dashboard(request):
    students = Student.objects.select_related("school_class").filter(is_active=True)
    filter_form = TermYearFilterForm(
        request.GET or {"term": DEFAULT_TERM, "year": CURRENT_YEAR}
    )
    term, year = DEFAULT_TERM, CURRENT_YEAR
    if filter_form.is_valid():
        term = filter_form.cleaned_data["term"]
        year = filter_form.cleaned_data["year"]

    fee_rows = [fee_status_for_student(s, term, year) for s in students]
    defaulter_count = sum(1 for r in fee_rows if r["is_defaulter"])

    context = {
        "fee_rows": fee_rows,
        "filter_form": filter_form,
        "term": term,
        "year": year,
        "defaulter_count": defaulter_count,
        "total_students": students.count(),
        "read_only": request.user.role == User.Role.HEADTEACHER,
    }
    return render(request, "fees/bursar_dashboard.html", context)


@role_required(User.Role.BURSAR)
def record_payment(request):
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.received_by = request.user
            payment.save()
            messages.success(
                request,
                f"Payment of {payment.amount} recorded for {payment.student.full_name}.",
            )
            return redirect("fees:student_fee_detail", pk=payment.student.pk)
    else:
        initial = {"year": CURRENT_YEAR, "term": DEFAULT_TERM}
        student_id = request.GET.get("student")
        if student_id:
            initial["student"] = student_id
        form = PaymentForm(initial=initial)
    return render(request, "fees/record_payment.html", {"form": form})

@role_required(User.Role.BURSAR, User.Role.HEADTEACHER)
def student_fee_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    payments = student.payments.order_by("-year", "-date_paid")

    filter_form = TermYearFilterForm(request.GET or {"term": DEFAULT_TERM, "year": CURRENT_YEAR})
    term, year = DEFAULT_TERM, CURRENT_YEAR
    if filter_form.is_valid():
        term = filter_form.cleaned_data["term"]
        year = filter_form.cleaned_data["year"]

    fee_status = fee_status_for_student(student, term, year)

    return render(
        request,
        "fees/student_fee_detail.html",
        {
            "student": student,
            "payments": payments,
            "filter_form": filter_form,
            "term": term,
            "year": year,
            "fee_status": fee_status,
            "read_only": request.user.role == User.Role.HEADTEACHER,
        },
    )


@role_required(User.Role.BURSAR)
def edit_payment(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method == "POST":
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            messages.success(request, "Payment updated.")
            return redirect("fees:student_fee_detail", pk=payment.student.pk)
    else:
        form = PaymentForm(instance=payment)
    return render(request, "fees/edit_payment.html", {"form": form, "payment": payment})


@role_required(User.Role.BURSAR)
def delete_payment(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    student_pk = payment.student.pk
    if request.method == "POST":
        payment.delete()
        messages.success(request, "Payment deleted.")
        return redirect("fees:student_fee_detail", pk=student_pk)
    return render(request, "fees/confirm_delete_payment.html", {"payment": payment})


@role_required(User.Role.BURSAR, User.Role.HEADTEACHER)
def manage_fee_structure(request):
    if request.method == "POST":
        form = FeeStructureForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Fee structure saved.")
            return redirect("fees:manage_fee_structure")
    else:
        form = FeeStructureForm(initial={"year": CURRENT_YEAR, "term": DEFAULT_TERM})
    structures = FeeStructure.objects.select_related("school_class").all()
    return render(request, "fees/manage_fee_structure.html", {"form": form, "structures": structures})

@role_required(User.Role.BURSAR, User.Role.HEADTEACHER)
def edit_fee_structure(request, pk):
    structure = get_object_or_404(FeeStructure, pk=pk)
    if request.method == "POST":
        form = FeeStructureForm(request.POST, instance=structure)
        if form.is_valid():
            form.save()
            messages.success(request, "Fee structure updated.")
            return redirect("fees:manage_fee_structure")
    else:
        form = FeeStructureForm(instance=structure)
    return render(request, "fees/edit_fee_structure.html", {"form": form, "structure": structure})

@role_required(User.Role.BURSAR, User.Role.HEADTEACHER)
def defaulters_list(request):
    filter_form = TermYearFilterForm(request.GET or {"term": DEFAULT_TERM, "year": CURRENT_YEAR})
    term, year = DEFAULT_TERM, CURRENT_YEAR
    if filter_form.is_valid():
        term = filter_form.cleaned_data["term"]
        year = filter_form.cleaned_data["year"]
    defaulters = all_defaulters(term, year)
    return render(
        request,
        "fees/defaulters_list.html",
        {"defaulters": defaulters, "filter_form": filter_form, "term": term, "year": year},
    )


def _fee_report_rows(term, year, defaulters_only=False):
    students = Student.objects.select_related("school_class").filter(is_active=True)
    rows_data = [fee_status_for_student(s, term, year) for s in students]
    if defaulters_only:
        rows_data = [r for r in rows_data if r["is_defaulter"]]
    headers = ["Admission No.", "Name", "Class", "Expected", "Paid", "Balance", "Status"]
    rows = [
        [
            r["student"].admission_number,
            r["student"].full_name,
            r["student"].school_class.name if r["student"].school_class else "-",
            f"{r['expected']:.2f}",
            f"{r['paid']:.2f}",
            f"{r['balance']:.2f}",
            "DEFAULTER" if r["is_defaulter"] else "Cleared",
        ]
        for r in rows_data
    ]
    return headers, rows


@role_required(User.Role.BURSAR, User.Role.HEADTEACHER)
def export_fees_report(request, filetype):
    term = request.GET.get("term", DEFAULT_TERM)
    year = int(request.GET.get("year", CURRENT_YEAR))
    defaulters_only = request.GET.get("defaulters_only") == "1"
    headers, rows = _fee_report_rows(term, year, defaulters_only)
    title = f"Fee Report - {term} {year}" + (" (Defaulters)" if defaulters_only else "")
    fname = f"fee_report_{term}_{year}" + ("_defaulters" if defaulters_only else "")
    if filetype == "pdf":
        return export_pdf(fname, title, headers, rows, landscape_mode=True)
    return export_excel(fname, title, headers, rows)
