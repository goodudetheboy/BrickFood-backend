import firebase_admin, os
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import storage

# Use a service account.
cred = credentials.Certificate("./serviceAccount.json")

app = firebase_admin.initialize_app(cred, {"storageBucket": "brickfoodapp.appspot.com"})

db = firestore.client()

bucket = storage.bucket()
