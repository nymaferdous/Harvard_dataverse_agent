"""
agent.py
--------
Harvard Dataverse Publishing Agent — powered by LangChain ReAct.

The agent reasons step-by-step to:
  1. Analyse the dataset file and auto-generate Dataverse-compliant metadata
  2. Search Dataverse to avoid publishing duplicates
  3. Create the dataset record (draft)
  4. Upload the data file
  5. Verify the upload
  6. Publish the dataset (with user confirmation)

Architecture:
    User request
        │
        ▼
    LangChain ReAct Agent (GPT-4o)
        │
        ├── Tool: generate_metadata   → reads file, calls LLM for metadata
        ├── Tool: search_dataverse    → checks for duplicates
        ├── Tool: create_dataset      → POST /api/dataverses/.../datasets
        ├── Tool: upload_file         → POST /api/datasets/.../add
        ├── Tool: get_dataset_info    → GET  /api/datasets/...
        └── Tool: publish_dataset     → POST /api/datasets/.../actions/:publish

Usage:
    python agent.py --file path/to/data.csv
    python agent.py --file path/to/data.csv --dry-run
    python agent.py --interactive
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Type

from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import BaseTool
from langchain_core.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, Field
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

from modules.dataverse_tools import get_dataverse_tools
from modules.metadata_generator import generate_dataverse_metadata, build_dataverse_metadata

console = Console()


# ---------------------------------------------------------------------------
# Metadata generation as a LangChain Tool
# ---------------------------------------------------------------------------

class GenerateMetadataInput(BaseModel):
    file_path: str = Field(description="Path to the dataset file to analyse.")
    author_name: str = Field(
        default=os.getenv("DATAVERSE_AUTHOR_NAME", ""),
        description="Author name for the dataset record.",
    )
    author_affiliation: str = Field(
        default=os.getenv("DATAVERSE_AUTHOR_AFFILIATION", ""),
        description="Author's institutional affiliation.",
    )
    contact_email: str = Field(
        default=os.getenv("DATAVERSE_CONTACT_EMAIL", ""),
        description="Contact email address for the dataset.",
    )


class GenerateMetadataTool(BaseTool):
    """Analyse a dataset file and generate Dataverse-compliant metadata JSON."""

    name: str = "generate_dataset_metadata"
    description: str = (
        "Analyse a dataset file (CSV, TXT, PDF) and generate a complete, "
        "Harvard Dataverse-compliant metadata JSON string. "
        "Returns a JSON string ready to pass to create_dataverse_dataset. "
        "Always call this FIRST before creating a dataset."
    )
    args_schema: Type[BaseModel] = GenerateMetadataInput

    def _run(
        self,
        file_path: str,
        author_name: str = "",
        author_affiliation: str = "",
        contact_email: str = "",
    ) -> str:
        try:
            metadata = generate_dataverse_metadata(
                file_path=file_path,
                author_name=author_name or os.getenv("DATAVERSE_AUTHOR_NAME", "Dataset Author"),
                author_affiliation=author_affiliation or os.getenv("DATAVERSE_AUTHOR_AFFILIATION", ""),
                contact_email=contact_email or os.getenv("DATAVERSE_CONTACT_EMAIL", "contact@example.com"),
            )
            return json.dumps(metadata, indent=2)
        except Exception as e:
            return f"ERROR generating metadata: {e}"

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Agent system prompt
# ---------------------------------------------------------------------------

AGENT_SYSTEM_PROMPT = """You are a Harvard Dataverse publishing agent — an expert in \
FAIR data principles, research data management, and the Harvard Dataverse API.

Your job is to help researchers publish datasets to Harvard Dataverse accurately and efficiently.

## Workflow you MUST follow for publishing:
1. **generate_dataset_metadata** — Analyse the file and generate metadata. Always do this first.
2. **search_dataverse** — Search for similar existing datasets to avoid duplicates.
3. **create_dataverse_dataset** — Create the dataset record using the generated metadata JSON.
4. **upload_file_to_dataset** — Upload the data file to the created dataset.
5. **get_dataset_info** — Verify the dataset looks correct before publishing.
6. **publish_dataverse_dataset** — Publish the dataset (only after confirming with the user).

## Rules:
- Always generate and review metadata BEFORE creating a dataset.
- Always search for duplicates before creating.
- Always verify with get_dataset_info before publishing.
- If any step fails, explain the error clearly and suggest a fix.
- Never skip the verification step.
- For dry runs, stop after get_dataset_info and do NOT call publish_dataverse_dataset.
- Be explicit about what each step did and what comes next.

## Available tools:
{tools}

## Tool names:
{tool_names}

## Format:
Use this exact format for every response:

Question: the input question you must answer
Thought: your reasoning about what to do next
Action: the tool name (must be one of [{tool_names}])
Action Input: the input to the tool
Observation: the result of the tool
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: I now know the final answer
Final Answer: the final answer to the original question

Begin!

Question: {input}
Thought: {agent_scratchpad}"""


# ---------------------------------------------------------------------------
# Agent builder
# ---------------------------------------------------------------------------

def build_agent(model: str = "claude-sonnet-4-6", dry_run: bool = False) -> AgentExecutor:
    """Construct and return the Dataverse publishing agent.

    Args:
        model: Anthropic model name.
        dry_run: If True, agent stops before publishing.

    Returns:
        A LangChain AgentExecutor.
    """
    llm = ChatAnthropic(model=model, temperature=0.0)

    tools = [GenerateMetadataTool()] + get_dataverse_tools()

    prompt = PromptTemplate.from_template(AGENT_SYSTEM_PROMPT)

    agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)

    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=12,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )

    print(f"[DataverseAgent] Agent ready (model={model}, dry_run={dry_run})")
    return executor


# ---------------------------------------------------------------------------
# High-level publish workflow
# ---------------------------------------------------------------------------

def publish_dataset(
    file_path: str,
    dry_run: bool = False,
    model: str = "claude-sonnet-4-6",
) -> str:
    """Run the full publish workflow for a single file.

    Args:
        file_path: Path to the dataset file to publish.
        dry_run: If True, creates the dataset and uploads but does NOT publish.
        model: Anthropic model.

    Returns:
        Final agent response string.
    """
    if not Path(file_path).exists():
        return f"ERROR: File not found at '{file_path}'"

    agent = build_agent(model=model, dry_run=dry_run)

    dry_run_note = " This is a DRY RUN — do NOT call publish_dataverse_dataset." if dry_run else ""

    task = (
        f"Please publish the dataset at '{file_path}' to Harvard Dataverse. "
        f"Follow the full workflow: generate metadata, check for duplicates, "
        f"create the dataset, upload the file, verify, then publish.{dry_run_note}"
    )

    console.print(Panel(
        f"[bold green]Publishing:[/bold green] {file_path}\n"
        f"[bold]Dry run:[/bold] {'Yes — will stop before publishing' if dry_run else 'No — will publish'}",
        title="Dataverse Publishing Agent",
        border_style="blue",
    ))

    result = agent.invoke({"input": task})
    return result.get("output", "No output returned.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def check_env() -> None:
    missing = []
    if not os.getenv("ANTHROPIC_API_KEY"):
        missing.append("ANTHROPIC_API_KEY")
    if not os.getenv("DATAVERSE_API_TOKEN"):
        missing.append("DATAVERSE_API_TOKEN")
    if missing:
        console.print(
            f"[bold red]Missing env vars:[/bold red] {', '.join(missing)}\n"
            "Set [cyan]ANTHROPIC_API_KEY[/cyan] and [cyan]DATAVERSE_API_TOKEN[/cyan] in your [cyan].env[/cyan] file."
        )
        sys.exit(1)


def run_interactive(model: str = "claude-sonnet-4-6") -> None:
    """Interactive agent session — ask anything about Dataverse publishing."""
    agent = build_agent(model=model)
    console.print(Panel(
        "[bold]Harvard Dataverse Publishing Agent[/bold]\n\n"
        "Ask me to publish a file, search for datasets, check metadata, or manage versions.\n"
        "Type [cyan]quit[/cyan] to exit.",
        title="Interactive Mode",
        border_style="blue",
    ))
    while True:
        try:
            user_input = console.input("\n[bold yellow]You:[/bold yellow] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Session ended.[/dim]")
            break
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            console.print("[dim]Goodbye![/dim]")
            break
        result = agent.invoke({"input": user_input})
        console.print(Panel(
            Markdown(result.get("output", "")),
            title="Agent",
            border_style="green",
        ))


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Harvard Dataverse Publishing Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--file", "-f", type=str, default=None,
                        help="Path to the dataset file to publish.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run the full workflow but stop before publishing.")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="Start interactive agent session.")
    parser.add_argument("--model", type=str, default="claude-sonnet-4-6",
                        help="Anthropic model to use (default: claude-sonnet-4-6).")
    parser.add_argument("--preview-metadata", type=str, default=None,
                        metavar="FILE",
                        help="Preview auto-generated metadata for a file without publishing.")
    return parser


def main():
    parser = build_arg_parser()
    args = parser.parse_args()
    check_env()

    if args.preview_metadata:
        console.print(Panel(
            f"Generating metadata preview for: [cyan]{args.preview_metadata}[/cyan]",
            title="Metadata Preview",
        ))
        from modules.rag_metadata_generator import generate_metadata_rag
        meta = generate_metadata_rag(args.preview_metadata, original_filename=args.preview_metadata)
        console.print_json(json.dumps(meta, indent=2))
        return

    if args.interactive:
        run_interactive(model=args.model)
        return

    if args.file:
        output = publish_dataset(
            file_path=args.file,
            dry_run=args.dry_run,
            model=args.model,
        )
        console.print(Rule("Final Answer"))
        console.print(Markdown(output))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
