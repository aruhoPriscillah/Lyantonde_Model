import datetime
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from accounts.decorators import role_required
from accounts.models import User
from academics.models import term_is_closed
from reportsapp.utils import export_excel, export_pdf
from students.models import Student
from .forms import PaymentForm, FeeStructureForm, TermYearFilterForm, VaultFilterForm
from .models import all_defaulters, fee_status_for_student, FeeStructure, Payment
from .utils import format_ugx
from django.db.models import Q, Sum
from .models import all_defaulters, fee_status_for_student, FeeStructure, Payment



CURRENT_YEAR = datetime.date.today().year
DEFAULT_TERM = "TERM1"


@role_required(User.Role.BURSAR, User.Role.HEADTEACHER)
def bursar_dashboard(request):
    students = Student.objects.select_related("school_class").filter(is_active=True)
    search_query = request.GET.get("q", "").strip()
    for token in search_query.split():
        students = students.filter(
            Q(admission_number__icontains=token)
            | Q(first_name__icontains=token)
            | Q(last_name__icontains=token)
        )
    filter_form = TermYearFilterForm(
        request.GET or {"term": DEFAULT_TERM, "year": CURRENT_YEAR}
    )
    term, year = DEFAULT_TERM, CURRENT_YEAR
    if filter_form.is_valid():
        term = filter_form.cleaned_data["term"]
        year = filter_form.cleaned_data["year"]

    fee_rows = [fee_status_for_student(s, term, year) for s in students]
    defaulter_count = sum(1 for r in fee_rows if r["is_defaulter"])

    vault_form = VaultFilterForm(request.GET or {"period": "TERM", "term": DEFAULT_TERM, "year": CURRENT_YEAR})
    vault_total = 0
    vault_label = "Select a period"
    if vault_form.is_valid():
        period = vault_form.cleaned_data["period"]
        if period == "DAY":
            d = vault_form.cleaned_data.get("date") or datetime.date.today()
            vault_total = Payment.objects.filter(date_paid=d).aggregate(total=Sum("amount"))["total"] or 0
            vault_label = f"Collections on {d}"
        elif period == "MONTH":
            m = vault_form.cleaned_data.get("month") or datetime.date.today().month
            y = vault_form.cleaned_data.get("year") or CURRENT_YEAR
            vault_total = Payment.objects.filter(date_paid__year=y, date_paid__month=m).aggregate(total=Sum("amount"))["total"] or 0
            vault_label = f"Collections in {m:02d}/{y}"
        elif period == "TERM":
            t = vault_form.cleaned_data.get("term") or DEFAULT_TERM
            y = vault_form.cleaned_data.get("year") or CURRENT_YEAR
            vault_total = Payment.objects.filter(term=t, year=y).aggregate(total=Sum("amount"))["total"] or 0
            vault_label = f"Collections in {dict(vault_form.TERM_CHOICES).get(t, t)} {y}"
        elif period == "YEAR":
            y = vault_form.cleaned_data.get("year") or CURRENT_YEAR
            vault_total = Payment.objects.filter(year=y).aggregate(total=Sum("amount"))["total"] or 0
            vault_label = f"Collections in {y}"
        else:
            vault_total = Payment.objects.aggregate(total=Sum("amount"))["total"] or 0
            vault_label = "All-Time Collections"

    context = {
        "fee_rows": fee_rows,
        "search_query": search_query,
        "filter_form": filter_form,
        "term": term,
        "year": year,
        "defaulter_count": defaulter_count,
        "total_students": students.count(),
        "read_only": request.user.role == User.Role.HEADTEACHER,
        "vault_form": vault_form,
        "vault_total": vault_total,
        "vault_label": vault_label,
    }
    return render(request, "fees/bursar_dashboard.html", context)


@role_required(User.Role.BURSAR)
def record_payment(request):
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            if term_is_closed(payment.term, payment.year):
                form.add_error(None, "This term is closed. Payments cannot be changed.")
                return render(request, "fees/record_payment.html", {"form": form})
            payment.received_by = request.user
            payment.save()
            messages.success(
                request,
                f"Payment of {format_ugx(payment.amount)} recorded for {payment.student.full_name}.",
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
    original_term, original_year = payment.term, payment.year
    if request.method == "POST":
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            candidate = form.save(commit=False)
            if term_is_closed(candidate.term, candidate.year) or term_is_closed(original_term, original_year):
                form.add_error(None, "This term is closed. Payments cannot be changed.")
            else:
                candidate.save()
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
        if term_is_closed(payment.term, payment.year):
            messages.error(request, "This term is closed. Payments cannot be changed.")
        else:
            payment.delete()
            messages.success(request, "Payment deleted.")
        return redirect("fees:student_fee_detail", pk=student_pk)
    return render(request, "fees/confirm_delete_payment.html", {"payment": payment})


@role_required(User.Role.BURSAR, User.Role.HEADTEACHER)
def manage_fee_structure(request):
    if request.method == "POST":
        form = FeeStructureForm(request.POST)
        if form.is_valid():
            structure = form.save(commit=False)
            if term_is_closed(structure.term, structure.year):
                form.add_error(None, "This term is closed. Fee structures cannot be changed.")
            else:
                structure.save()
                messages.success(request, "Fee structure saved.")
                return redirect("fees:manage_fee_structure")
    else:
        form = FeeStructureForm(initial={"year": CURRENT_YEAR, "term": DEFAULT_TERM})
    structures = FeeStructure.objects.select_related("school_class").all()
    return render(request, "fees/manage_fee_structure.html", {"form": form, "structures": structures})

@role_required(User.Role.BURSAR, User.Role.HEADTEACHER)
def edit_fee_structure(request, pk):
    structure = get_object_or_404(FeeStructure, pk=pk)
    original_term, original_year = structure.term, structure.year
    if request.method == "POST":
        form = FeeStructureForm(request.POST, instance=structure)
        if form.is_valid():
            candidate = form.save(commit=False)
            if term_is_closed(candidate.term, candidate.year) or term_is_closed(original_term, original_year):
                form.add_error(None, "This term is closed. Fee structures cannot be changed.")
            else:
                candidate.save()
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
    headers = ["Admission No.", "Name", "Class", "Previous Balance", "Current Fees", "Total Due", "Paid This Term", "Balance", "Status"]
    rows = [
        [
            r["student"].admission_number,
            r["student"].full_name,
            r["student"].school_class.name if r["student"].school_class else "-",
            format_ugx(r["previous_balance"]),
            format_ugx(r["expected"]),
            format_ugx(r["total_due"]),
            format_ugx(r["paid"]),
            format_ugx(r["balance"]),
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
