"""
seed_test_user.py - Populate a demo account with 30 days of data

Writes 30 days of meals, water logs and symptoms so every feature (dashboard
insights, logs, symptom report, doctor summary) has data.

IMPORTANT: the web app authenticates against its own Firebase project, so the
UID it sends to this API is NOT one this backend's admin SDK knows about. We
therefore seed under the `firebase_uid` already stored on the user document
(which /user/link-account backfills on login), not a UID we invent here.

Usage:
    cd backend && uv run python seed_test_user.py
    cd backend && uv run python seed_test_user.py --uid <firebase-uid>
"""

import argparse
import random
import sys
from datetime import datetime, timedelta, timezone

from config import (
    firestoreDB,
    maternal_profiles_collection,
    onboarding_status_collection,
    user_consent_collection,
    users_collection,
)

EMAIL = "test@testuser.com"
DISPLAY_NAME = "Priya Sharma"
PHONE = "+919876543210"
DAYS = 30

random.seed(42)

# ---------------------------------------------------------------------------
# Meal catalogue: (name, description, grams, protein_g, fiber_g, iron_mg,
#                   vitamin_d_mcg, omega3_g)
# Values are rough per-serving figures used to make trends realistic.
# ---------------------------------------------------------------------------
BREAKFASTS = [
    ("Masala Oats with Almonds", "Oats cooked with milk, almonds and spices", 250, 9.5, 5.2, 2.4, 1.2, 0.15),
    ("Poha with Peanuts", "Flattened rice with peanuts and lemon", 200, 6.2, 2.8, 1.9, 0.3, 0.05),
    ("Idli with Sambar", "Steamed rice cakes with lentil stew", 300, 11.0, 4.6, 3.1, 0.4, 0.08),
    ("Paneer Paratha", "Whole wheat flatbread stuffed with paneer", 220, 14.5, 3.9, 1.6, 1.8, 0.06),
    ("Greek Yogurt with Berries", "High protein yogurt with mixed berries", 200, 12.8, 3.1, 0.6, 2.4, 0.12),
]

LUNCHES = [
    ("Rajma Chawal", "Kidney bean curry with steamed rice", 400, 15.2, 11.4, 5.2, 0.5, 0.22),
    ("Palak Paneer with Roti", "Spinach curry with cottage cheese", 350, 18.6, 6.8, 6.4, 2.1, 0.18),
    ("Chicken Curry with Rice", "Home style chicken curry and rice", 420, 28.4, 3.2, 2.8, 1.4, 0.35),
    ("Dal Tadka with Brown Rice", "Yellow lentils with brown rice", 380, 13.8, 9.6, 4.6, 0.2, 0.14),
    ("Chole with Bhature", "Chickpea curry with fried bread", 450, 16.2, 10.8, 6.9, 0.6, 0.25),
]

DINNERS = [
    ("Grilled Salmon with Quinoa", "Omega rich salmon fillet with quinoa", 350, 34.2, 5.4, 2.1, 12.8, 2.4),
    ("Vegetable Khichdi", "Rice and lentil one pot with vegetables", 350, 12.4, 6.8, 3.8, 0.4, 0.12),
    ("Roti with Soya Chunks Curry", "Whole wheat roti with soya curry", 330, 22.6, 7.2, 6.1, 0.2, 0.18),
    ("Egg Curry with Rice", "Boiled eggs in tomato gravy with rice", 400, 20.8, 2.9, 3.4, 3.2, 0.28),
    ("Tofu Stir Fry with Noodles", "Tofu, peppers and noodles", 380, 18.4, 5.6, 4.2, 0.3, 0.42),
]

SNACKS = [
    ("Mixed Nuts", "Almonds, walnuts and cashews", 50, 6.4, 2.8, 1.4, 0.2, 0.86),
    ("Fruit Bowl", "Seasonal fruits", 180, 1.8, 4.2, 0.9, 0.1, 0.06),
    ("Buttermilk", "Spiced yogurt drink", 200, 4.2, 0.2, 0.3, 0.6, 0.03),
    ("Roasted Chana", "Roasted chickpeas", 60, 5.8, 4.1, 2.2, 0.05, 0.04),
]

WATER_NOTES = ["Morning glass", "After breakfast", "Mid-morning", "With lunch",
               "Afternoon", "Evening", "With dinner", "Before bed"]

SYMPTOMS = [
    ("headache", 2, "Mild throbbing in the morning"),
    ("nausea", 3, "Felt queasy after breakfast"),
    ("fatigue", 2, "Tired by mid afternoon"),
    ("back pain", 3, "Lower back ache after sitting"),
    ("heartburn", 2, "Acidity after dinner"),
    ("swelling", 1, "Slight ankle swelling"),
    ("dizziness", 2, "Brief dizziness on standing"),
    ("insomnia", 3, "Trouble falling asleep"),
]

CONTEXTS = [
    {"time_of_day": "morning"},
    {"time_of_day": "afternoon", "after_meal": True},
    {"time_of_day": "evening"},
    {"time_of_day": "night"},
]


def resolve_uid(explicit_uid: str | None) -> tuple[str, str]:
    """
    Return (firebase_uid, user_doc_id) for the demo account.

    The UID must be the one the web client uses, which is stored on the user
    document by /user/link-account at login.
    """
    if explicit_uid:
        uid = explicit_uid
    else:
        matches = list(users_collection.where("email", "==", EMAIL).limit(1).stream())
        if not matches:
            raise SystemExit(
                f"No user document found for {EMAIL}.\n"
                "Log in to the web app once so /user/link-account creates it, "
                "then re-run this script (or pass --uid)."
            )
        doc = matches[0]
        uid = (doc.to_dict() or {}).get("firebase_uid")
        if not uid:
            raise SystemExit(
                f"User document {doc.id} has no firebase_uid yet.\n"
                "Log in to the web app once to backfill it, then re-run."
            )

    existing = list(users_collection.where("firebase_uid", "==", uid).limit(1).stream())
    if existing:
        doc_id = existing[0].id
        users_collection.document(doc_id).set(
            {"email": EMAIL, "phone": PHONE, "role": "mother", "firebase_uid": uid},
            merge=True,
        )
        print(f"  user doc        : {doc_id} (updated)")
        return uid, doc_id

    payload = {
        "email": EMAIL,
        "phone": PHONE,
        "role": "mother",
        "firebase_uid": uid,
        "created_at": datetime.now(timezone.utc),
    }
    _, ref = users_collection.add(payload)
    print(f"  user doc        : {ref.id} (created)")
    return uid, ref.id


def upsert_maternal_profile(user_doc_id: str):
    """Create or update the maternal profile linked to the user document."""
    profile = {
        "user_id": user_doc_id,
        "personal": {
            "age": 28,
            "height_cm": 163.0,
            "weight_kg": 62.5,
            "language": "en",
        },
        "pregnancy": {
            "stage": "trimester_2",
            "expected_delivery_date": (datetime.now(timezone.utc) + timedelta(days=120)).isoformat(),
            "gravida": 1,
            "para": 0,
            "known_conditions": [],
            "risk_level": "low",
        },
        "diet": {
            "type": "mixed",
            "diet_type": "mixed",
            # A couple of allergies so the allergy screen has content.
            "allergies": ["Peanuts", "Shellfish"],
        },
    }

    existing = list(maternal_profiles_collection.where("user_id", "==", user_doc_id).limit(1).stream())
    if existing:
        maternal_profiles_collection.document(existing[0].id).set(profile, merge=True)
        print(f"  maternal profile : {existing[0].id} (updated)")
        return existing[0].id

    profile["created_at"] = datetime.now(timezone.utc)
    _, ref = maternal_profiles_collection.add(profile)
    print(f"  maternal profile : {ref.id} (created)")
    return ref.id


def upsert_consent_and_status(user_doc_id: str):
    """Ensure consent and onboarding status documents exist and are complete."""
    consent = {
        "user_id": user_doc_id,
        "consents": {"data_usage": True, "medical_disclaimer": True},
        "accepted_at": datetime.now(timezone.utc),
    }
    existing = list(user_consent_collection.where("user_id", "==", user_doc_id).limit(1).stream())
    if existing:
        user_consent_collection.document(existing[0].id).set(consent, merge=True)
    else:
        user_consent_collection.add(consent)

    status_doc = {
        "user_id": user_doc_id,
        "steps": {"maternal_profile": True, "baby_profile": False, "consent": True},
        "completed_at": datetime.now(timezone.utc),
    }
    existing = list(onboarding_status_collection.where("user_id", "==", user_doc_id).limit(1).stream())
    if existing:
        onboarding_status_collection.document(existing[0].id).set(status_doc, merge=True)
    else:
        onboarding_status_collection.add(status_doc)

    print("  consent/status   : ready")


def clear_existing(user_id: str):
    """Remove previously seeded data so re-runs stay clean."""
    user_ref = firestoreDB.collection("users").document(user_id)
    total = 0
    for sub in ("meals", "water_logs", "medic_stones", "messages", "insights"):
        docs = list(user_ref.collection(sub).stream())
        for doc in docs:
            doc.reference.delete()
            total += 1
    print(f"  cleared {total} existing docs")


def seed_meals(user_id: str):
    """Write breakfast/lunch/dinner (+ some snacks) for each of the last DAYS days."""
    meals_ref = firestoreDB.collection("users").document(user_id).collection("meals")
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    count = 0

    for day_offset in range(DAYS):
        day = today - timedelta(days=day_offset)

        # Occasional gap so the insight engine has realistic "missed days".
        if day_offset in (7, 8, 19):
            continue

        plan = [
            (random.choice(BREAKFASTS), 8),
            (random.choice(LUNCHES), 13),
            (random.choice(SNACKS), 17),
            (random.choice(DINNERS), 20),
        ]

        for (name, desc, grams, protein, fiber, iron, vit_d, omega3), hour in plan:
            jitter = random.uniform(-0.15, 0.15)
            created = day.replace(hour=hour, minute=random.randint(0, 59)) + timedelta(minutes=int(jitter * 60))

            meals_ref.add({
                "name": name,
                "desc": desc,
                "amnt": float(grams),
                "analysis": {
                    "protein": round(protein * (1 + jitter), 2),
                    "fiber": round(fiber * (1 + jitter), 2),
                    # The schema stores iron in grams, not mg.
                    "iron": round(iron / 1000.0, 4),
                    "vitamin_d": round(vit_d, 2),
                    "omega_3": round(omega3, 3),
                    "omega_3_epa": round(omega3 * 0.4, 3),
                    "omega_3_dha": round(omega3 * 0.6, 3),
                },
                "created_at": created,
                "updated_at": created,
            })
            count += 1

    print(f"  meals            : {count} entries")


def seed_water(user_id: str):
    """Write several water logs per day."""
    water_ref = firestoreDB.collection("users").document(user_id).collection("water_logs")
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    count = 0

    for day_offset in range(DAYS):
        day = today - timedelta(days=day_offset)
        if day_offset in (11, 22):
            continue

        glasses = random.randint(5, 9)
        for i in range(glasses):
            created = day.replace(hour=7, minute=0) + timedelta(hours=i, minutes=random.randint(0, 50))
            water_ref.add({
                "amount_ml": float(random.choice([150, 200, 250, 250, 300, 400])),
                "note": WATER_NOTES[i % len(WATER_NOTES)],
                "created_at": created,
                "updated_at": created,
            })
            count += 1

    print(f"  water logs       : {count} entries")


def seed_symptoms(user_id: str):
    """Write symptoms across the period so reports and patterns have data."""
    stones_ref = firestoreDB.collection("users").document(user_id).collection("medic_stones")
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    count = 0

    for day_offset in range(DAYS):
        # Roughly every other day.
        if day_offset % 2 != 0:
            continue

        day = today - timedelta(days=day_offset)
        for _ in range(random.choice([1, 1, 2])):
            name, severity, description = random.choice(SYMPTOMS)
            reported = day.replace(hour=random.randint(7, 21), minute=random.randint(0, 59))

            stones_ref.add({
                "symptom_name": name,
                "severity": severity,
                "description": description,
                "context": random.choice(CONTEXTS),
                "trends": ["high_severity"] if severity >= 4 else [],
                "reported_at": reported,
                "created_at": reported,
                "updated_at": reported,
            })
            count += 1

    print(f"  symptoms         : {count} entries")


def main():
    parser = argparse.ArgumentParser(description="Seed the CareNest demo account")
    parser.add_argument(
        "--uid",
        default=None,
        help="Firebase UID used by the web client (defaults to the user doc's firebase_uid)",
    )
    args = parser.parse_args()

    print("\nSeeding CareNest demo account")
    print("=" * 52)

    firebase_uid, user_doc_id = resolve_uid(args.uid)
    upsert_maternal_profile(user_doc_id)
    upsert_consent_and_status(user_doc_id)

    # Meals/water/symptoms are stored under the *Firebase UID* because that is
    # what the web client sends on every request. Insights are cleared so they
    # regenerate from the fresh data.
    clear_existing(firebase_uid)
    seed_meals(firebase_uid)
    seed_water(firebase_uid)
    seed_symptoms(firebase_uid)

    print("=" * 52)
    print(f"Login : {EMAIL}")
    print(f"UID   : {firebase_uid}")
    print(f"Doc   : {user_doc_id}")
    print("Done.\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nSeeding failed: {exc}", file=sys.stderr)
        raise
