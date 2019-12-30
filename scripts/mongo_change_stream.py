from pymongo import MongoClient
import pprint

client = MongoClient()
_MONGODB_NAME = "tctrl_stagging"
#client = MongoClient('localhost', 27017)
client = "mongodb+srv://tctrl_atlas_dev:tctrl_atlas_dev@topaz-staging-v4-t1wgq.mongodb.net/tctrl_stagging?retryWrites=true"
print(client)
print("MongoDB connected")
db = client["changestream"]
print("database connected")
collection = db['collection']	
print("connected to collection table")

print(collection.insert_one({"hello": "marit"}).inserted_id)

