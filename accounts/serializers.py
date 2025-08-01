from rest_framework import serializers
from .models import CustomUser

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'password', 'full_name', 'phone_number']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'full_name', 'phone_number']
