from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def add_requirements(apps, schema_editor):
    Requirement = apps.get_model("students", "Requirement")
    groups = {
        "NURSERY_P3": [
            "4 toilet rolls", "2 brooms", "Book covers", "6 pencils / pens", "1 packet of crayons",
            "2 manila papers", "1 bucket of detergent", "1 cutter", "1 ream of paper",
            "12 exercise books (Picfare 96 pages)",
        ],
        "P4_P7": [
            "1 ream of paper", "4 toilet rolls", "2 brooms", "1 mathematics set",
            "1 bucket of detergent", "Atlas", "Dictionary", "Enough books and pens",
        ],
    }
    for group, names in groups.items():
        for name in names:
            Requirement.objects.get_or_create(name=name, class_group=group)


class Migration(migrations.Migration):
    dependencies = [("students", "0006_alter_student_nin"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="Requirement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150)),
                ("class_group", models.CharField(choices=[("NURSERY_P3", "Nursery - P3"), ("P4_P7", "P4 - P7")], max_length=20)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"ordering": ["class_group", "id"], "unique_together": {("name", "class_group")}},
        ),
        migrations.CreateModel(
            name="StudentRequirement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("term", models.CharField(max_length=10)),
                ("year", models.PositiveIntegerField()),
                ("brought", models.BooleanField(default=False)),
                ("brought_on", models.DateField(blank=True, null=True)),
                ("recorded_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("requirement", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="student_records", to="students.requirement")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="requirement_records", to="students.student")),
            ],
            options={"ordering": ["student", "requirement"], "unique_together": {("student", "requirement", "term", "year")}},
        ),
        migrations.RunPython(add_requirements, migrations.RunPython.noop),
    ]
