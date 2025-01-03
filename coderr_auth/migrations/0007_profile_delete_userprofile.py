# Generated by Django 5.1.4 on 2025-01-03 14:45

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coderr_auth', '0006_alter_userprofile_location'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('username', models.CharField(default='max_mustermann', max_length=150)),
                ('type', models.CharField(choices=[('business', 'business'), ('customer', 'customer')], max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('first_name', models.CharField(default='Max', max_length=100)),
                ('last_name', models.CharField(default='Mustermann', max_length=100)),
                ('file', models.FileField(blank=True, null=True, upload_to='uploads/')),
                ('location', models.CharField(default='Lappland', max_length=100)),
                ('description', models.TextField(default='Lappland Business', max_length=1000)),
                ('working_hours', models.CharField(default='8 - 16', max_length=100)),
                ('tel', models.CharField(default='0123456789', max_length=100)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.DeleteModel(
            name='UserProfile',
        ),
    ]
