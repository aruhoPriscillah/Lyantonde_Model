from django.db import migrations


def add_lower_primary_subjects(apps, schema_editor):
    Subject = apps.get_model("academics", "Subject")
    for name in (
        "Mathematics",
        "English",
        "Literacy I",
        "Literacy II (Reading)",
        "Religious Education",
        "Luganda",
    ):
        Subject.objects.get_or_create(name=name)


class Migration(migrations.Migration):
    dependencies = [("academics", "0004_alter_result_remarks")]
    operations = [migrations.RunPython(add_lower_primary_subjects, migrations.RunPython.noop)]
