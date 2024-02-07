# Generated by Django 4.2.9 on 2024-01-18 17:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('workspaces', '0008_alter_sticker_color'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=256, verbose_name='Текст сообщения')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Время создания')),
                ('read', models.BooleanField(default=False, verbose_name='Прочитано')),
                ('board', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='board_notifications', to='workspaces.board')),
                ('recipients', models.ManyToManyField(related_name='notification', to=settings.AUTH_USER_MODEL)),
                ('workspace', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ws_notifications', to='workspaces.workspace')),
            ],
        ),
    ]