import os, django, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Contido_Transcode.settings")
django.setup()

from django.http import JsonResponse, HttpResponse
from django.conf import settings
from decouple import config
import json
import datetime
from transcode.models import Transcode
from mongoengine import signals

def main():
	
	try:
		data = Transcode.objects.filter(job_id='TRD14')

		for transcode_data in data:
			#job_status_updated = transcode_data.job_status
			a=transcode_data.update(job_status=3)
			b=transcode_data.save()
			#print(a,b.job_id)
		     
	except Exception as e:
		print(e)
		
	

if __name__ == '__main__':
    print( '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
    print( str(datetime.datetime.now()))
    main()
# 100888471059
