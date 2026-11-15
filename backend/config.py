import os
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore

BACKEND_DIR = Path(__file__).resolve().parent

# Firebase
CREDENTIALS_PATH = os.getenv(
    "FIREBASE_CREDENTIALS",
    str(BACKEND_DIR / "care-45426-firebase-adminsdk-fbsvc-3c8cacde10.json"),
)

if not firebase_admin._apps:
    cred = credentials.Certificate(CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)

# Firestore client
firestoreDB = firestore.client()

# Collections (Firestore collection references)
users_collection = firestoreDB.collection("users")
maternal_profiles_collection = firestoreDB.collection("maternal_profiles")
baby_profiles_collection = firestoreDB.collection("baby_profiles")
user_consent_collection = firestoreDB.collection("user_consent")
onboarding_status_collection = firestoreDB.collection("onboarding_status")
