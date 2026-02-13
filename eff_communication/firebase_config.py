import os
import json
import firebase_admin
from firebase_admin import credentials
from dotenv import load_dotenv

load_dotenv()  # ensures .env loads

if not firebase_admin._apps:

    firebase_json = os.getenv("FIREBASE_SERVICE_ACCOUNT")

    if not firebase_json:
        raise Exception("FIREBASE_SERVICE_ACCOUNT environment variable is missing")

    cred = credentials.Certificate(json.loads(firebase_json))
    firebase_admin.initialize_app(cred)
