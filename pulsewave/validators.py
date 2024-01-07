import re

from django.core.exceptions import ValidationError
import string


class UppercaseLetterPasswordValidator:
    """
    Проверка, что в пароле есть минимум одна заглавная буква.
    """

    def validate(self, password, user=None):
        if not any(char.isupper() for char in password):
            raise ValidationError("Пароль должен содержать хотя бы одну букву в верхнем регистре.")

    def get_help_text(self):
        return "В пароле должна содержаться хотя бы одна строчная буква."


class LowercaseLetterPasswordValidator:
    """
    Проверка, что в пароле есть минимум одна строчная буква.
    """

    def validate(self, password, user=None):
        if not any(char.islower() for char in password):
            raise ValidationError("Пароль должен содержать хотя бы одну букву в нижнем регистре.")

    def get_help_text(self):
        return "В пароле должна содержаться хотя бы одна строчная буква."


class IncludeNumberPasswordValidator:
    """
    Проверка, что в пароле есть минимум одна цифра.
    """

    def validate(self, password, user=None):
        if not any(char.isdigit() for char in password):
            raise ValidationError("Пароль должен содержать хотя бы одну цифру.")

    def get_help_text(self):
        return "Пароль не может быть без цифр."


class SpecialCharacterPasswordValidator:
    """
    Проверка, что в пароле есть минимум один специальный символ.
    """

    def validate(self, password, user=None):
        special_characters = r"!@#$%^&*-_+=[](){}|;:\,.<>?"
        if not any(char in special_characters for char in password):
            raise ValidationError("Пароль должен содержать хотя бы один специальный символ.")

    def get_help_text(self):
        return r"Пароль должен содержать минимум один специальный символ: !@#$%^&*-_+[]{}|;:\,.<>?"


def validate_name(name):
    union_string = ('.-_ '
                   f'{string.ascii_letters}'
                   f'{string.digits}'
                   'абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ')

    if not all(char in union_string for char in name):
        raise ValidationError(f'Имя может содержать буквы строчные и заглавные, цифры,'
                              f' символы (.-_), русский или латинский алфавит.')


def validate_sticker_color(name):
    color_pattern = re.compile(r'^#(?:[0-9a-fA-F]{3}){1,2}$')
    if not color_pattern.match(name):
        raise ValidationError(
            'Может содержать только HEX обозначение цвета, например: #159ACF'
        )
