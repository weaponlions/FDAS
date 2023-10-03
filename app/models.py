from django.db import models

# Create your models here.
class UserModel(models.Model):
    name = models.CharField(null=False, max_length=255)
    roll_number = models.CharField(null=False, unique=True, max_length=20, primary_key=True)
    class_name = models.CharField(null=False, max_length=255)
    profile_img = models.CharField(null=True, blank=True, max_length=255, unique=True)
    date = models.DateField(auto_now=True)
    time = models.TimeField(auto_now=True)


class AttendanceModel(models.Model):
    user_roll = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name="user_data")
    persent = models.BooleanField(blank=False, default=False)
    date = models.DateField(auto_now=True)
    time = models.TimeField(auto_now=True)


class DayModel(models.Model):
    holiday = models.BooleanField(blank=False, default=False)
    date = models.DateTimeField(editable=False)