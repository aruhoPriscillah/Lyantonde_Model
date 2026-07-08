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
            "amount": forms.NumberInput(attrs={"class": "form-control"}),
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
            "amount": forms.NumberInput(attrs={"class": "form-control"}),
        }


class TermYearFilterForm(forms.Form):
    TERM_CHOICES = [("TERM1", "Term 1"), ("TERM2", "Term 2"), ("TERM3", "Term 3")]
    term = forms.ChoiceField(choices=TERM_CHOICES, widget=forms.Select(attrs={"class": "form-select"}))
    year = forms.IntegerField(widget=forms.NumberInput(attrs={"class": "form-control"}))
