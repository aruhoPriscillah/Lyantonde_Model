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
            "photo",
            "first_name",
            "last_name",
            "gender",
            "date_of_birth",
            "school_class",
            "boarding_status",
            "former_school",
            "religion",
            "nin",
            "guardian_name",
            "guardian_phone",
            "address",
            "date_admitted",
        ]
        widgets = {
            "photo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "school_class": forms.Select(attrs={"class": "form-select"}),
            "boarding_status": forms.Select(attrs={"class": "form-select"}),
            "former_school": forms.TextInput(attrs={"class": "form-control"}),
            "religion": forms.TextInput(attrs={"class": "form-control"}),
            "nin": forms.TextInput(attrs={"class": "form-control"}),
            "guardian_name": forms.TextInput(attrs={"class": "form-control"}),
            "guardian_phone": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
        }


class SchoolClassForm(forms.ModelForm):
    class Meta:
        model = SchoolClass
        fields = ["name", "class_teacher"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "class_teacher": forms.Select(attrs={"class": "form-select"}),
        }