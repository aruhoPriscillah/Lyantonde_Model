import datetime
import re
from django.conf import settings
from django.db import models
from django.db.models import Max
from django.core.validators import RegexValidator


uganda_nin_validator = RegexValidator(
    regex=r"^C[MF][A-Z0-9]{12}$",
    flags=re.IGNORECASE,
    message="Enter a valid 14-character Ugandan NIN beginning with CM or CF.",
)


class SchoolClass(models.Model):
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


class Requirement(models.Model):
    class ClassGroup(models.TextChoices):
        NURSERY_P3 = "NURSERY_P3", "Nursery - P3"
        P4_P7 = "P4_P7", "P4 - P7"

    name = models.CharField(max_length=150)
    class_group = models.CharField(max_length=20, choices=ClassGroup.choices)
    scholar_type = models.CharField(
        max_length=10, choices=(("DAY", "Day Scholar"), ("BOARDING", "Boarding Scholar")), default="DAY"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["scholar_type", "class_group", "id"]
        unique_together = ("name", "class_group", "scholar_type")

    def __str__(self):
        return f"{self.name} ({self.get_class_group_display()}, {self.get_scholar_type_display()})"


class Student(models.Model):
    class Gender(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"

    class BoardingStatus(models.TextChoices):
        DAY = "DAY", "Day Scholar"
        BOARDING = "BOARDING", "Boarding Scholar"

    class Religion(models.TextChoices):
        CATHOLIC = "CATHOLIC", "Catholic"
        PROTESTANT = "PROTESTANT", "Protestant / Anglican"
        MUSLIM = "MUSLIM", "Muslim"
        PENTECOSTAL = "PENTECOSTAL", "Pentecostal / Born Again"
        SDA = "SDA", "Seventh-Day Adventist"
        ORTHODOX = "ORTHODOX", "Orthodox"
        OTHER = "OTHER", "Other"

    admission_number = models.CharField(max_length=20, unique=True, editable=False)
    photo = models.ImageField(upload_to="student_photos/", blank=True, null=True)
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
    former_school = models.CharField(max_length=200, blank=True, help_text="Previous school attended, if any.")
    religion = models.CharField(max_length=20, choices=Religion.choices, blank=True)
    nin = models.CharField(
        max_length=14,
        blank=True,
        validators=[uganda_nin_validator],
        verbose_name="Guardian NIN (optional)",
        help_text="14 characters beginning with CM or CF, for example CM4900906P76ZE.",
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
        self.nin = (self.nin or "").strip().upper()
        if not self.admission_number:
            self.admission_number = self._generate_admission_number()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_admission_number():
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


class StudentRequirement(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="requirement_records")
    requirement = models.ForeignKey(Requirement, on_delete=models.CASCADE, related_name="student_records")
    term = models.CharField(max_length=10)
    year = models.PositiveIntegerField()
    brought = models.BooleanField(default=False)
    brought_on = models.DateField(null=True, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        unique_together = ("student", "requirement", "term", "year")
        ordering = ["student", "requirement"]
