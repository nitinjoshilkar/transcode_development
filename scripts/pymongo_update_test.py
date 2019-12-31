from pymongo import MongoClient
import pprint

client = MongoClient()

client = MongoClient('localhost', 27017)
db = client.transcode_db2
print("database connected")
collection = db.Transcode
print("connected to collection")
collection_name=db.list_collection_names()
print(collection_name)
transcode=db.transcode
pprint.pprint(transcode.find_one({"job_id":"TRD17"}))
data=transcode.find_one({"job_id":"TRD17"})
print(transcode.count_documents({}))
transcode.update_one({"job_id":"TRD17"}, {"$set":{"job_status":2}})
print('data updated')
# 100888471059
# MuYx66


