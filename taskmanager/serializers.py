from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class CurrentUserSerializer(serializers.ModelSerializer):
    """
    Сериализатор пользователя, используется вместо стандартного Djoser current_user сериализатора.
    Сериализует данные авторизованного пользователя в его профиле.
    """
    class Meta:
        model = User
        read_only_fields = ['email']
        fields = (
            'id',
            'email',
            'name',
        )


class UserListSerializer(serializers.ModelSerializer):  # на будущее
    """
    Сериализатор для представления списка пользователей при добавлении их в рабочее пространство.
    Десериализует имя из БД и представляет его в необходимой форме. Способ представления
    реализован в методе presentation_name модели User.
    """
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('name',)

    def get_name(self, obj):
        return obj.presentation_name()

