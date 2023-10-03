from rest_framework import serializers
from .models import AttendanceModel, UserModel


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = '__all__'

class AttendanceSerializer(serializers.ModelSerializer):
    user_data = UserSerializer(many=True, read_only=True)
    class Meta:
        model = AttendanceModel
        fields = ['user_roll', 'persent', 'date', 'user_data']