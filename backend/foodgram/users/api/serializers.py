from djoser.serializers import (
    UserCreateSerializer as BaseUserRegistrationSerializer
)
from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework import serializers

from recipes.models import Follow


class UserRegistrationSerializer(BaseUserRegistrationSerializer):
    class Meta(BaseUserRegistrationSerializer.Meta):
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'password', )


class UserDetailSerializer(BaseUserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        return Follow.objects.filter(
            user=self.context['request'].user.id,
            following=obj.id
        ).exists()

    class Meta(BaseUserSerializer.Meta):
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'is_subscribed', )
