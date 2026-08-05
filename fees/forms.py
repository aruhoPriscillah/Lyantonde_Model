from django import forms
from .models import Payment, FeeStructure


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["student", "term", "year", "amount", "method", "reference"]
        widgets = {
            "student": forms.Select(attrs={"class": "form-select"}),
            "term": forms.Select(attrs={"class": "form-select"}),
            "year": forms.NumberInput(attrs={"class": "form-control"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "min": "0.01", "step": "0.01"}),
            "method": forms.Select(attrs={"class": "form-select"}),
            "reference": forms.TextInput(attrs={"class": "form-control"}),
        }


class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = ["school_class", "term", "year", "boarding_status", "amount"]
        widgets = {
            "school_class": forms.Select(attrs={"class": "form-select"}),
            "term": forms.Select(attrs={"class": "form-select"}),
            "year": forms.NumberInput(attrs={"class": "form-control"}),
            "boarding_status": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "min": "0.01", "step": "0.01"}),
        }


class TermYearFilterForm(forms.Form):
    TERM_CHOICES = [("TERM1", "Term 1"), ("TERM2", "Term 2"), ("TERM3", "Term 3")]
    term = forms.ChoiceField(choices=TERM_CHOICES, widget=forms.Select(attrs={"class": "form-select"}))
    year = forms.IntegerField(widget=forms.NumberInput(attrs={"class": "form-control"}))


class VaultFilterForm(forms.Form):
    PERIOD_CHOICES = [
        ("DAY", "Day"),
        ("MONTH", "Month"),
        ("TERM", "Term"),
        ("YEAR", "Year"),
        ("ALL", "All Time"),
    ]
    TERM_CHOICES = [("TERM1", "Term 1"), ("TERM2", "Term 2"), ("TERM3", "Term 3")]

    period = forms.ChoiceField(choices=PERIOD_CHOICES, widget=forms.Select(attrs={"class": "form-select", "id": "id_vault_period"}))
    date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date", "class": "form-control vault-field vault-field-day"}))
    month = forms.IntegerField(required=False, min_value=1, max_value=12, widget=forms.NumberInput(attrs={"class": "form-control vault-field vault-field-month", "placeholder": "Month (1-12)"}))
    term = forms.ChoiceField(choices=TERM_CHOICES, required=False, widget=forms.Select(attrs={"class": "form-select vault-field vault-field-term"}))
    year = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={"class": "form-control vault-field vault-field-month vault-field-term vault-field-year", "placeholder": "Year"}))
