from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("tenancy", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="business",
            name="plan",
            field=models.CharField(
                choices=[
                    ("free", "Free"),
                    ("professional", "Professional"),
                    ("enterprise", "Enterprise"),
                ],
                default="free",
                max_length=20,
            ),
        ),
    ]
