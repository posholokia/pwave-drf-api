# Generated by Django 4.2.8 on 2023-12-30 16:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0006_remove_task_color_mark_remove_task_name_mark_sticker'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sticker',
            name='task',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sticker', to='workspaces.task'),
        ),
    ]