# Copyright 2026 Google LLC
# Seed script for Firestore collection 'exercises'

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-02-4dd59a379000"

EXERCISES = [
    {
        "id": "ex_pushups",
        "name": "Push-ups",
        "category": "Strength",
        "target_muscle": "Chest",
        "difficulty": "Beginner",
        "calories_per_min": 8.0,
        "instructions": "Keep core tight, lower chest to floor, push up explosively."
    },
    {
        "id": "ex_squats",
        "name": "Squats",
        "category": "Strength",
        "target_muscle": "Legs",
        "difficulty": "Beginner",
        "calories_per_min": 7.5,
        "instructions": "Keep feet shoulder-width apart, lower hips back and down."
    },
    {
        "id": "ex_hiit_sprint",
        "name": "HIIT Sprint Intervals",
        "category": "Cardio",
        "target_muscle": "Full Body",
        "difficulty": "Advanced",
        "calories_per_min": 14.0,
        "instructions": "Sprint at full speed for 30s, jog for 30s. Repeat for 10 rounds."
    },
    {
        "id": "ex_plank",
        "name": "Plank",
        "category": "Core",
        "target_muscle": "Abs",
        "difficulty": "Intermediate",
        "calories_per_min": 4.5,
        "instructions": "Hold forearm plank position with straight spinal alignment."
    },
    {
        "id": "ex_bicep_curls",
        "name": "Dumbbell Bicep Curls",
        "category": "Strength",
        "target_muscle": "Biceps",
        "difficulty": "Beginner",
        "calories_per_min": 5.0,
        "instructions": "Keep elbows tucked, curl weights toward shoulders under control."
    }
]

def seed():
    db = firestore.Client(project=PROJECT_ID)
    print(f"Seeding Firestore collection 'exercises' in project '{PROJECT_ID}'...")
    
    collection_ref = db.collection("exercises")
    for item in EXERCISES:
        doc_id = item["id"]
        collection_ref.document(doc_id).set(item)
        print(f"  - Seeded exercise '{item['name']}' ({doc_id})")
        
    print("Firestore seeding complete! ✅")

if __name__ == "__main__":
    seed()
