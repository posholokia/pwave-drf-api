# Generated by Django 4.2.8 on 2023-12-29 17:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0005_alter_column_index_alter_task_index'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='task',
            name='color_mark',
        ),
        migrations.RemoveField(
            model_name='task',
            name='name_mark',
        ),
        migrations.CreateModel(
            name='Sticker',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32, verbose_name='Название стикера')),
                ('color', models.CharField(max_length=7, verbose_name='Цвет')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workspaces.task')),
            ],
        ),
    ]
