# Generated by Django 4.2.5 on 2023-11-24 14:43

from django.db import migrations, models
import pulsewave.validators


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_alter_user_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='avatar',
            field=models.ImageField(default=None, null=True, upload_to='avatars/', verbose_name='Аватар'),
        ),
        migrations.AlterField(
            model_name='user',
            name='name',
            field=models.CharField(blank=True, max_length=50, validators=[pulsewave.validators.validate_name], verbose_name='Имя пользователя'),
        ),
    ]
