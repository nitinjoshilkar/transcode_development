from mongoengine import *
import json
from django.db import models
from django.utils import timezone
from mongoengine import signals
import datetime
from transcode.models import *
import logging
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save,pre_save,pre_init

#Create and configure logger 
logging.basicConfig(filename="transcode_job_update.log", 
                    format='%(asctime)s %(message)s', 
                    filemode='a+') 

logger=logging.getLogger() 
logger.setLevel(logging.DEBUG)

class Transcode(Document):

    hostname = StringField(default='')
    job_id = StringField(default='')
    job_status = IntField(default=0)
    job_action = StringField(default='')
    commands = StringField(default='')

    location = StringField(default='')
    master_file_path = StringField(default='')
    timecode = StringField(default='')
    archive_path = StringField(default='')
    output_format = ListField(StringField())
    
    input_file_path = StringField(default='')

    upload_from = StringField(default='')
    upload_type =StringField(default='')
    error = StringField(default=None)
    #data = DictField(default=None)

    asset_type = StringField(default='')
    is_mxf = BooleanField(default=False)
    mediainfo = DictField(default={})
    audio_house_format = ListField(default=[])
    #originalMessage = DictField(default='')

    shape_wav_id = StringField(default='')
    shape_app_id = StringField(default='')
    shape_web_id = StringField(default='')
    shape_master_id = StringField(default='')
    shape_hls_id = StringField(default='')

    thumbnail = StringField(default='')
    thumbnail_preview = StringField(default='')
    partial_clipping = ListField(DictField())
    audio_tracks = ListField(DictField())
    input_file_path_mp4 = StringField(default='')
    response_formatter = ListField(default=[])    

    job_starttime = DateTimeField(default=timezone.now().replace(microsecond=0))
    job_endtime = DateTimeField(default=timezone.now().replace(microsecond=0))
    creation = DateTimeField(default=timezone.now().replace(microsecond=0))
    modified_at = DateTimeField(default=timezone.now().replace(microsecond=0))


    @classmethod
    def pre_save(cls,sender,document,**kwargs):
        logging.debug("job id: {} updated".format(document.job_id))

    @classmethod
    def post_save(cls,sender,document,**kwargs):
        
        print("job_id :{} is updated".format(document.job_id))
        modified_at = datetime.datetime.now()
        document.modified_at = modified_at
        print("Modified at:",modified_at)
        return document.job_id
        
    @classmethod
    def pre_init(cls,sender,document,**kwargs):
        print("job_id :{} is updated with job status:{}".format(document.job_id,document.job_status))
        modified_at = datetime.datetime.now()
        document.modified_at = modified_at
        print("Modified at:",modified_at)
        return {'job_id':document.job_id,'job_status': document.job_status}

    @classmethod
    def pre_save_post_validation(cls,sender,document,**kwargs):
        print("job_id :{} is updated with job status:{}".format(document.job_id,document.job_status))
        modified_at = datetime.datetime.now()
        document.modified_at = modified_at
        print("Modified at:",modified_at)
        return {'job_id':document.job_id,'job_status': document.job_status}

signals.post_save.connect(Transcode.post_save,sender=Transcode)
signals.pre_save.connect(Transcode.pre_save,sender=Transcode)
#signals.pre_init.connect(Transcode.pre_init,sender=Transcode)
#signals.pre_save_post_validation.connect(Transcode.pre_save_post_validation,sender=Transcode,weak=False)

class Machines(Document):

    hostname=StringField(required=True)
    status=IntField(required=True,default=0)
    alloted_jobs=IntField(max_value=4,default=0)


