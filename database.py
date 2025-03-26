import os
import pymongo
from pymongo.server_api import ServerApi
from urllib.parse import quote_plus

# Connect to MongoDB Cluster
db_password = os.environ.get('MONGODB_PASS')
db_username = os.environ.get('MONGODB_USERNAME')

URI = f"mongodb+srv://{db_username}:{db_password}@cluster0.zphey.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = pymongo.MongoClient(URI, server_api=ServerApi("1"))

# Confirm the connection
try:
    client.admin.command("ping")
    print("Succesfully pinged your deployment. You're connected to MongoDB!")

    client.close()
except Exception as e:
    print(e)
    
