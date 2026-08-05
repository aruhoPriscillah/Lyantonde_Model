from django.db import migrations, models


def add_boarding_requirements(apps, schema_editor):
    Requirement = apps.get_model("students", "Requirement")
    common = [
        "Bible (Good News)",
        "Mattress, blanket, pillow, 2 pairs of bed sheets and mosquito net",
        "Cup, plate, spoon and fork",
        "Report from previous school (newcomers)",
        "School uniform",
        "School bag",
        "At least 5 knickers / underpants",
        "Night dresses",
        "Toothpaste and toothbrushes",
        "Shoe polish and shoe polisher",
        "Torch",
        "Bathing and washing soap (3 bars)",
        "Metallic suitcase",
        "12 counter books for each subject (2 quires), pens and pencils",
        "A textbook in each subject",
        "1 pair of slippers / sandals",
        "Sanitary pads - 3 packets (girls only)",
        "Knife (girls only)",
        "1 pack of razor blades",
        "Black shoes and grey stockings with blue stripes",
        "1 ream of paper",
        "3 kg of sugar",
    ]
    by_group = {
        "NURSERY_P3": common + ["Geometry set (P3)"],
        "P4_P7": common + ["Geometry set", "Dictionary (P5-P7)", "Atlas (P5-P7)"],
    }
    for class_group, names in by_group.items():
        for name in names:
            Requirement.objects.get_or_create(
                name=name, class_group=class_group, scholar_type="BOARDING"
            )


class Migration(migrations.Migration):
    dependencies = [("students", "0007_requirement_studentrequirement")]
    operations = [
        migrations.AddField(
            model_name="requirement",
            name="scholar_type",
            field=models.CharField(
                choices=[("DAY", "Day Scholar"), ("BOARDING", "Boarding Scholar")],
                default="DAY", max_length=10,
            ),
        ),
        migrations.AlterUniqueTogether(
            name="requirement",
            unique_together={("name", "class_group", "scholar_type")},
        ),
        migrations.AlterModelOptions(
            name="requirement",
            options={"ordering": ["scholar_type", "class_group", "id"]},
        ),
        migrations.RunPython(add_boarding_requirements, migrations.RunPython.noop),
    ]
