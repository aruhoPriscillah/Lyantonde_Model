from django import forms
from .models import Result, Subject
from .models import GradingScale
from .models import Subject

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
        widgets = {"name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Mathematics"})}

class GradingScaleForm(forms.ModelForm):
    class Meta:
        model = GradingScale
        fields = ["grade", "min_score"]
        widgets = {
            "grade": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. D1"}),
            "min_score": forms.NumberInput(attrs={"class": "form-control", "min": 0, "max": 100, "step": "0.01"}),
        }

        
class BulkResultFilterForm(forms.Form):
    TERM_CHOICES = [("TERM1", "Term 1"), ("TERM2", "Term 2"), ("TERM3", "Term 3")]
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(), required=False,
        widget=forms.Select(attrs={"class": "form-select"})
    )
    term = forms.ChoiceField(choices=TERM_CHOICES, widget=forms.Select(attrs={"class": "form-select"}))
    year = forms.IntegerField(widget=forms.NumberInput(attrs={"class": "form-control"}))