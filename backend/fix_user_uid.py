from config import users_collection
import firebase_admin
from firebase_admin import firestore
import sys

# The UID reported by the user in the error logs
TARGET_UID = "7qL4PzrEfQe04tvpUems1L89ePg1"

def fix_missing_uid():
    print(f"Searching for user to patch with UID: {TARGET_UID}")
    
    # Get recent users
    # We assume the user encountering this is likely one of the most recent ones
    users = users_collection.order_by("created_at", direction=firestore.Query.DESCENDING).limit(10).stream()
    
    candidate_doc = None
    
    for doc in users:
        data = doc.to_dict()
        uid = data.get("firebase_uid")
        email = data.get("email")
        phone = data.get("phone")
        
        print(f"Checking user {doc.id} (Email: {email}, Phone: {phone}, UID: {uid})")
        
        if not uid:
            # Found a user without UID
            candidate_doc = doc
            break
            
    if candidate_doc:
        print(f"Found candidate user: {candidate_doc.id}")
        print(f"Patching with firebase_uid: {TARGET_UID}")
        
        users_collection.document(candidate_doc.id).update({
            "firebase_uid": TARGET_UID
        })
        print("SUCCESS: User patched.")
    else:
        print("FAILURE: No user found without firebase_uid in the last 10 users.")
        # Fallback dump
        print("Dumping all users just in case:")
        all_users = users_collection.limit(20).stream()
        for doc in all_users:
            print(f"- {doc.id}: {doc.to_dict()}")

if __name__ == "__main__":
    try:
        fix_missing_uid()
    except Exception as e:
        print(f"Error: {e}")
