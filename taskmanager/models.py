from django.db import models
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser
from .managers import UserManager
from pulsewave import settings
from pulsewave.validators import validate_name


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField('Эл. почта', unique=True)
    date_joined = models.DateTimeField('Дата создания', auto_now_add=True)
    is_active = models.BooleanField('Активирован', default=True)  # обязательно
    is_staff = models.BooleanField('Персонал', default=False)  # для админ панели

    subscriber = models.BooleanField('Подписан на рассылки', default=False)
    name = models.CharField('Имя пользователя', max_length=50, blank=True, validators=[validate_name])

    objects = UserManager()  # используется кастомный менеджер юзера

    USERNAME_FIELD = 'email'  # поле, используемое в качестве логина
    REQUIRED_FIELDS = ['subscriber']  # дополнительные поля при регистрации

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def representation_name(self):
        """
        Способ представления имени пользователя в списке пользователей
        """
        if self.name:
            return f'{self.name}({self.email.split("@")[0]})'
        else:
            return self.email
