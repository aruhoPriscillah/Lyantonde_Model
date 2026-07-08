from django import forms
from .models import Student, SchoolClass


class StudentForm(forms.ModelForm):
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    date_admitted = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}), required=False
    )

    class Meta:
        model = Student
        fields = [
            "first_name",
            "last_name",
            "gender",
            "date_of_birth",
            "school_class",
           "boarding_status",
            "guardian_name",
            "guardian_phone",
            "address",
            "date_admitted",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "school_class": forms.Select(attrs={"class": "form-select"}),
            "boarding_status": forms.Select(attrs={"class": "form-select"}),
            "guardian_name": forms.TextInput(attrs={"class": "form-control"}),
            "guardian_phone": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
        }


class SchoolClassForm(forms.ModelForm):
    class Meta:
        model = SchoolClass
        fields = ["name", "class_teacher"]
