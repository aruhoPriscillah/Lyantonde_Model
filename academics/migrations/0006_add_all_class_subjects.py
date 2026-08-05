from django.db import migrations


def add_class_subjects(apps, schema_editor):
    Subject = apps.get_model("academics", "Subject")
    for name in (
        "Numbers",
        "English",
        "Reading",
        "Health Habits",
        "Social Development",
        "Drawing",
        "Writing",
        "Mathematics",
        "Literacy I",
        "Literacy II (Reading)",
        "Religious Education",
        "Luganda",
        "SST",
        "Science",
    ):
        Subject.objects.get_or_create(name=name)


class Migration(migrations.Migration):
    dependencies = [("academics", "0005_add_lower_primary_subjects")]
    operations = [migrations.RunPython(add_class_subjects, migrations.RunPython.noop)]
