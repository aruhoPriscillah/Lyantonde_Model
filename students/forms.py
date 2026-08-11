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
            "lin",
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
            "lin": forms.TextInput(attrs={
                "class": "form-control",
                "maxlength": 30,
                "autocomplete": "off",
            }),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "school_class": forms.Select(attrs={"class": "form-select"}),
            "boarding_status": forms.Select(attrs={"class": "form-select"}),
            "former_school": forms.TextInput(attrs={"class": "form-control"}),
           "religion": forms.Select(attrs={"class": "form-select"}),
            "nin": forms.TextInput(attrs={
                "class": "form-control",
                "maxlength": 14,
                "placeholder": "e.g. CM4900906P76ZE",
                "autocomplete": "off",
            }),
            "guardian_name": forms.TextInput(attrs={"class": "form-control"}),
            "guardian_phone": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean_nin(self):
        return self.cleaned_data.get("nin", "").strip().upper()


class SchoolClassForm(forms.ModelForm):
    class Meta:
        model = SchoolClass
        fields = ["name", "class_teacher"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "class_teacher": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["class_teacher"].queryset = self.fields["class_teacher"].queryset.filter(
            role="TEACHER", is_active=True
        ).order_by("first_name", "last_name", "username")
