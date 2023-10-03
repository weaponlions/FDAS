from django.urls import path
from .  import views

urlpatterns = [
    # path('registerform.html', views.registerformPage),
    path('registerformData.html', views.registerUserData),
    path('takeattendance.html', views.takeAttendancePage),
    path('attendance.html', views.takeAttendance),
    path('todayList.html', views.TodayList),
    path('calender.html', views.takeAttendance),
    path('getAttendanceData.html', views.getAttendanceData),

    path('userList.html', views.userList),
    path('userUpdate.html', views.userUpdate),
    path('userDelete.html', views.userDelete),
    path('userProfile.html', views.userProfile),
    path('userFaceUpdate.html', views.userFaceUpdate),

    path('', views.adminIndex),
    path('adminLogin.html', views.adminLogin),
    path('adminStudent.html', views.adminStudent),
    path('adminSign.html', views.adminSign),
    path('adminFaceLogin.html', views.adminFaceLogin),
    path('adminSignUp.html', views.adminSignUp),
    path('adminFaceUpdate.html', views.adminFaceUpdate),

    path('logout.html', views.Userlogout),
    path('getChartData.html', views.getChartData),
    # path('genUser.html', views.gen),
]