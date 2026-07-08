import datetime
from django.conf import settings
from django.db import models
from django.db.models import Max


class SchoolClass(models.Model):
    """A class/stream, e.g. Primary 1, Primary 2 ... each led by one teacher."""

    name = models.CharField(max_length=50, unique=True)  
    class_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="classes_managed",
        limit_choices_to={"role": "TEACHER"},
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Student(models.Model):
    class Gender(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"
        
    class BoardingStatus(models.TextChoices):
        DAY = "DAY", "Day Scholar"
        BOARDING = "BOARDING", "Boarding Scholar"

    admission_number = models.CharField(max_length=20, unique=True, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=Gender.choices)
    date_of_birth = models.DateField()
    school_class = models.ForeignKey(
        SchoolClass, on_delete=models.SET_NULL, null=True, related_name="students"
    )
    boarding_status = models.CharField(
        max_length=10, choices=BoardingStatus.choices, default=BoardingStatus.DAY
    )
    guardian_name = models.CharField(max_length=150)
    guardian_phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255, blank=True)
    date_admitted = models.DateField(default=datetime.date.today)
    is_active = models.BooleanField(default=True)
    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["admission_number"]

    def __str__(self):
        return f"{self.admission_number} - {self.full_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.admission_number:
            self.admission_number = self._generate_admission_number()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_admission_number():
        """Format: LM<4+ digit sequence>, e.g. LM0001, LM0002 ... LM10000."""
        prefix = "LM"
        last = (
            Student.objects.filter(admission_number__startswith=prefix)
            .aggregate(Max("admission_number"))
            .get("admission_number__max")
        )
        if last:
            last_seq = int(last[len(prefix):])
        else:
            last_seq = 0
        return f"{prefix}{last_seq + 1:04d}"