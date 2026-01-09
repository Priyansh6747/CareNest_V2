import firebase_admin
from firebase_admin import credentials, firestore

# Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# Firestore client
db = firestore.client()

# Collections (Firestore collection references)
users_collection = db.collection("users")
maternal_profiles_collection = db.collection("maternal_profiles")
baby_profiles_collection = db.collection("baby_profiles")
user_consent_collection = db.collection("user_consent")
onboarding_status_collection = db.collection("onboarding_status")
