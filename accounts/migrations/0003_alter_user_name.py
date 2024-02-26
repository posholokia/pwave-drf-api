# Generated by Django 4.2.5 on 2023-11-24 14:41

from django.db import migrations, models
import pulsewave.validators


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_user_name_user_subscriber'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='name',
            field=models.CharField(blank=True, max_length=40, validators=[pulsewave.validators.validate_name], verbose_name='Имя пользователя'),
        ),
    ]
