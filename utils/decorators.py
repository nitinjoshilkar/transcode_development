import json
from django.http import HttpResponseRedirect, JsonResponse
#import jwt
from django.conf import settings
from functools import wraps
from django.contrib.sessions.models import Session
from jwt import (
    JWT,
    jwk_from_dict,
    jwk_from_pem,
)
from Contido_Transcode.models import UserInfo

def is_login_required(func):
    @wraps(func)
    def wrapped_function(*args, **kwargs):
        try:
            request = args[0] if len(args) == 1 else args[1]
            # print ( 'args is ',args)
            #print ( 'request.session ',request.session)
            if 'auth' in request.session:
                try:
                    session = Session.objects.get(session_key=str(request.session.session_key))
                    #payload = jwt.decode(str(session.get_decoded().get('auth').get('token')), settings.ACCESS_TOKEN_SECRET, algorithms=['HS256'])
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
            
                    if payload.get('username')!=request.session['auth']['current_user']:
                        return JsonResponse({
                                "error_code" : 401,
                                "message": "Invalid login token",
                                "status": False
                            })
                    user_qrysets=UserInfo.objects.filter(id=str(payload.get('obj_id')))
                    if user_qrysets.count()==0:
                        return JsonResponse({
                                "error_code" : 401,
                                "message": "Invalid login token",
                                "status": False
                            })
                    return func(*args, **kwargs)
                except Exception as e:
                    print ( 'No session found for session key {} with error code {}'.format(str(request.session.session_key), e))
                    return JsonResponse({
                            "error_code" : 401,
                            "message": "Invalid login token",
                            "status": False
                        })
            else:
                return JsonResponse({
                    "error_code" : 401,
                    "message": "Invalid login token",
                    "status": False
                })
        except Exception as e:
            print ( e)
            return JsonResponse({
                "error_code" : 401,
                "message": "Invalid login token",
                "status": False
            })
    return wrapped_function

def superadmin_user_group_check(function):
    def wrap(request, *args, **kwargs):
        encoded = request.META.get('HTTP_X_ACCESS_TOKEN',None)
        try:
            # request = args[0] if len(args) == 1 else args[1]
            if 'auth' in request.session:
                try:
                    session = Session.objects.get(session_key=str(request.session.session_key))
                    #payload = jwt.decode(str(session.get_decoded().get('auth').get('token')), settings.ACCESS_TOKEN_SECRET, algorithms=['HS256'])
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
                    if payload.get('username')!=request.session['auth']['current_user']:
                        return JsonResponse({
                                "error_code" : 401,
                                "message": "Invalid login token",
                                "status": False
                            })
                    valid = False
                    user_qrysets=UserInfo.objects.get(id=str(payload.get('obj_id')))
                    for groupname in user_qrysets.groupname:
                        if groupname in ['SUPERADMIN']:
                            valid = True
                    if not valid:
                        return JsonResponse({
                            "message": "Invalid superadmin Group",
                            "status": False
                        })
                    return function(request, *args, **kwargs)
                except Exception as e:
                    print ( e)
                    return JsonResponse({
                        "message": "Invalid superadmin Exception Group "+str(e),
                        "status": False
                    })
            else:
                return JsonResponse({
                                "error_code" : 401,
                                "message": "Invalid login token",
                                "status": False
                            })
        except Exception as e:
            print ( e)
            return JsonResponse({
                "message": "Invalid superadmin Exception Group "+str(e),
                "status": False
            })
    return wrap
