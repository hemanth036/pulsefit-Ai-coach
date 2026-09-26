# PulseCraft AI Coach

> A personalized, interactive AI fitness & wellness coach built with Gemini on Vertex AI Agent Engine.

![PulseCraft AI Coach Demo](agent_demo.gif)

## Overview

**PulseCraft AI Coach** is an intelligent fitness assistant designed to help users calculate target training zones, discover exercises, log workouts, locate nearby gyms, and visualize exercise routines through AI-generated images and short video demonstrations. 

Built using Google's **Agent Development Kit (ADK)**, PulseCraft leverages Vertex AI Reasoning Engines, persistent Memory Bank storage, Cloud Firestore, Google Cloud Storage, and multi-modal media generation models.

---

## Capabilities & Architecture

### 🧠 Intelligent ReAct Agent & Memory Bank
* **Model**: Powered by `gemini-flash-latest` via the Google GenAI SDK.
* **Persistent Memory**: Uses **Vertex AI Memory Bank Service** (`VertexAiMemoryBankService`) to automatically load and remember user fitness goals, body metrics, dietary preferences, and allergy profiles across sessions (`load_memory`, `preload_memory`).

### 🗄️ Database & Storage Infrastructure
* **Google Cloud Firestore**: Real-time database hosting:
  * **Exercise Catalog** (`exercises` collection) via `get_exercise_catalog` with category and target muscle group filtering.
  * **User Workout Logs** (`workout_logs` collection) via `log_workout` and `get_workout_history`.
* **Google Cloud Storage**: Public media bucket (`pulsecraft-media-qwiklabs-gcp-02-4dd59a379000`) hosting generated images and video demonstrations accessible via public HTTPS URLs.

### 🎨 Multi-Modal Media Generation & Rich A2UI
* **Image Generation**: Uses `gemini-3.1-flash-lite-image` (`generate_exercise_image`) to generate fitness illustrations, saving them as Playground session artifacts and uploading them to Google Cloud Storage.
* **Video Generation**: Uses Google's Omni model `gemini-omni-flash-preview` (`generate_exercise_video`) in the global region to generate short video demonstrations of exercises, saving them as session artifacts and uploading to Google Cloud Storage.
* **Agent-to-User Interface (A2UI v0.8)**: Generates structured, responsive UI cards (`Card`, `Column`, `Row`, `Text`, `Image`) rendered directly in the web user interface via an after-model callback (`a2ui_callback`).

### 🧮 Code Execution & Location Services
* **Karvonen Heart Rate Calculator**: Executes Karvonen formula calculations in `AgentEngineSandboxCodeExecutor` (`calculate_heart_rate_zones`) to determine 5 distinct heart rate training zones based on age and resting HR.
* **Google Maps & Places APIs**: Integrates Google Geocoding API (`geocode_address`) and Google Places API New (`find_nearby_places`) to locate nearby gyms, parks, and fitness centers.
* **Public Fitness API**: Fetches exercise suggestions from the public **wger Workout Manager API** (`fetch_public_exercise_ideas`).
* **Utilities**: Simulated weather (`get_weather`) and timezone/clock lookup (`get_current_time`).

---

## Implemented vs. Planned Capabilities

| Capability | Status | Implementation Details |
| :--- | :--- | :--- |
| **Vertex AI Memory Bank** | ✅ Implemented | Persistent user profile and allergy memory across sessions |
| **Firestore Exercise Catalog & Logs** | ✅ Implemented | Query exercise catalog & persist workout logs |
| **GCS Public Bucket Media Host** | ✅ Implemented | Media storage for public HTTPS image/video URLs |
| **Imagen Image Generation** | ✅ Implemented | `gemini-3.1-flash-lite-image` exercise illustrations |
| **Omni Video Generation** | ✅ Implemented | `gemini-omni-flash-preview` video demonstration tool |
| **A2UI Rich Cards (v0.8)** | ✅ Implemented | Dynamic structured UI cards with `a2ui_callback` |
| **Agent Engine Code Sandbox** | ✅ Implemented | Python Karvonen heart rate training zone calculation |
| **Maps & Places Nearby Gym Finder** | ✅ Implemented | Google Geocoding & Places API integration |
| **Cloud Trace Telemetry Exporter** | 🚧 Planned, not yet implemented | OpenTelemetry / Cloud Trace exporting |

---

## Project Structure

```text
pulsecraft-ai-coach/
├── app/
│   ├── agent.py               # Root ReAct Agent definition, instructions & tool registration
│   ├── tools.py               # Firestore, GCS, Imagen, Omni, Maps & calculation tools
│   ├── a2ui_utils.py          # A2UI schema manager, sanitizer, and after_model_callback
│   ├── fast_api_app.py        # FastAPI server endpoints
│   └── app_utils/             # Agent runtime helpers
├── frontend/                  # React frontend web application
├── agents-cli-manifest.yaml   # Agents CLI configuration & deployment target
├── deployment_metadata.json   # Remote agent runtime & sandbox resource mappings
├── seed_firestore.py          # Seed script for initial exercise catalog
├── agent_demo.webm            # Recorded Playwright web demo video
├── agent_demo.gif             # Optimized looping demo GIF
└── pyproject.toml             # Python dependencies and project settings
```

---

## Local Setup & Execution

### Prerequisites
* Python 3.10+
* `uv` package manager
* `google-agents-cli`

### Installation

1. Install project dependencies:
   ```bash
   uv sync
   ```

2. Seed Firestore exercise catalog (optional):
   ```bash
   uv run python seed_firestore.py
   ```

3. Launch the local agent server & playground:
   ```bash
   agents-cli playground
   ```
   Or launch via ADK web UI:
   ```bash
   uv run adk web
   ```

---

## Deployment Instructions

Deploy the agent engine to Google Cloud Vertex AI Agent Runtime:

```bash
gcloud config set project <YOUR_PROJECT_ID>
agents-cli deploy
```

Deploy the frontend container to Google Cloud Run:

```bash
gcloud run deploy pulsecraft-frontend \
  --source . \
  --region us-east1 \
  --allow-unauthenticated \
  --set-env-vars="AGENT_ENGINE_RESOURCE_NAME=<YOUR_AGENT_ENGINE_RESOURCE_NAME>,AGENT_DIRECTORY=app"
```
