from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

## пример реализации вывода в качестве имени пользователя его имени, если оно есть или почты если нет
# class UserSerializer(serializers.ModelSerializer):
#     name = serializers.SerializerMethodField()
#
#     class Meta:
#         model = User
#         fields = tuple(User.REQUIRED_FIELDS) + ("password",)
#
#     def get_name(self, obj):
#         return obj.email if obj.email else 'randomname'
