# Generated by Django 4.2.9 on 2024-01-26 15:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0008_alter_sticker_color'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='deadline',
            field=models.DateTimeField(null=True, verbose_name='Срок выполнения'),
        ),
    ]
