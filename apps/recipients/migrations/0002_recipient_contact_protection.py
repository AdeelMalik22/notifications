from django.db import migrations, models


def protect_existing_contacts(apps, schema_editor):
    from apps.recipients.privacy import contact_lookup, encrypt_contact

    Recipient = apps.get_model("recipients", "Recipient")
    for recipient in Recipient.objects.all().iterator():
        updates = {}
        if recipient.email:
            updates["email_ciphertext"] = encrypt_contact(recipient.email)
            updates["email_lookup"] = contact_lookup(recipient.email)
            updates["email"] = ""
        if recipient.phone_number:
            updates["phone_ciphertext"] = encrypt_contact(recipient.phone_number)
            updates["phone_lookup"] = contact_lookup(recipient.phone_number)
            updates["phone_number"] = ""
        if updates:
            Recipient.objects.filter(pk=recipient.pk).update(**updates)


class Migration(migrations.Migration):
    dependencies = [("recipients", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="recipient",
            name="email_ciphertext",
            field=models.BinaryField(blank=True, default=bytes),
        ),
        migrations.AddField(
            model_name="recipient",
            name="email_lookup",
            field=models.CharField(blank=True, editable=False, max_length=64),
        ),
        migrations.AddField(
            model_name="recipient",
            name="phone_ciphertext",
            field=models.BinaryField(blank=True, default=bytes),
        ),
        migrations.AddField(
            model_name="recipient",
            name="phone_lookup",
            field=models.CharField(blank=True, editable=False, max_length=64),
        ),
        migrations.RunPython(protect_existing_contacts, migrations.RunPython.noop),
    ]
