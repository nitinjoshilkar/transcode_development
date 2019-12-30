from bson.json_util import dumps
from pymongo import MongoClient
import pprint

client = MongoClient()

client = MongoClient('localhost', 27017)

change_stream = client.changestream.collection.watch()

for change in change_stream:
    print(dumps(change))
    print('') # for readability only