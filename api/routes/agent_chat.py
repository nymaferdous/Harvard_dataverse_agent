"""
routes/agent_chat.py
--------------------
POST /api/v1/agent/chat

Natural language interface to the Dataverse publishing agent.
Send a plain-English instruction and the ReAct agent will figure
out which tools to call and execute the workflow.

Examples:
  "Search Dataverse for biomass datasets"
  "What datasets exist about US wood fuel production?"
  "Publish my FAOSTAT file to my Harvard Dataverse"
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

from fastapi import APIRouter
from api.models import AgentChatRequest, AgentChatResponse

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from agent import build_agent

router = APIRouter(prefix="/agent", tags=["Agent Chat"])

# Simple in-memory session store (swap for Redis in production)
_sessions: dict = {}


@router.post(
    "/chat",
    response_model=AgentChatResponse,
    summary="Chat with the Dataverse publishing agent",
    description=(
        "Send a natural language instruction to the ReAct agent. "
        "It will reason step-by-step and call the appropriate Dataverse API tools. "
        "Optionally pass a session_id to maintain conversational context."
    ),
)
def agent_chat(body: AgentChatRequest):
    session_id = body.session_id or str(uuid.uuid4())

    # Reuse existing agent for session, or create new one
    if session_id not in _sessions:
        _sessions[session_id] = build_agent()

    agent_executor = _sessions[session_id]

    result = agent_executor.invoke({"input": body.message})
    steps = result.get("intermediate_steps", [])

    return AgentChatResponse(
        success=True,
        session_id=session_id,
        answer=result.get("output", ""),
        steps_taken=len(steps),
    )
