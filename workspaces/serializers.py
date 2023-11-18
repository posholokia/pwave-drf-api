from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import WorkSpace

User = get_user_model()


class CreateWorkSpaceSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = WorkSpace
        fields = (
            'owner',
            'name',
        )

    def create(self, validated_data):
        instance = super().create(validated_data)
        user = validated_data.get('owner')
        instance.users.add(user)
        return instance


class WorkSpaceSerializer(serializers.ModelSerializer):
    users = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True,
        many=True
    )

    class Meta:
        model = WorkSpace
        fields = (
            'users',
            'name',
        )


class WorkSpaceInviteSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()

    class Meta:
        model = WorkSpace
        fields = (
            'id',
            'email',
        )
