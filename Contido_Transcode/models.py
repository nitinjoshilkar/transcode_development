from mongoengine import *
import datetime
import json
from django.db import models
from django.utils import timezone

class UserInfo(Document):
    username = StringField(default='')
    password = StringField(default='')

    token = StringField(default='')
    transcode_token = StringField(default='')

    firstname = StringField(default='')
    lastname = StringField(default='')

    project_title= StringField(default='')
    groupname = ListField()
    groupaccess = ListField()
    location = StringField(default='')
    location_tag = StringField(default='HYD')
    user_hash = StringField(default='')

    has_access_to = ListField()                     # this field refers to ['COLLAB','CONTROL']
    transcode_title = StringField(default='')           # this field refers to ['Programing', 'OAP', 'S&P', 'Traffic', 'Operations', 'Broadcast Tech', 'Prod House', 'Corporate']
    user_image = StringField(default='')            # this field refers to image for user to upload
    location_id = StringField(default='')           # location id foreign key from location model
              # firebase id for that user
    transcode_company = StringField(default='')         # entity id refernce key
    transcode_company_name = StringField(default='')    # entity name which is referred
    assigned_shows = ListField()                    # assigned shows for that user for collab
    assigned_movies = ListField()                   # assigned movied for that user for collab
    is_tvc = BooleanField(default=False)            # do we want to show tvc for that user or not collab
    is_promo = BooleanField(default=False)          # does we want to show generic promo for that user
    is_clip = BooleanField(default=False)           # does we want to show generic clip for that user
    is_all_shows = BooleanField(default=False)           # does we want to show generic clip for that user
    is_all_movies = BooleanField(default=False)           # does we want to show generic clip for that user
    disabled = BooleanField(default=True)          # field used to restrict the user in login sectio
    invite_request_token = StringField(default='')  # field used for first time login of password
    invite_acceptance_token = StringField(default='')  # field used for first time login of password
    reset_password_token = StringField(default='')  # field used for reset password
    asset_permissions = ListField()                 # this is list of permission set which belongs to that specific user
    asset_permission_id = ListField()               #
    last_login_transcode = DateTimeField(default=timezone.now())
    last_login_transcode = DateTimeField(default=timezone.now())
    password_set_time = DateTimeField(default=timezone.now())
    creation = DateTimeField(default=timezone.now())
    api_created_token_at= DateTimeField(default=timezone.now())
    api_expired_token_at = DateTimeField(default=timezone.now())
    api_token_recreate = BooleanField(default= False)

    def get_user_info(self):
        if not self.groupaccess:
            group_name=[]
            for given_group in self.groupname:
                group_name.append({'name':given_group,'subgroups':['ALL']})
        else:
            group_name=self.groupaccess
        return {"id": str(self.id), "username": self.username,
                "token": self.token,
                "firstname": self.firstname, "lastname": self.lastname,
                "groupname": self.groupname, "location":self.location,
                "location_tag":self.location_tag, "groupaccess":group_name,
                "user_hash": self.user_hash}

