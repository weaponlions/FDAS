from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
import cv2, cvzone, pickle, asyncio, math, json
import face_recognition, datetime, os, numpy as np
from .models import UserModel, AttendanceModel
from asgiref.sync import sync_to_async, async_to_sync
from django.db import IntegrityError
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from datetime import timedelta
# Create your views here.

global cam_num
cam_num = 0

def get_face_location(img):
    face_loc = face_recognition.face_locations(img)
    return face_loc

async def generate_face_enc(request, img, face_loc, roll, name, profile_img):
    try:
        model = sync_to_async(UserModel.objects.create)(name=name, roll_number=roll, class_name="10", profile_img=profile_img)
        await model
    except IntegrityError as e:
        pass
    face_enc = face_recognition.face_encodings(img, face_loc)
    with open('Face/Encoding.pt', 'ab') as f:
        pickle.dump(face_enc[0], f)
    with open('Face/Mapping.pt', 'ab') as f:
        pickle.dump(roll, f)

@sync_to_async
def old_user(roll):
    return list(UserModel.objects.filter(roll_number=roll))


async def registerUserData(request):
    name = request.GET.get('userName', None)
    roll = request.GET.get('userRoll', None)
    if roll is not None and name is not None:
        user = await old_user(roll)
        if len(user) >= 1:
            return JsonResponse({'code': 'already'})
    else:
        return JsonResponse({'code': 'parameter_error'})

    profile_img = ""
    cam = cv2.VideoCapture(cam_num)
    step = 0
    task = ''
    manual_quite = False
    while True:
        __, img = cam.read()
        img = cv2.resize(img, (0, 0), None, 0.6, 0.6)
        resize_img = cv2.resize(img, (0, 0), None, 0.50, 0.50)
        resize_img = cv2.cvtColor(resize_img, cv2.COLOR_BGR2RGB)
        face_loc = get_face_location(resize_img)
        if len(face_loc) == 1:
            if os.path.isfile("static/user_image/{}.jpg".format(roll)) is not True:
                cv2.imwrite("static/user_image/{}.jpg".format(roll), img)

            profile_img = "user_image/{}.jpg".format(roll)
            step += 1
            task = asyncio.create_task(generate_face_enc(request, resize_img, face_loc, roll, name, profile_img))
            y1, x2, y2, x1 = face_loc[0]
            y1, x2, y2, x1 = (y1*2, x2*2, y2*2, x1*2)
            img = cvzone.cornerRect(img, (x1, y1, x2-x1, y2-y1), l=20, t=3, rt=0)
            cvzone.putTextRect(img, "{}_{}".format(name, roll), (x1, y1), scale=1, thickness=1)
        cv2.imshow('Camera', img)
        cv2.setWindowProperty('Camera', cv2.WND_PROP_TOPMOST, 1)
        if cv2.waitKey(100) & 0xFF == ord('q'):
            manual_quite = True
            break
        if step >= 5:
            break

    cam.release()
    cv2.destroyAllWindows()
    if manual_quite == True:
        return JsonResponse({'code': 'manual'})
    if task != "":
        await task
    return JsonResponse({'code': 'done'})

def registerformPage(request):
    return render(request, "app/templates/register.html")

def takeAttendance(request):
    calender = request.GET.get('calender', None)
    if calender is not None:
        return render(request, "app/templates/calender.html", {'user': 'user'})
    face_lst = []
    with open('Face/Encoding.pt', 'rb') as f:
        while True:
            try:
                face_lst.append(pickle.load(f))
            except EOFError:
                break
    face_roll = []
    with open('Face/Mapping.pt', 'rb') as f:
        while True:
            try:
                face_roll.append(pickle.load(f))
            except EOFError:
                break

    cam = cv2.VideoCapture(cam_num)
    attend = 0
    attend_roll = ""
    attemp = 0
    manual_quite = False
    already = False
    data = ""
    frame = "Camera"
    cv2.namedWindow(frame)
    cv2.moveWindow(frame, 800, 210)
    while True:
        __, img = cam.read()
        img = cv2.resize(img,  (0, 0), None, 0.6, 0.6)
        resize_img = cv2.resize(img, (0, 0), None, 0.40, 0.40)
        resize_img = cv2.cvtColor(resize_img, cv2.COLOR_BGR2RGB)
        face_loc = get_face_location(resize_img)
        if len(face_loc) == 1:
            attemp += 1
            face_enc = face_recognition.face_encodings(resize_img, face_loc)
            lst_dis = face_recognition.face_distance(face_lst, face_enc[0])
            lst_com = face_recognition.compare_faces(face_lst, face_enc[0])
            if len(lst_dis) == 0:
                cam.release()
                cv2.destroyAllWindows()
                return JsonResponse({'code': 'zero', 'user': None})
            index = np.argmin(lst_dis)
            if lst_com[index] == True and lst_dis[index] < 0.5:
                roll = face_roll[index]
                model = UserModel.objects.filter(roll_number=roll).values()
                print(model)
                print(len(model))
                if len(model) > 0:
                    name = model[0].get('name')
                if attend == 0:
                    attend_roll = roll
                if attend_roll == roll:
                    attend +=1
                else:
                    attend_roll = roll
                    attend = 1
                if attend > 5:
                    user = UserModel.objects.get(roll_number=attend_roll)
                    previous = AttendanceModel.objects.filter(user_roll=user, date=datetime.date.today()).values()
                    data = user
                    if calender == "True":
                        cam.release()
                        cv2.destroyAllWindows()
                        # request.session['user_key'] = user.roll_number
                        return render(request, "app/templates/calender.html", {'user': user})
                    if len(previous) == 0:
                        model = AttendanceModel.objects.create(user_roll=user, persent=True)
                        model.save()
                        break
                    else:
                        already = True
                        break
            else:
                name = "Unknown"
                roll = "Person"
            y1, x2, y2, x1 = face_loc[0]
            y1, x2, y2, x1 = (math.floor(y1*2.5), math.floor(x2*2.5), math.floor(y2*2.5), math.floor(x1*2.5))
            img = cvzone.cornerRect(img, (x1, y1, x2-x1, y2-y1), l=20, t=3, rt=0)
            cvzone.putTextRect(img, "{}_{}".format(name, roll), (x1, y1), scale=1, thickness=1)

            if attemp > 40:
                break
        cv2.imshow(frame, img)
        cv2.setWindowProperty(frame, cv2.WND_PROP_TOPMOST, 1)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            manual_quite = True
            break
    cam.release()
    cv2.destroyAllWindows()
    data = data.__dict__
    data = {
        'profile_img':  data['profile_img'],
        'userName':  data['name'],
        'userRoll': data['roll_number']
    }
    if already == True:
        return JsonResponse({'code': 'already', 'user': data})
    if attemp > 40 or manual_quite == True:
        return JsonResponse({'code': 'err'})
    else:
        return JsonResponse({'code': 'done', 'user': data})

def takeAttendancePage(request):
    # day = datetime.date.today().weekday()
    # day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    holiday = True
    # if day_name[day] == 'Sunday':
    #     holiday = True
    return render(request, "app/templates/takeAttendance.html", {'holiday': holiday })


def TodayList(request):
    today_date = datetime.date.today()

    today_list = AttendanceModel.objects.filter(date=today_date).select_related('user_roll')
    data = []
    for list in today_list:
        user_data = {
            'name': list.user_roll.name,
            'roll_number': list.user_roll.roll_number,
            'class_name': list.user_roll.class_name,
            'profile_img': list.user_roll.profile_img,
            'date': list.date,
            'time': list.time,
            'persent': list.persent
        }
        data.append(user_data)

    return JsonResponse({'results': data}, safe=False)
 
    

def userList(request):
    search = (request.GET.get('search', None))
    page = int (request.GET.get('page', 1))
    limit = int (request.GET.get('limit', 10))
    data = {}
    start_index = (page - 1) * limit
    end_index = (page) * limit
    if search is None:
        model = UserModel.objects.all()
    else:
        model = UserModel.objects.filter(name=search)
    total_page = math.ceil(model.count()/limit)
    data['result'] = list((model[start_index : end_index]).values())
    data['current_page'] = page
    data['total_page'] = total_page
    return JsonResponse(data, safe=False)

def gen(request):
    data = [
        # {'name': "Harsit", 'roll_number': 3, 'class_name': 10, 'profile_img': ""},
        {'name': "Rohit", 'roll_number': 4, 'class_name': 10, 'profile_img': ""},
        {'name': "Neha", 'roll_number': 5, 'class_name': 10, 'profile_img': ""},
        {'name': "Nisha", 'roll_number': 6, 'class_name': 10, 'profile_img': ""},
        {'name': "Deepak", 'roll_number': 7, 'class_name': 10, 'profile_img': ""},
        {'name': "Divakar", 'roll_number': 8, 'class_name': 10, 'profile_img': ""},
        {'name': "Rahul", 'roll_number': 9, 'class_name': 10, 'profile_img': ""},
        {'name': "Nitin", 'roll_number': 10, 'class_name': 10, 'profile_img': ""},
        {'name': "Abhi", 'roll_number': 11, 'class_name': 10, 'profile_img': ""},
        {'name': "Mukesh", 'roll_number': 12, 'class_name': 10, 'profile_img': ""},
        {'name': "Dev", 'roll_number': 13, 'class_name': 10, 'profile_img': ""},
        {'name': "Vansh", 'roll_number': 14, 'class_name': 10, 'profile_img': ""},
        {'name': "Sandeep", 'roll_number': 15, 'class_name': 10, 'profile_img': ""},
    ] 
    for i in data:
        model = UserModel.objects.create(name=i['name'], roll_number=i['roll_number'], class_name=i['class_name'], profile_img=("{}.jpg".format(i['roll_number'])))
        model.save()
        
    return JsonResponse({'mes': 'Done'})


@csrf_exempt
def userUpdate(request):
    post_data = json.loads(request.body.decode("utf-8"))
    roll_number = post_data.get('roll_number', None)
    if roll_number is None:
        return JsonResponse({'code': 'parameter_error'})
    user = UserModel.objects.get(roll_number=roll_number)
    name = post_data.get('name', None)
    if user and name is not None:
        user.name = name
        user.save()
        return JsonResponse({'code': 'done'})
    else:
        return JsonResponse({'code': 'invalid'})


@csrf_exempt
def userDelete(request):
    post_data = json.loads(request.body.decode("utf-8"))
    roll_number = post_data.get('roll_number', None)
    if roll_number is None:
        return JsonResponse({'code': 'parameter_error'})
    user = UserModel.objects.get(roll_number=roll_number)
    if user:
        user.delete()
        return JsonResponse({'code': 'done'})
    else:
        return JsonResponse({'code': 'invalid'})



@csrf_exempt
def userProfile(request):
    post_data = json.loads(request.body.decode("utf-8"))
    roll_number = post_data.get('roll_number', None)
    if roll_number is None:
        return JsonResponse({'code': 'parameter_error'})
    user = UserModel.objects.filter(roll_number=roll_number).values()
    return JsonResponse({'result': list(user)})


def adminIndex(request):
    today_date = datetime.date.today()
    if request.user.is_authenticated:
        total_student = UserModel.objects.all().count()
        today = AttendanceModel.objects.filter(date= today_date).count()
        weakly = AttendanceModel.objects.filter(date__gte= (today_date - timedelta(days = 7)), date__lte = today_date).count()
        monthly = AttendanceModel.objects.filter(date__gte= (today_date - timedelta(days = 30)), date__lte = today_date).count()
        return render(request, 'app/templates/pages/index.html', {'total_student': total_student, 'today': today, 'weakly': weakly, 'monthly': monthly})
    else:
        return render(request, 'app/templates/pages/login.html')

def adminLogin(request):
    if request.user.is_authenticated:
        return redirect(request.META.get('HTTP_REFERER'))
    else:
        return render(request, 'app/templates/pages/login.html')


def adminStudent(request):
    if request.user.is_authenticated:
        return render(request, 'app/templates/pages/student.html')
    else:
        return render(request, 'app/templates/pages/login.html')

@csrf_exempt
def adminSign(request):
    post_data = json.loads(request.body.decode("utf-8"))
    user = authenticate(request, username=post_data['username'], password=post_data['password'])
    if user is not None:
        login(request, user)
        return JsonResponse({'code': 'done'})
    print(user)
    return JsonResponse({'code': 'err'})

def Userlogout(request):
    logout(request)
    return render(request, 'app/templates/pages/login.html')



async def generate_admin_enc(request, img, face_loc, username, password):
    try:
        model = sync_to_async(User.objects.create_user)(username=username, password=password)
        await model
    except IntegrityError as e:
        pass
    face_enc = face_recognition.face_encodings(img, face_loc)
    with open('Face/AdminEncoding.pt', 'ab') as f:
        pickle.dump(face_enc[0], f)
    with open('Face/AdminMapping.pt', 'ab') as f:
        pickle.dump(username, f)

@sync_to_async
def old_adminUser(username):
    exist = list(User.objects.all())
    if len(exist) < 2:
        return list(User.objects.filter(username=username))
    else:
        return exist

async def adminSignUp(request):
    username = request.GET.get('username', None)
    password = request.GET.get('password', None)
    if username is not None and password is not None:
        user = await old_adminUser(username)
        if len(user) >= 1:
            return JsonResponse({'code': 'already'})
    else:
        return JsonResponse({'code': 'parameter_error'})
    cam = cv2.VideoCapture(cam_num)
    step = 0
    manual_quite = False
    while True:
        __, img = cam.read()
        img = cv2.resize(img, (0, 0), None, 0.6, 0.6)
        resize_img = cv2.resize(img, (0, 0), None, 0.50, 0.50)
        resize_img = cv2.cvtColor(resize_img, cv2.COLOR_BGR2RGB)
        face_loc = get_face_location(resize_img)
        if len(face_loc) == 1:
            step += 1
            task = asyncio.create_task(generate_admin_enc(request, resize_img, face_loc, username, password))
            y1, x2, y2, x1 = face_loc[0]
            y1, x2, y2, x1 = (y1 * 2, x2 * 2, y2 * 2, x1 * 2)
            img = cvzone.cornerRect(img, (x1, y1, x2 - x1, y2 - y1), l=20, t=3, rt=0)
            cvzone.putTextRect(img, "{}".format(username), (x1, y1), scale=1, thickness=1)
        cv2.imshow('Camera', img)
        cv2.setWindowProperty('Camera', cv2.WND_PROP_TOPMOST, 1)
        if cv2.waitKey(100) & 0xFF == ord('q'):
            manual_quite = True
            break
        if step >= 5:
            break
    cam.release()
    cv2.destroyAllWindows()
    if manual_quite == True:
        return JsonResponse({'code': 'manual'})
    if task != "":
        await task
    return JsonResponse({'code': 'done'})


def adminFaceLogin(request):
    face_lst = []
    with open('Face/AdminEncoding.pt', 'rb') as f:
        while True:
            try:
                face_lst.append(pickle.load(f))
            except EOFError:
                break
    face_name = []
    with open('Face/AdminMapping.pt', 'rb') as f:
        while True:
            try:
                face_name.append(pickle.load(f))
            except EOFError:
                break

    cam = cv2.VideoCapture(cam_num)
    attend = 0
    attemp = 0
    manual_quite = False
    attend_user = ""
    frame = "Camera"
    cv2.namedWindow(frame)
    cv2.moveWindow(frame, 800, 210)
    while True:
        __, img = cam.read()
        img = cv2.resize(img, (0, 0), None, 0.6, 0.6)
        resize_img = cv2.resize(img, (0, 0), None, 0.40, 0.40)
        resize_img = cv2.cvtColor(resize_img, cv2.COLOR_BGR2RGB)
        face_loc = get_face_location(resize_img)
        if len(face_loc) == 1:
            attemp += 1
            face_enc = face_recognition.face_encodings(resize_img, face_loc)
            lst_dis = face_recognition.face_distance(face_lst, face_enc[0])
            lst_com = face_recognition.compare_faces(face_lst, face_enc[0])
            index = np.argmin(lst_dis)
            if lst_com[index] == True and lst_dis[index] < 0.5:
                username = face_name[index]
                name = username
                if attend == 0:
                    attend_user = username
                if attend_user == username:
                    attend += 1
                else:
                    attend_user = username
                    attend = 1
                if attend > 7:
                    user = User.objects.get(username=username)
                    login(request, user)
                    break
            else:
                name = "Unknown Person"
            y1, x2, y2, x1 = face_loc[0]
            y1, x2, y2, x1 = (math.floor(y1 * 2.5), math.floor(x2 * 2.5), math.floor(y2 * 2.5), math.floor(x1 * 2.5))
            img = cvzone.cornerRect(img, (x1, y1, x2 - x1, y2 - y1), l=20, t=3, rt=0)
            cvzone.putTextRect(img, "{}".format(name), (x1, y1), scale=1, thickness=1)

            if attemp > 40:
                break
        cv2.imshow(frame, img)
        cv2.setWindowProperty(frame, cv2.WND_PROP_TOPMOST, 1)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            manual_quite = True
            break
    cam.release()
    cv2.destroyAllWindows()
    if attemp > 40 or manual_quite == True:
        return JsonResponse({'code': 'err'})
    else:
        return JsonResponse({'code': 'done'})


def adminFaceUpdate(request):
    if request.user.is_authenticated:
        username = request.user.username
        face_lst = []
        with open('Face/AdminEncoding.pt', 'rb') as f:
            while True:
                try:
                    face_lst.append(pickle.load(f))
                except EOFError:
                    break
            with open('Face/AdminEncoding.pt', 'w') as f:
                f.close()
        face_name = []
        with open('Face/AdminMapping.pt', 'rb') as f:
            while True:
                try:
                    face_name.append(pickle.load(f))
                except EOFError:
                    break
            with open('Face/AdminMapping.pt', 'w') as f:
                f.close()
        lst_index = []
        for i in range(len(face_name)):
            if face_name[i] == username:
                lst_index.append(i)

        fac_step = len(lst_index)
        update_face = False
        if fac_step > 0:
            update_face = True
        else:
            fac_step = 5
        cam = cv2.VideoCapture(cam_num)
        while True:
            __, img = cam.read()
            img = cv2.resize(img, (0, 0), None, 0.6, 0.6)
            resize_img = cv2.resize(img, (0, 0), None, 0.50, 0.50)
            resize_img = cv2.cvtColor(resize_img, cv2.COLOR_BGR2RGB)
            face_loc = get_face_location(resize_img)
            if len(face_loc) == 1:
                face_enc = face_recognition.face_encodings(resize_img, face_loc)
                if update_face == True:
                    face_lst[lst_index[fac_step-1]] = face_enc[0]
                else:
                    face_lst.append(face_enc[0])
                    face_name.append(username)

                fac_step -= 1
                y1, x2, y2, x1 = face_loc[0]
                y1, x2, y2, x1 = (y1 * 2, x2 * 2, y2 * 2, x1 * 2)
                img = cvzone.cornerRect(img, (x1, y1, x2 - x1, y2 - y1), l=20, t=3, rt=0)
                cvzone.putTextRect(img, "{}".format(username), (x1, y1), scale=1, thickness=1)
            cv2.imshow('Camera', img)
            cv2.setWindowProperty('Camera', cv2.WND_PROP_TOPMOST, 1)
            if cv2.waitKey(100) & 0xFF == ord('q'):
                break
            if fac_step < 1:
                break
        cam.release()
        cv2.destroyAllWindows()

        if fac_step <= 0:
            with open('Face/AdminEncoding.pt', 'wb') as f:
                for i in face_lst:
                    pickle.dump(i, f)
            if update_face == False:
                with open('Face/AdminMapping.pt', 'wb') as f:
                    for i in face_name:
                        pickle.dump(i, f)
            return JsonResponse({'code': 'done'})
        else:
            return JsonResponse({'code': 'not'})
    else:
        return JsonResponse({'code': 'err', 'msg': 'Not authenticate'})


@csrf_exempt
def userFaceUpdate(request):
    if request.user.is_authenticated: 
        userName = request.POST.get('userName')
        userRoll = request.POST.get('userRoll') 
        face_lst = []
        with open('Face/Encoding.pt', 'rb') as f:
            while True:
                try:
                    face_lst.append(pickle.load(f))
                except EOFError:
                    break
            with open('Face/Encoding.pt', 'w') as f:
                f.close()
        face_roll = []
        with open('Face/Mapping.pt', 'rb') as f:
            while True:
                try:
                    face_roll.append(pickle.load(f))
                except EOFError:
                    break
            with open('Face/Mapping.pt', 'w') as f:
                f.close()
        lst_index = []
        for i in range(len(face_roll)):
            if face_roll[i] == userRoll:
                lst_index.append(i)

        fac_step = len(lst_index)
        update_face = False
        if fac_step > 0:
            update_face = True
        else:
            fac_step = 5
        cam = cv2.VideoCapture(cam_num)
        while True:
            __, img = cam.read()
            img = cv2.resize(img, (0, 0), None, 0.6, 0.6)
            resize_img = cv2.resize(img, (0, 0), None, 0.50, 0.50)
            resize_img = cv2.cvtColor(resize_img, cv2.COLOR_BGR2RGB)
            face_loc = get_face_location(resize_img)
            if len(face_loc) == 1:
                face_enc = face_recognition.face_encodings(resize_img, face_loc)
                if update_face == True:
                    face_lst[lst_index[fac_step-1]] = face_enc[0]
                else:
                    face_lst.append(face_enc[0])
                    face_roll.append(userRoll)

                fac_step -= 1
                y1, x2, y2, x1 = face_loc[0]
                y1, x2, y2, x1 = (y1 * 2, x2 * 2, y2 * 2, x1 * 2)
                img = cvzone.cornerRect(img, (x1, y1, x2 - x1, y2 - y1), l=20, t=3, rt=0)
                cvzone.putTextRect(img, "{}_{}".format(userName, userRoll), (x1, y1), scale=1, thickness=1)
            cv2.imshow('Camera', img)
            cv2.setWindowProperty('Camera', cv2.WND_PROP_TOPMOST, 1)
            if cv2.waitKey(100) & 0xFF == ord('q'):
                break
            if fac_step < 1:
                break
        cam.release()
        cv2.destroyAllWindows()
        if fac_step <= 0:
            with open('Face/Encoding.pt', 'wb') as f:
                for i in face_lst:
                    pickle.dump(i, f)
            if update_face == False:
                with open('Face/Mapping.pt', 'wb') as f:
                    for i in face_roll:
                        pickle.dump(i, f)
            return JsonResponse({'code': 'done'})
        else:
            return JsonResponse({'code': 'not'})
    else:
        return JsonResponse({'code': 'err', 'msg': 'Not authenticate'})



def getAttendanceData(request):
    month = int (request.GET.get('month', None))
    year = int (request.GET.get('year', None))
    # roll = request.GET.get('user_roll', None)
    roll = 190
    if roll is not None:
        start = datetime.date(year, month, 1) 
        end = datetime.date(year, month, 30) 
        data = AttendanceModel.objects.filter(user_roll= roll, date__gte=start, date__lte=end)
        print(data.values())
        return JsonResponse({'code': 'done'})
        
    else:
        return JsonResponse({'code': 'err', 'msg': 'Not authenticate'})


def getChartData(request):
    year = request.GET.get('year', datetime.datetime.today().year)
    start = datetime.date(year, 1, 1)
    end = datetime.date(year, 12, 31)
    data = UserModel.objects.filter(date__gte=start, date__lte=end)
    print(data)
    return JsonResponse({'m':"fdf"})
