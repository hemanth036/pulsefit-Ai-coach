# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

import json
from pathlib import Path
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from app.tools import (
    get_exercise_catalog,
    log_workout,
    get_workout_history,
    calculate_heart_rate_zones,
    fetch_public_exercise_ideas,
    geocode_address,
    find_nearby_places,
    generate_exercise_image,
    generate_exercise_video,
)


def get_code_executor():
    metadata_path = Path(__file__).parent.parent / "deployment_metadata.json"
    if not metadata_path.exists():
        metadata_path = Path("deployment_metadata.json")
        
    if metadata_path.exists():
        with open(metadata_path) as f:
            meta = json.load(f)
            
        sandbox_res = meta.get("sandbox_resource_name")
        if sandbox_res and sandbox_res != "None":
            return AgentEngineSandboxCodeExecutor(sandbox_resource_name=sandbox_res)
            
        pending_op = meta.get("pending_operation", {})
        op_name = pending_op.get("operation_name", "")
        if "/operations/" in op_name:
            engine_name = op_name.split("/operations/")[0]
            return AgentEngineSandboxCodeExecutor(agent_engine_resource_name=engine_name)
            
        runtime_id = meta.get("remote_agent_runtime_id")
        if runtime_id and runtime_id != "None":
            project = pending_op.get("project", "qwiklabs-gcp-02-4dd59a379000")
            location = pending_op.get("location", "us-east1")
            engine_name = f"projects/{project}/locations/{location}/reasoningEngines/{runtime_id}"
            return AgentEngineSandboxCodeExecutor(agent_engine_resource_name=engine_name)
            
    engine_name = "projects/qwiklabs-gcp-02-4dd59a379000/locations/us-east1/reasoningEngines/5735534236572581888"
    return AgentEngineSandboxCodeExecutor(agent_engine_resource_name=engine_name)


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        query: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


from google.adk.tools import load_memory, preload_memory
from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from app.a2ui_utils import a2ui_callback

schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

a2ui_instruction = schema_manager.generate_system_prompt(
    role_description="PulseCraft AI Coach, a personalized fitness & wellness coach assistant.",
    workflow_description="Analyze the request, call relevant tools to fetch real data or generate images, and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects. "
        "Always check and remember user health profiles, dietary preferences, and all user allergies "
        "(such as peanut, dairy, shellfish, or gluten allergies) using your memory bank so they are remembered "
        "and respected across all sessions."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=a2ui_instruction,
    code_executor=get_code_executor(),
    after_model_callback=a2ui_callback,
    tools=[
        load_memory,
        preload_memory,
        get_exercise_catalog,
        log_workout,
        get_workout_history,
        calculate_heart_rate_zones,
        fetch_public_exercise_ideas,
        generate_exercise_image,
        generate_exercise_video,
        geocode_address,
        find_nearby_places,
        get_weather,
        get_current_time,
    ],
)


from google.adk.memory import VertexAiMemoryBankService

PROJECT_ID = "qwiklabs-gcp-02-4dd59a379000"
AGENT_ENGINE_ID = "5735534236572581888"

memory_service = VertexAiMemoryBankService(
    project=PROJECT_ID,
    location="us-east1",
    agent_engine_id=AGENT_ENGINE_ID,
)

app = App(
    root_agent=root_agent,
    name="app",
)
object.__setattr__(app, "memory_service", memory_service)

