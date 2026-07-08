from django import forms
from .models import Result, Subject


class ResultForm(forms.ModelForm):
    class Meta:
        model = Result
        fields = ["student", "subject", "term", "year", "score", "remarks"]
        widgets = {
            "student": forms.Select(attrs={"class": "form-select"}),
            "subject": forms.Select(attrs={"class": "form-select"}),
            "term": forms.Select(attrs={"class": "form-select"}),
            "year": forms.NumberInput(attrs={"class": "form-control"}),
            "score": forms.NumberInput(attrs={"class": "form-control", "min": 0, "max": 100, "step": "0.01"}),
            "remarks": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, teacher_class=None, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher_class is not None:
            self.fields["student"].queryset = teacher_class.students.filter(is_active=True)


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ["name"]
