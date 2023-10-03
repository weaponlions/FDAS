from django.contrib import admin
from . import models
# Register your models here.

admin.site.register(models.DayModel)
admin.site.register(models.UserModel)
admin.site.register(models.AttendanceModel)