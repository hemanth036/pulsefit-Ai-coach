# Copyright 2026 Google LLC
# Firestore tools for PulseCraft AI Coach

import json
from datetime import datetime, timezone
from google.cloud import firestore

# IMPORTANT: Hardcoded Project ID as requested to prevent Agent Platform runtime project number issues
PROJECT_ID = "qwiklabs-gcp-02-4dd59a379000"

def get_firestore_client() -> firestore.Client:
    return firestore.Client(project=PROJECT_ID)

def get_exercise_catalog(category: str = None, target_muscle: str = None) -> str:
    """Retrieve exercises from the Firestore exercise catalog.
    
    Args:
        category: Optional exercise category filter (e.g. Strength, Cardio, Core).
        target_muscle: Optional target muscle group filter (e.g. Chest, Legs, Abs, Biceps).
        
    Returns:
        JSON string listing matching exercises.
    """
    db = get_firestore_client()
    query = db.collection("exercises")
    
    if category:
        query = query.where("category", "==", category)
    if target_muscle:
        query = query.where("target_muscle", "==", target_muscle)
        
    docs = query.stream()
    exercises = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        exercises.append(data)
        
    if not exercises:
        return json.dumps({"message": "No matching exercises found in catalog."})
        
    return json.dumps(exercises, indent=2)

def log_workout(exercise_name: str, duration_minutes: int, calories_burned: float = 0.0, notes: str = "") -> str:
    """Log a completed workout activity to the user's Firestore workout history.
    
    Args:
        exercise_name: Name of the exercise or workout activity performed.
        duration_minutes: Duration of the exercise in minutes.
        calories_burned: Estimated total calories burned.
        notes: Optional notes on performance or effort.
        
    Returns:
        Status message confirming the workout was logged.
    """
    db = get_firestore_client()
    now_iso = datetime.now(timezone.utc).isoformat()
    
    doc_data = {
        "exercise_name": exercise_name,
        "duration_minutes": duration_minutes,
        "calories_burned": calories_burned,
        "notes": notes,
        "timestamp": now_iso
    }
    
    doc_ref = db.collection("workout_logs").add(doc_data)
    doc_id = doc_ref[1].id
    
    return json.dumps({
        "status": "success",
        "message": f"Logged workout '{exercise_name}' for {duration_minutes} minutes.",
        "log_id": doc_id,
        "timestamp": now_iso
    })

def get_workout_history() -> str:
    """Retrieve all previously logged workouts from Firestore.
    
    Returns:
        JSON string containing the user's workout log history.
    """
    db = get_firestore_client()
    docs = db.collection("workout_logs").order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
    
    history = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        history.append(data)
        
    if not history:
        return json.dumps({"message": "No workouts logged yet."})
        
    return json.dumps(history, indent=2)

def calculate_heart_rate_zones(age: int, resting_hr: int = 60) -> str:
    """Calculate target heart rate training zones using the Karvonen formula.
    
    Args:
        age: The user's age in years.
        resting_hr: Resting heart rate in beats per minute (default: 60).
        
    Returns:
        JSON string listing heart rate training zones and BPM ranges.
    """
    max_hr = 220 - age
    hrr = max_hr - resting_hr
    
    zones = {
        "max_heart_rate": max_hr,
        "resting_heart_rate": resting_hr,
        "zones": {
            "Zone 1 (Warm-up / Recovery)": f"{round(resting_hr + hrr * 0.50)} - {round(resting_hr + hrr * 0.60)} BPM",
            "Zone 2 (Fat Burn / Endurance)": f"{round(resting_hr + hrr * 0.60)} - {round(resting_hr + hrr * 0.70)} BPM",
            "Zone 3 (Aerobic / Fitness)": f"{round(resting_hr + hrr * 0.70)} - {round(resting_hr + hrr * 0.80)} BPM",
            "Zone 4 (Anaerobic / Performance)": f"{round(resting_hr + hrr * 0.80)} - {round(resting_hr + hrr * 0.90)} BPM",
            "Zone 5 (Peak Effort)": f"{round(resting_hr + hrr * 0.90)} - {max_hr} BPM",
        }
    }
    return json.dumps(zones, indent=2)

def fetch_public_exercise_ideas(limit: int = 5) -> str:
    """Fetch real exercise ideas from the public wger Workout Manager API (https://wger.de/api/v2/).
    
    Args:
        limit: Number of exercise ideas to retrieve (default: 5, max: 20).
        
    Returns:
        JSON string list of exercise names, categories, and targeted muscles from the public API.
    """
    import os
    import urllib.request
    
    api_key = os.environ.get("WGER_API_KEY")
    url = f"https://wger.de/api/v2/exerciseinfo/?limit={min(limit, 20)}"
    
    headers = {"User-Agent": "PulseCraft-AI-Coach/1.0"}
    if api_key:
        headers["Authorization"] = f"Token {api_key}"
        
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            
        exercises = []
        for item in data.get("results", []):
            translations = item.get("translations", [])
            name = next((t["name"] for t in translations if t.get("language") == 2 and t.get("name")), None)
            if not name and translations:
                name = translations[0].get("name")
            if not name:
                continue
                
            category = item.get("category", {}).get("name", "General")
            muscles = [m.get("name_en", m.get("name")) for m in item.get("muscles", []) if m.get("name_en") or m.get("name")]
            
            exercises.append({
                "name": name,
                "category": category,
                "target_muscles": muscles or ["General"],
            })
            
        return json.dumps(exercises[:limit], indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch public exercise data: {str(e)}"})

def geocode_address(address: str) -> str:
    """Turn a street address or city name into geographic coordinates (latitude, longitude) using Google Geocoding API.
    
    Args:
        address: The address or place name to geocode.
        
    Returns:
        JSON string with formatted address, latitude, and longitude.
    """
    import os
    import urllib.request
    import urllib.parse
    
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return json.dumps({"error": "GOOGLE_MAPS_API_KEY environment variable not set."})
        
    encoded_address = urllib.parse.quote(address)
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            
        if data.get("status") != "OK" or not data.get("results"):
            return json.dumps({"error": f"Geocoding failed with status: {data.get('status')}"})
            
        result = data["results"][0]
        location = result["geometry"]["location"]
        
        return json.dumps({
            "formatted_address": result.get("formatted_address"),
            "latitude": location.get("lat"),
            "longitude": location.get("lng")
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Geocoding API call failed: {str(e)}"})

def find_nearby_places(latitude: float, longitude: float, place_type: str = "gym", radius_meters: float = 5000.0) -> str:
    """Find nearby places (e.g. gym, park, fitness_center) around coordinates using Google Places API (New).
    
    Args:
        latitude: Latitude coordinate center.
        longitude: Longitude coordinate center.
        place_type: Type of place to search for (e.g. 'gym', 'park', 'fitness_center').
        radius_meters: Search radius in meters (default: 5000.0).
        
    Returns:
        JSON string listing nearby places with name, formatted address, and location.
    """
    import os
    import urllib.request
    
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return json.dumps({"error": "GOOGLE_MAPS_API_KEY environment variable not set."})
        
    url = "https://places.googleapis.com/v1/places:searchNearby"
    payload = json.dumps({
        "includedTypes": [place_type],
        "maxResultCount": 5,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "radius": radius_meters
            }
        }
    }).encode("utf-8")
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location"
    }
    
    req = urllib.request.Request(url, data=payload, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            
        places = []
        for p in data.get("places", []):
            places.append({
                "name": p.get("displayName", {}).get("text", "Unknown"),
                "address": p.get("formattedAddress"),
                "location": p.get("location")
            })
            
        if not places:
            return json.dumps({"message": f"No nearby places of type '{place_type}' found."})
            
        return json.dumps(places, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Places API call failed: {str(e)}"})

BUCKET_NAME = "pulsecraft-media-qwiklabs-gcp-02-4dd59a379000"

async def generate_exercise_image(exercise_name: str, tool_context: "ToolContext") -> str:
    """Generate a visual illustration or photo of a fitness exercise or equipment item using Gemini image model, save it as a session artifact, and upload it to Google Cloud Storage.
    
    Args:
        exercise_name: Name of the exercise, workout item, or equipment to generate an image for.
        
    Returns:
        JSON string containing status and the public Cloud Storage HTTPS URL of the generated image.
    """
    import uuid
    from google import genai
    from google.genai import types
    from google.cloud import storage

    client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
    prompt = f"A professional high-quality fitness illustration of {exercise_name}, clean aesthetic."
    
    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"]
            )
        )
        
        image_bytes = None
        mime_type = "image/jpeg"
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    image_bytes = part.inline_data.data
                    mime_type = part.inline_data.mime_type or "image/jpeg"
                    break
                    
        if not image_bytes:
            return json.dumps({"error": "No image data was generated by the model."})

        # 1. Save as artifact in Playground via tool_context
        filename = f"{exercise_name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:6]}.jpg"
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        await tool_context.save_artifact(filename=filename, artifact=artifact_part)


        # 2. Upload to public Cloud Storage bucket directly from memory
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type=mime_type)
        
        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
        
        return json.dumps({
            "status": "success",
            "exercise_name": exercise_name,
            "filename": filename,
            "public_url": public_url
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Image generation failed: {str(e)}"})


async def generate_exercise_video(exercise_name: str, tool_context: "ToolContext") -> str:
    """Generate a short video demonstration of an exercise or workout item using Google's Omni model (gemini-omni-flash-preview) in the global region, save it as a session artifact, and upload it to Google Cloud Storage.
    
    Args:
        exercise_name: Name of the exercise or fitness routine item to generate a video for.
        
    Returns:
        JSON string containing status and the public Cloud Storage HTTPS URL of the generated video.
    """
    import base64
    import uuid
    from google import genai
    from google.genai import types
    from google.cloud import storage

    client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
    prompt = f"A short video demonstration of the {exercise_name} exercise."
    
    try:
        interaction = client.interactions.create(
            model="gemini-omni-flash-preview",
            input=prompt,
            response_modalities=["text", "video"]
        )
        
        video_bytes = None
        mime_type = "video/mp4"
        
        if hasattr(interaction, "output_video") and interaction.output_video:
            mime_type = interaction.output_video.mime_type or "video/mp4"
            if interaction.output_video.data:
                d = interaction.output_video.data
                video_bytes = d if isinstance(d, bytes) else base64.b64decode(d)

        if not video_bytes and getattr(interaction, "steps", None):
            for step in interaction.steps:
                if hasattr(step, "outputs") and step.outputs:
                    for output in step.outputs:
                        v = getattr(output, "video", None) or (output if getattr(output, "type", None) == "video" else None)
                        if v and hasattr(v, "data") and v.data:
                            d = v.data
                            video_bytes = d if isinstance(d, bytes) else base64.b64decode(d)
                            if hasattr(v, "mime_type") and v.mime_type:
                                mime_type = v.mime_type
                            break
                if video_bytes:
                    break

        if not video_bytes:
            return json.dumps({"error": "No video data was generated by the model."})

        filename = f"{exercise_name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:6]}.mp4"
        
        # 1. Save artifact in Playground via tool_context
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
        await tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 2. Upload to public Cloud Storage bucket directly from memory
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type=mime_type)
        
        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
        
        return json.dumps({
            "status": "success",
            "exercise_name": exercise_name,
            "filename": filename,
            "public_url": public_url
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Video generation failed: {str(e)}"})





