# Generated by Django 4.2.9 on 2024-01-31 17:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0010_comment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='name',
            field=models.CharField(max_length=200, verbose_name='Название задачи'),
        ),
    ]