from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("students", "0008_requirement_scholar_type_and_boarding_items"),
    ]

    operations = [
        migrations.AddField(
            model_name="student",
            name="lin",
            field=models.CharField(
                blank=True,
                help_text="Learner Identification Number, if available.",
                max_length=30,
                null=True,
                unique=True,
                verbose_name="LIN (optional)",
            ),
        ),
    ]
