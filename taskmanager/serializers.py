from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserModelSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'subscriber',
            'name',
        )

    def get_name(self, obj):
        return obj.presentation_name()
