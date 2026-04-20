"""
Defines the core multi-agent workflow. Configures individual agents (Researcher, 
Screenwriter, File Writer), assigns their specific tools, and orchestrates 
their collaboration using the ADK's SequentialAgent pattern.
"""
import os
import logging
import google.cloud.logging
import google.auth

import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH
from a2a.types import AgentCard
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents import SequentialAgent, LoopAgent, ParallelAgent
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from google.adk.tools.langchain_tool import LangchainTool
from starlette.requests import Request
from starlette.responses import PlainTextResponse


cloud_logging_client = google.cloud.logging.Client()
cloud_logging_client.setup_logging()


model_name = os.environ.get('MODEL', 'gemini-2.5-flash')
public_url = os.environ.get('RESEARCHER_URL', 'http://localhost:8000')
use_vertex_ai = os.environ.get('GOOGLE_GENAI_USE_VERTEXAI', True)
project = os.environ.get('GOOGLE_CLOUD_PROJECT')
location = os.environ.get('GOOGLE_CLOUD_LOCATION', 'us-central1')

print(model_name)

# 1. Initialize the model object
llm_model = Gemini(
    model_name=model_name,
    vertexai=use_vertex_ai,
    project=project,
    location=location
)

# Tools

def append_to_state(
    tool_context: ToolContext, field: str, response: str
) -> dict[str, str]:
    """Append new output to an existing state key.

    Args:
        field (str): a field name to append to
        response (str): a string to append to the field

    Returns:
        dict[str, str]: {"status": "success"}
    """
    existing_state = tool_context.state.get(field, [])
    tool_context.state[field] = existing_state + [response]
    logging.info(f"[Added to {field}] {response}")
    return {"status": "success"}



# Agents

root_agent = Agent(
    name="wiki_researcher",
    model=llm_model,
    description="Answer research questions using Wikipedia.",
    instruction="""
    PROMPT:
    { PROMPT? }

    PLOT_OUTLINE:
    { PLOT_OUTLINE? }

    CRITICAL_FEEDBACK:
    { CRITICAL_FEEDBACK? }

    INSTRUCTIONS:
    - If there is a CRITICAL_FEEDBACK, use your wikipedia tool to do research to solve those suggestions
    - If there is a PLOT_OUTLINE, use your wikipedia tool to do research to add more historical detail
    - If these are empty, use your Wikipedia tool to gather facts about the person in the PROMPT
    - Use the 'append_to_state' tool to add your research to the field 'research'.
    - Summarize what you have learned.
    Now, use your Wikipedia tool to do research.
    """,
    generate_content_config=types.GenerateContentConfig(
        temperature=0,
    ),
    tools=[
        LangchainTool(tool=WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())),
        append_to_state,
    ],
)

researcher_agent_card = AgentCard(
    name=root_agent.name,
    url=public_url, 
    description="Answer research questions using Wikipedia.",
    version="1.0.0",
    capabilities={},
    skills=[],
    defaultInputModes=["text/plain"],
    defaultOutputModes=["text/plain"]
)

app = to_a2a(root_agent, agent_card=researcher_agent_card)

async def health_check(request: Request) -> PlainTextResponse:
    return PlainTextResponse("Agent is healthy and running!")

app.add_route("/", health_check, methods=["GET"])