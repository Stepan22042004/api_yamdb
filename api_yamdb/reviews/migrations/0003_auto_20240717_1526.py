# Generated by Django 3.2 on 2024-07-17 12:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0002_auto_20240717_1507'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='customuser',
            managers=[
            ],
        ),
        migrations.AddField(
            model_name='customuser',
            name='confirmation_code',
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
    ]
