import json
import hmac
import hashlib
from .models import *
import sys
from django.utils import timezone
from django.contrib.auth import logout
import datetime
import time
import base64
import string
import random
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from utils.decorators import *
from django.contrib.sessions.models import Session
from django.shortcuts import HttpResponse, render_to_response, HttpResponseRedirect,render
from Contido_Transcode.models import UserInfo
from decouple import config
from rest_framework.response import Response
from rest_framework import views
from jwt import (
    JWT,
    jwk_from_dict,
    jwk_from_pem,
)
import jwt
from rest_framework.decorators import api_view


def gen_random_number(number):
    characterSet = string.digits
    random_id = ''.join(random.choice(characterSet) for i in range(number))
    return random_id

def generate_token(user):
    # number = gen_random_number(10)
    
    currentTime = int(datetime.datetime.now().strftime("%s")) * 1000
    payload = {"username": user.username,
               "obj_id": str(user.id),
               "firstname": user.firstname,
               "lastname": user.lastname,
               "groupname": user.groupname,
               #"location":user.location,
               "location_tag":user.location_tag,
               "randomNumber": gen_random_number(10),
               #"tokenCreatedAt": currentTime,
               #"exp": datetime.datetime.now() + datetime.timedelta(days=10)
               }
    
    #encoded = jwt.encode(payload, settings.ACCESS_TOKEN_SECRET)
    with open('settings/rsa_private_key.pem', 'rb') as fh:
        signing_key = jwk_from_pem(fh.read())
        jwt = JWT()
    try:
        encoded= jwt.encode(payload, signing_key, 'RS256')
    except Exception as e:
        print(e)
        return JsonResponse({"Error":"Token is not created","status":"400"})
    return encoded

def auth_view(request):
    username=request.POST.get('username',None)
    raw_password=request.POST.get('password',None)
    project_title=request.POST.get('project_title',None)

    if raw_password and username:
        try:
            user_info_qryset = UserInfo.objects.filter(username=username.lower())
            if len(user_info_qryset) <=0:return JsonResponse({'message': "Your profile doesn't seem to exist with us.", 'status': False})
            try:
                if (username.split('@')[-1] not in config('TRANSCODE_USER_DOMAIN').split(',')):
                    return JsonResponse({'message': 'Please login with okta' , 'status': False})
            except Exception as e:
                return JsonResponse({'message': "Your profile doesn't seem to exist with us.", 'status': False})
            encoded_username=username.encode('utf-8')
            raw_password = raw_password.encode('utf-8')
            password = base64.b64encode(encoded_username.lower()+raw_password).decode('ascii')
            #print (password)
            user_info = user_info_qryset.first()
            if user_info.project_title != project_title:
                return JsonResponse({'message':"Invalid project title"})
            action=action_id=share_id=''
            guest_user = False
            # print any(x in ['ACCESS_SUBTITLE','ACCESS_TAGGING','ACCESS_QC','SUPERADMIN'] for x in user_info.groupname)
            if user_info_qryset.filter(password=password):
                guest_user = False
            elif any(x in ['NORMAL_USER','SUPERADMIN'] for x in user_info.groupname):
                
                try:
                    ps = '{}{}'.format(str(encoded_username.lower()),str(raw_password))
                    one_time_passwd=base64.b64encode(ps.encode('utf-8')).decode('ascii')
                    guest_user=True
                    request.session.set_expiry(28800) # 480 minutes expiry time for session and this is in seconds
                except Exception as e:
                    print (e)
                    return JsonResponse({'message': "Invalid login credentials!", 'status': False})
            else:
                return JsonResponse({'message': "Your profile doesn't seem to exist with us.", 'status': False})

            if not guest_user and (user_info.disabled or len(user_info.groupname) < 1):
                print ('bypassing the only collab users to restrict it from control login or if the user is disabled from backend or not')
                return JsonResponse({'message': 'Invalid login credentials!!' , 'status': False})
            user_info.token = generate_token(user_info)
            user_info.save()
            print ("Successfully Login")
            
            data = {'token': user_info.token,'groupname': user_info.groupname, 'groupaccess':user_info.groupaccess}

            request.session['HTTP_X_ACCESS_TOKEN'] = user_info.token
            request.session['guest_user'] = guest_user
            request.session['action'] = action
            request.session['action_id'] = action_id
            request.session['share_id'] = share_id
            request.session['device'] = request.META.get('HTTP_API_TYPE','WEB')
            request.session['auth'] = {'current_user': username, 'token': user_info.token}
            print(request.session['auth'])
            return HttpResponseRedirect('/api/home/')
            #return JsonResponse({'is_guest_user':guest_user, 'action':action,'id':action_id ,'data': user_info.get_user_info(), 'message': 'Success', 'status': True})
        except Exception as e:
            print (" Login Error ",e)
            return JsonResponse({'message': 'Invalid login credentials!!!' , 'status': False})
    #return JsonResponse({'message': 'Success', 'status': True})
    return render(request,'html_templates/login.html')

@is_login_required
@superadmin_user_group_check
def add_user(request):
    username= request.POST.get('username',None)
    password= request.POST.get('password',None)
    firstname= request.POST.get('firstname',None)
    lastname= request.POST.get('lastname',None)
    project_title= request.POST.get('project_title',None)
    groupname= request.POST.get('groupname',None)


    if username and password:
        try:
            user_info = UserInfo.objects.get(username=username)
            return JsonResponse({'message': 'Username is registered', 'status': False})
        except:
            user_info = UserInfo()
            username_encoded = username.encode('utf-8')
            print(username_encoded)
            password = password.encode('utf-8')
            print(password)
            user_info.username = username.lower()
            user_info.password = base64.b64encode(username_encoded.lower() + password).decode('ascii')
            print(user_info.password)
            user_info.firstname = firstname
            user_info.lastname = lastname
            user_info.project_title = project_title
            user_info.groupname = [groupname]
            print(user_info.token)
            user_info.save()
            return JsonResponse({'message': 'Success', 'status': True})
    return render(request,'html_templates/adduser.html')

def home(request):
    
    return render(request,'html_templates/home.html')

def logout_view(request):
    encoded = request.META.get('HTTP_X_ACCESS_TOKEN',None)
    try:
        session = Session.objects.get(session_key=str(request.session.session_key))
        with open('settings/rsa_public_key.pem', 'rb') as fa:
                jwk = jwk_from_pem(fa.read())
                data=jwk.to_dict()
        jwt = JWT() 
        verifying_key = jwk_from_dict(data)
            
        try:
            payload = jwt.decode(str(session.get_decoded().get('auth').get('token')), verifying_key)
        except Exception as e:
            print(e)
            print("token not decoded")
            
        #payload = jwt.decode(str(session.get_decoded().get('auth').get('token')), settings.ACCESS_TOKEN_SECRET, algorithms=['HS256'])
        if payload.get('username')==request.session['auth']['current_user']:
            user_info = UserInfo.objects.get(id=payload.get('obj_id'))
            user_info.token = None
            user_info.save()
            logout(request)
            print( "Successfully Logout")
        if request.session.get('guest_user', False):
            try:
                share_qryset=Share.objects.get(id=request.session.get('share_id'))
                share_qryset.update(is_verified=True)
                share_qryset.update(is_accessed=True)
            except:
                pass
        return HttpResponseRedirect('/')
        #return JsonResponse({'message': 'Success', 'status': True, 'error_code':401})
    except IOError as e:
        logout(request)
        print ( "I/O error({0}): {1}".format(e.errno, e.strerror))
        return JsonResponse({'message': 'Error!', 'status': True, 'error_code':401})
    except ValueError:
        logout(request)
        print ( "Could not convert data to an integer.")
        return JsonResponse({'message': 'Error!!', 'status': True, 'error_code':401})
    except Exception as e:
        logout(request)
        print ( "Unexpected error:", sys.exc_info()[0], ' ',e)
        return JsonResponse({'message': 'Error!!!', 'status': True, 'error_code':401})

class LoginApi(views.APIView):
    
    def post(self, request, *args, **kwargs):
        
        if not request.data:
            return Response({'Error': "Please provide email and organisation name"}, status="400")
        try:
            email = request.data['email']
            organisation = request.data['organisation']
        except Exception as e:
            print(e)
            return Response({'Error': "Invalid parameter"}, status="400")

        try:
           user = UserInfo.objects.filter(username=email,project_title=organisation)

           for user_data in user:
                new_expire_time=int(user_data.api_expired_token_at.timestamp())
                new_token_created= int(user_data.api_created_token_at.timestamp())
                api_token_recreate = user_data.api_token_recreate
                email = user_data.username
                project_title = user_data.project_title
           if user_data.username != email:
                return Response({'Error': "Email id doesn't exists"}, status="400")
           elif user_data.project_title != organisation:
                return Response({'Error': "project title not associated with user"}, status="400")


        except Exception as e:
            print(e)
            return Response({'Error': "Your profile doesn't exist with us."}, status="400")
        #if user_data:
        current_time = int(datetime.datetime.now().timestamp())
        data_current_time=datetime.datetime.fromtimestamp(current_time).strftime("%Y-%m-%d %H:%M:%S")
        print("current time:",data_current_time)
        expiry_time = datetime.datetime.now()+ datetime.timedelta(hours=24)
        expirytime2=int(expiry_time.strftime('%s'))
        data_expirytime2= datetime.datetime.fromtimestamp(expirytime2).strftime("%Y-%m-%d %H:%M:%S")
        print("Expiry time",data_expirytime2)
        # user.api_token_recreate == False
        #if current_time > new_expire_time and api_token_recreate == False:
        #    return Response({"Error":"Token is Expired"},status="400")
        if (current_time > new_token_created) and (current_time < new_expire_time):
            return Response({"Error":"Token is already created. You can access api"},status="400")
        elif user_data.transcode_token:
            return Response({"Error":"Use refresh token because one time token created already"},status="400")

        elif current_time > new_expire_time and user_data.api_token_recreate == False:

            message = {
                    "email": email,
                    "organisation": project_title
                    
                    }
    
                
            with open('settings/rsa_private_key.pem', 'rb') as fh:
                signing_key = jwk_from_pem(fh.read())
            jwt = JWT()
            try:
                compact_jws = jwt.encode(message, signing_key, 'RS256')
            except Exception as e:
                print(e)
                return Response({"Error":"Token is Expired"},status="400")
            user_data.transcode_token = compact_jws
            user_data.api_created_token_at = data_current_time
            user_data.api_expired_token_at = data_expirytime2
            #user.api_token_recreate = False
            user_data.save() 
            print(compact_jws)
            # with open('settings/rsa_public_key.json', 'r') as fc:
            #     print(fc)
            #     print(json.load(fc))
            #     verifying_key = jwk_from_dict(json.load(fc))
            with open('settings/rsa_public_key.pem', 'rb') as fa:
                jwk = jwk_from_pem(fa.read())
                data=jwk.to_dict()
                print(data) 
    
            verifying_key = jwk_from_dict(data)
            
            try:
                message_received = jwt.decode(compact_jws, verifying_key)
            except Exception as e:
                print(e)
                return Response({"Error":"Token is Expired"},status="400")
            print(message_received)
            return Response({"compact_jws":compact_jws, "message_received":message_received},
                  status="200",
                  )
    
class LoginApiRefresh(views.APIView):
    
    def post(self, request, *args, **kwargs):
        
        if not request.data:
            return Response({'Error': "Please provide email and organisation name"}, status="400")
        try:
            email = request.data['email']
            organisation = request.data['organisation']
            token_refresh = request.data['token_refresh']
        except Exception as e:
            print(e)
            return Response({'Error': "Invalid parameter"}, status="400")

        try:
           user = UserInfo.objects.filter(username=email,project_title=organisation)

           for user_data in user:
                new_expire_time=int(user_data.api_expired_token_at.timestamp())
                new_token_created= int(user_data.api_created_token_at.timestamp())
                api_token_recreate = user_data.api_token_recreate
                email = user_data.username
                project_title = user_data.project_title
           if user_data.username != email:
                return Response({'Error': "Email id doesn't exists"}, status="400")
           elif user_data.project_title != organisation:
                return Response({'Error': "project title not associated with user"}, status="400")
           elif user_data.transcode_token != token_refresh:
                return Response({'Error': "token doesn't match"}, status="400")
            

        except Exception as e:
            print(e)
            return Response({'Error': "Your profile doesn't exist with us."}, status="400")
        #if user_data:
        current_time = int(datetime.datetime.now().timestamp())
        data_current_time=datetime.datetime.fromtimestamp(current_time).strftime("%Y-%m-%d %H:%M:%S")
        print("current time:",current_time)
        print("current time:",data_current_time)
        expiry_time = datetime.datetime.now()+ datetime.timedelta(hours=24)
        expirytime2=int(expiry_time.strftime('%s'))
        data_expirytime2= datetime.datetime.fromtimestamp(expirytime2).strftime("%Y-%m-%d %H:%M:%S")
        print("Expiry time",data_expirytime2)
        # user.api_token_recreate == False
        #if current_time > new_expire_time:
        #    return Response({"Error":"Token is Expired"},status="400")
        if (current_time > new_token_created) and (current_time < new_expire_time):
            return Response({"Error":"Token is already created. You can access api"},status="400")
        elif current_time > new_expire_time and api_token_recreate == False:

            message = {
                    "email": email,
                    "organisation": project_title,
                    
                    }
    
                
            with open('settings/rsa_private_key.pem', 'rb') as fh:
                signing_key = jwk_from_pem(fh.read())
            jwt = JWT()
            try:
                compact_jws = jwt.encode(message, signing_key, 'RS256')
            except Exception as e:
                print(e)
                return Response({"Error":"Token is Expired"},status="400")
            user_data.api_token = compact_jws
            user_data.api_created_token_at = data_current_time
            user_data.api_expired_token_at = data_expirytime2
            #user.api_token_recreate = False
            user_data.save() 
            print(compact_jws)
            # with open('settings/rsa_public_key.json', 'r') as fc:
            #     print(fc)
            #     print(json.load(fc))
            #     verifying_key = jwk_from_dict(json.load(fc))
            with open('settings/rsa_public_key.pem', 'rb') as fa:
                jwk = jwk_from_pem(fa.read())
                data=jwk.to_dict()
                print(data) 
    
            verifying_key = jwk_from_dict(data)
            
            try:
                message_received = jwt.decode(compact_jws, verifying_key)
            except Exception as e:
                print(e)
                return Response({"Error":"Token is Expired"},status="400")
            print(message_received)
            return Response({"compact_jws":compact_jws, "message_received":message_received},
                  status="200",
                  )

@api_view(['POST'])
def login_api(request):
    if not request.data:
        return Response({'Error': "Please provide email and organisation name"}, status="400")
    try:
        email = request.data['email']
        organisation = request.data['organisation']
    except Exception as e:
        print(e)
        return Response({'Error': "Invalid parameter"}, status="400")

    try:
        user = UserInfo.objects.filter(username=email)

        for user_data in user:
             new_expire_time=int(user_data.api_expired_token_at.timestamp())
             new_token_created= int(user_data.api_created_token_at.timestamp())
             api_token_recreate = user_data.api_token_recreate
             email = user_data.username
             project_title = user_data.project_title
        if user_data.username != email:
             return Response({'Error': "Email id doesn't exists"}, status="400")
        elif user_data.project_title != organisation:
             return Response({'Error': "project title not associated with user"}, status="400")
    except Exception as e:
        print(e)
        return Response({'Error': "Your profile doesn't exist with us."}, status="400")
        #if user_data:
    current_time = int(datetime.datetime.now().timestamp())
    data_current_time=datetime.datetime.fromtimestamp(current_time).strftime("%Y-%m-%d %H:%M:%S")
    print("current time:",data_current_time)
    expiry_time = datetime.datetime.now()+ datetime.timedelta(hours=24)
    expirytime2=int(expiry_time.strftime('%s'))
    data_expirytime2= datetime.datetime.fromtimestamp(expirytime2).strftime("%Y-%m-%d %H:%M:%S")
    print("Expiry time",data_expirytime2)
    # user.api_token_recreate == False
    #if current_time > new_expire_time and api_token_recreate == False:
    #    return Response({"Error":"Token is Expired"},status="400")
    if (current_time > new_token_created) and (current_time < new_expire_time):
        return Response({"Error":"Token is already created. You can access api"},status="400")
    elif user_data.transcode_token:
        return Response({"Error":"Use refresh token because one time token created already"},status="400")
    elif current_time > new_expire_time and user_data.api_token_recreate == False:

        message = {
                "email": email,
                "organisation": project_title
                
                }
    
                
        with open('settings/rsa_private_key.pem', 'rb') as fh:
            signing_key = jwk_from_pem(fh.read())
        jwt = JWT()
        try:
            compact_jws = jwt.encode(message, signing_key, 'RS256')
        except Exception as e:
            print(e)
            return Response({"Error":"Token is Expired"},status="400")
        user_data.transcode_token = compact_jws
        user_data.api_created_token_at = data_current_time
        user_data.api_expired_token_at = data_expirytime2
        #user.api_token_recreate = False
        user_data.save() 
        print(compact_jws)
        # with open('settings/rsa_public_key.json', 'r') as fc:
        #     print(fc)
        #     print(json.load(fc))
        #     verifying_key = jwk_from_dict(json.load(fc))
        with open('settings/rsa_public_key.pem', 'rb') as fa:
            jwk = jwk_from_pem(fa.read())
            data=jwk.to_dict()
            print(data) 
    
        verifying_key = jwk_from_dict(data)
            
        try:
            message_received = jwt.decode(compact_jws, verifying_key)
        except Exception as e:
            print(e)
            return Response({"Error":"Token is Expired"},status="400")
        print(message_received)
        return Response({"compact_jws":compact_jws, "message_received":message_received},
              status="200",
              )

@api_view(['POST'])
def login_api_refresh(request):

    if not request.data:
        return Response({'Error': "Please provide email and organisation name"}, status="400")
    try:
        email = request.data['email']
        organisation = request.data['organisation']
        token_refresh = request.data['token_refresh']
    except Exception as e:
        print(e)
        return Response({'Error': "Invalid parameter"}, status="400")

    try:
        user = UserInfo.objects.filter(username=email,project_title=organisation)

        for user_data in user:
             new_expire_time=int(user_data.api_expired_token_at.timestamp())
             new_token_created= int(user_data.api_created_token_at.timestamp())
             api_token_recreate = user_data.api_token_recreate
             email = user_data.username
             project_title = user_data.project_title
        if user_data.username != email:
             return Response({'Error': "Email id doesn't exists"}, status="400")
        elif user_data.project_title != organisation:
             return Response({'Error': "project title not associated with user"}, status="400")
        elif user_data.transcode_token != token_refresh:
             return Response({'Error': "token doesn't match"}, status="400")
            

    except Exception as e:
        print(e)
        return Response({'Error': "Your profile doesn't exist with us."}, status="400")
        #if user_data:
    current_time = int(datetime.datetime.now().timestamp())
    data_current_time=datetime.datetime.fromtimestamp(current_time).strftime("%Y-%m-%d %H:%M:%S")
    print("current time:",current_time)
    print("current time:",data_current_time)
    expiry_time = datetime.datetime.now()+ datetime.timedelta(hours=24)
    expirytime2=int(expiry_time.strftime('%s'))
    data_expirytime2= datetime.datetime.fromtimestamp(expirytime2).strftime("%Y-%m-%d %H:%M:%S")
    print("Expiry time",data_expirytime2)
    # user.api_token_recreate == False
    #if current_time > new_expire_time:
    #    return Response({"Error":"Token is Expired"},status="400")
    if (current_time > new_token_created) and (current_time < new_expire_time):
        return Response({"Error":"Token is already created. You can access api"},status="400")
    elif current_time > new_expire_time and api_token_recreate == False:

        message = {
                "email": email,
                "organisation": project_title,
                
                }
    
                
        with open('settings/rsa_private_key.pem', 'rb') as fh:
            signing_key = jwk_from_pem(fh.read())
        jwt = JWT()
        try:
            refresh_jws = jwt.encode(message, signing_key, 'RS256')
        except Exception as e:
            print(e)
            return Response({"Error":"Token is Expired"},status="400")
        user_data.api_token = refresh_jws
        user_data.api_created_token_at = data_current_time
        user_data.api_expired_token_at = data_expirytime2
        #user.api_token_recreate = False
        user_data.save() 
        print(refresh_jws)
        # with open('settings/rsa_public_key.json', 'r') as fc:
        #     print(fc)
        #     print(json.load(fc))
        #     verifying_key = jwk_from_dict(json.load(fc))
        with open('settings/rsa_public_key.pem', 'rb') as fa:
            jwk = jwk_from_pem(fa.read())
            data=jwk.to_dict()
            print(data) 
    
        verifying_key = jwk_from_dict(data)
            
        try:
            message_received = jwt.decode(refresh_jws, verifying_key)
        except Exception as e:
            print(e)
            return Response({"Error":"Token is Expired"},status="400")
        print(message_received)
        return Response({"refresh_jws":refresh_jws, "message_received":message_received},
              status="200",
              )
    

def is_token_required(function):
    def wrap(request, *args, **kwargs):
        token = request.META.get('HTTP_AUTHORIZATION',None)
        try:
            print("token used:",token.split()[1])
            split_token= token.split()[1]
            token_data=UserInfo.objects.filter(transcode_token=split_token)
            for user_token in token_data:
                print("expiry time:",int(user_token.api_expired_token_at.strftime('%s')))
                expiry_time =int(user_token.api_expired_token_at.strftime('%s'))
            current_time = int(datetime.datetime.now().timestamp())
            data_current_time=datetime.datetime.fromtimestamp(current_time).strftime("%Y-%m-%d %H:%M:%S")
            print("current time:",current_time)
            if not token_data:
                return Response({"error":'token not matched'})
            elif current_time >= expiry_time:
                return Response({"error":"token is expired"})
            #return function(request, *args, **kwargs)   
            #expiry_time = datetime.datetime.now()+ datetime.timedelta(hours=24)
            #expirytime2=int(expiry_time.strftime('%s'))
            #data_expirytime2= datetime.datetime.fromtimestamp(expirytime2).strftime("%Y-%m-%d %H:%M:%S")
            #print("Expiry time",data_expirytime2)
            # user.api_token_recreate == False
            #if current_time > new_expire_time and api_token_recreate == False:
            #    return Response({"Error":"Token is Expired"},status="400")
            #if (current_time > new_token_created) and (current_time < new_expire_time):
            #    return Response({"Error":"Token is already created. You can access api"},status="400")
            #elif user_data.api_token:
            #    return Response({"Error":"Use refresh token because one time token created already"},status="400")
            
            return function(request, *args, **kwargs)
        except:
            return Response({"error":"token not found. try after sometime"})
    return wrap

