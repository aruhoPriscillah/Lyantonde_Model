from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("academics", "0006_add_all_class_subjects"),
    ]

    operations = [
        migrations.CreateModel(
            name="AcademicTerm",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("term", models.CharField(choices=[("TERM1", "Term 1"), ("TERM2", "Term 2"), ("TERM3", "Term 3")], max_length=10)),
                ("year", models.PositiveIntegerField()),
                ("opens_on", models.DateField()),
                ("closes_on", models.DateField()),
                ("is_closed", models.BooleanField(default=False)),
            ],
            options={
                "ordering": ["-year", "term"],
                "unique_together": {("term", "year")},
            },
        ),
    ]
