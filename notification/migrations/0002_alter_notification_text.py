# Generated by Django 4.2.9 on 2024-02-03 17:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='text',
            field=models.TextField(verbose_name='Текст сообщения'),
        ),
    ]
