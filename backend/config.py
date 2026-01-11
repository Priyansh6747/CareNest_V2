import firebase_admin
from firebase_admin import credentials, firestore

# Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# Firestore client
firestoreDB = firestore.client()

# Collections (Firestore collection references)
users_collection = firestoreDB.collection("users")
maternal_profiles_collection = firestoreDB.collection("maternal_profiles")
baby_profiles_collection = firestoreDB.collection("baby_profiles")
user_consent_collection = firestoreDB.collection("user_consent")
onboarding_status_collection = firestoreDB.collection("onboarding_status")
