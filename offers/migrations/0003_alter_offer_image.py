# Generated by Django 5.1.4 on 2025-01-05 17:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('offers', '0002_alter_offer_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='offer',
            name='image',
            field=models.FileField(null=True, upload_to='uploads/'),
        ),
    ]
