from Contido_Transcode.models import UserInfo
from transcode.models import Transcode

def generate_job_id():
    job_id=None
    latest_job_ids= []
    try:
        for given_job_ids in Transcode.objects.values_list('job_id').order_by('-job_id'):
            if given_job_ids is not None:
                latest_job_ids.append(given_job_ids)

        if len(latest_job_ids)<=0:
            return 'TRD1'
        numbs=[]
        for ids in latest_job_ids:
            numbs.append(str(ids.split('TRD')[1]))
        numbs.sort(key=int)
        job_id='TRD'+str( int(numbs[-1]) + 1)
        return job_id
    except Exception as e:
        print( e)
        return 'TRD1'