"""
browser_publish.py
------------------
Playwright-based Harvard Dataverse browser automation.

Watches the agent fill in the Harvard Dataverse "New Dataset" web form
field by field — title, author, description, keywords, subject, time period,
contact email — then uploads your file and publishes, all visibly in Chrome.

Usage:
    python browser_publish.py --file path/to/data.csv
    python browser_publish.py --file path/to/data.csv --dry-run
    python browser_publish.py --file path/to/data.csv --slowmo 800

Requirements:
    pip install playwright
    playwright install chromium

Credentials are read from .env:
    DATAVERSE_USERNAME   — your Harvard Dataverse login email
    DATAVERSE_PASSWORD   — your Harvard Dataverse password
    DATAVERSE_ALIAS      — your personal dataverse alias
    DATAVERSE_AUTHOR_NAME, DATAVERSE_AUTHOR_AFFILIATION, DATAVERSE_CONTACT_EMAIL
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

from modules.rag_metadata_generator import generate_metadata_rag

console = Console()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_URL        = os.getenv("DATAVERSE_BASE_URL", "https://dataverse.harvard.edu")
USERNAME        = os.getenv("DATAVERSE_USERNAME", "")
PASSWORD        = os.getenv("DATAVERSE_PASSWORD", "")
ALIAS           = os.getenv("DATAVERSE_ALIAS", "")
AUTHOR_NAME     = os.getenv("DATAVERSE_AUTHOR_NAME", "")
AUTHOR_AFF      = os.getenv("DATAVERSE_AUTHOR_AFFILIATION", "")
CONTACT_EMAIL   = os.getenv("DATAVERSE_CONTACT_EMAIL", "")

DATAVERSE_SUBJECTS = {
    "Agricultural Sciences",
    "Arts and Humanities",
    "Astronomy and Astrophysics",
    "Business and Management",
    "Chemistry",
    "Computer and Information Science",
    "Earth and Environmental Sciences",
    "Engineering",
    "Law",
    "Mathematical Sciences",
    "Medicine, Health and Life Sciences",
    "Physics",
    "Social Sciences",
    "Other",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slow_type(locator, text: str, delay: int = 40):
    """Type text character by character so the UI registers each keystroke."""
    locator.click()
    locator.fill("")
    locator.type(text, delay=delay)


def _wait_and_click(page, selector: str, timeout: int = 15_000):
    page.wait_for_selector(selector, timeout=timeout)
    page.click(selector)


# ---------------------------------------------------------------------------
# Step functions
# ---------------------------------------------------------------------------

def step_login(page, base_url: str, username: str, password: str):
    console.print("  [cyan]→[/cyan] Navigating to login page…")
    page.goto(f"{base_url}/loginpage.xhtml", wait_until="networkidle")

    # Fill credentials
    page.fill('input[id*="credentialsForm"][id*="userName"], input[name*="userName"]', username)
    page.fill('input[id*="credentialsForm"][id*="password"], input[name*="password"]', password)

    # Submit
    page.click('button[id*="login"], input[id*="login"], button:has-text("Log In")')
    page.wait_for_load_state("networkidle")

    if "loginpage" in page.url:
        raise RuntimeError("Login failed — check DATAVERSE_USERNAME and DATAVERSE_PASSWORD in .env")
    console.print("  [green]✓[/green] Logged in successfully")


def step_navigate_to_dataverse(page, base_url: str, alias: str):
    console.print(f"  [cyan]→[/cyan] Opening your dataverse: [bold]{alias}[/bold]")
    page.goto(f"{base_url}/dataverse/{alias}", wait_until="networkidle")

    if page.locator('text="Page Not Found"').count() > 0:
        raise RuntimeError(
            f"Dataverse alias '{alias}' not found. "
            "Check DATAVERSE_ALIAS in .env matches your personal dataverse URL."
        )
    console.print("  [green]✓[/green] Dataverse page loaded")


def step_open_new_dataset_form(page):
    console.print("  [cyan]→[/cyan] Opening New Dataset form…")

    # Click "Add Data" dropdown
    page.wait_for_selector('button:has-text("Add Data"), a:has-text("Add Data")', timeout=10_000)
    page.click('button:has-text("Add Data"), a:has-text("Add Data")')
    time.sleep(0.5)

    # Click "New Dataset" menu item
    page.wait_for_selector('a:has-text("New Dataset"), li:has-text("New Dataset")', timeout=5_000)
    page.click('a:has-text("New Dataset")')
    page.wait_for_load_state("networkidle")
    console.print("  [green]✓[/green] New Dataset form opened")


def step_fill_title(page, title: str):
    console.print(f"  [cyan]→[/cyan] Filling title: [bold]{title}[/bold]")
    title_input = page.locator(
        'input[id*="title"]:not([id*="keyword"]):not([id*="author"]), '
        'input[placeholder*="Title"]'
    ).first
    title_input.wait_for(timeout=10_000)
    _slow_type(title_input, title)
    console.print("  [green]✓[/green] Title filled")


def step_fill_author(page, author_name: str, affiliation: str):
    console.print(f"  [cyan]→[/cyan] Filling author: [bold]{author_name}[/bold]")

    # Author name field
    author_input = page.locator(
        'input[id*="authorName"], input[placeholder*="Family Name, Given Name"]'
    ).first
    if author_input.count() > 0:
        _slow_type(author_input, author_name)

    # Affiliation field
    if affiliation:
        aff_input = page.locator(
            'input[id*="authorAffiliation"], input[placeholder*="Affiliation"]'
        ).first
        if aff_input.count() > 0:
            _slow_type(aff_input, affiliation)

    console.print("  [green]✓[/green] Author filled")


def step_fill_contact(page, contact_name: str, contact_email: str):
    console.print(f"  [cyan]→[/cyan] Filling contact: [bold]{contact_email}[/bold]")

    name_input = page.locator(
        'input[id*="datasetContact"][id*="Name"], '
        'input[placeholder*="Contact Name"]'
    ).first
    if name_input.count() > 0:
        _slow_type(name_input, contact_name)

    email_input = page.locator(
        'input[id*="datasetContact"][id*="Email"], '
        'input[placeholder*="Contact Email"]'
    ).first
    if email_input.count() > 0:
        _slow_type(email_input, contact_email)

    console.print("  [green]✓[/green] Contact filled")


def step_fill_description(page, description: str):
    console.print("  [cyan]→[/cyan] Filling description…")

    desc_area = page.locator(
        'textarea[id*="dsDescription"], textarea[id*="description"]'
    ).first
    if desc_area.count() == 0:
        # Some versions use a contenteditable div
        desc_area = page.locator('div[id*="dsDescription"] .ui-inputfield').first

    if desc_area.count() > 0:
        desc_area.click()
        desc_area.fill(description)

    console.print("  [green]✓[/green] Description filled")


def step_fill_subject(page, subject: str):
    console.print(f"  [cyan]→[/cyan] Selecting subject: [bold]{subject}[/bold]")

    # Subject is a multi-select listbox — find and click the right option
    subject_option = page.locator(
        f'select[id*="subject"] option:has-text("{subject}"), '
        f'li[data-label="{subject}"], '
        f'.ui-selectmanymenu li:has-text("{subject}")'
    ).first

    if subject_option.count() > 0:
        subject_option.click()
    else:
        # Try the select element directly
        select_el = page.locator('select[id*="subject"]').first
        if select_el.count() > 0:
            select_el.select_option(label=subject)

    console.print("  [green]✓[/green] Subject selected")


def step_fill_keywords(page, keywords: list[str]):
    console.print(f"  [cyan]→[/cyan] Adding keywords: {', '.join(keywords[:4])}")

    for i, kw in enumerate(keywords[:4]):  # Dataverse usually shows 4 keyword rows
        # Each keyword row has its own input
        kw_inputs = page.locator('input[id*="keywordValue"]')
        if i < kw_inputs.count():
            _slow_type(kw_inputs.nth(i), kw)
            # Click "Add" button to add another row (except last)
            if i < len(keywords) - 1 and i < 3:
                add_btn = page.locator(
                    'button[id*="keyword"][id*="Add"], '
                    'a[id*="keyword"][id*="add"]'
                ).first
                if add_btn.count() > 0:
                    add_btn.click()
                    time.sleep(0.3)

    console.print("  [green]✓[/green] Keywords filled")


def step_fill_time_period(page, start: str, end: str):
    if not start and not end:
        return
    console.print(f"  [cyan]→[/cyan] Setting time period: {start} – {end}")

    start_input = page.locator('input[id*="timePeriodCoveredStart"]').first
    end_input   = page.locator('input[id*="timePeriodCoveredEnd"]').first

    if start and start_input.count() > 0:
        _slow_type(start_input, start)
    if end and end_input.count() > 0:
        _slow_type(end_input, end)

    console.print("  [green]✓[/green] Time period filled")


def step_upload_file(page, file_path: str):
    console.print(f"  [cyan]→[/cyan] Uploading file: [bold]{Path(file_path).name}[/bold]")

    # Find file input (may be hidden — use set_input_files which bypasses visibility)
    file_input = page.locator('input[type="file"]').first
    file_input.set_input_files(str(Path(file_path).resolve()))

    # Wait for upload to register (progress bar or filename appearing)
    page.wait_for_timeout(2000)
    try:
        page.wait_for_selector(
            f'text="{Path(file_path).name}", .ui-fileupload-filename',
            timeout=30_000,
        )
    except Exception:
        pass  # Some versions don't show the name, continue anyway

    console.print("  [green]✓[/green] File uploaded")


def step_save_dataset(page):
    console.print("  [cyan]→[/cyan] Saving dataset…")
    save_btn = page.locator(
        'button:has-text("Save Dataset"), input[value="Save Dataset"]'
    ).first
    save_btn.click()
    page.wait_for_load_state("networkidle")

    # Check for validation errors
    errors = page.locator('.ui-message-error, .alert-danger').all()
    if errors:
        msgs = [e.inner_text() for e in errors[:3]]
        raise RuntimeError(f"Form validation errors:\n" + "\n".join(msgs))

    console.print("  [green]✓[/green] Dataset saved as DRAFT")


def step_publish_dataset(page):
    console.print("  [cyan]→[/cyan] Publishing dataset…")

    # Click Publish button
    pub_btn = page.locator(
        'button:has-text("Publish Dataset"), a:has-text("Publish Dataset")'
    ).first
    pub_btn.wait_for(timeout=15_000)
    pub_btn.click()

    # Confirm in the modal dialog
    time.sleep(1)
    confirm_btn = page.locator(
        'button:has-text("Continue"), button:has-text("Publish"), '
        '.ui-dialog button:has-text("Yes")'
    ).first
    if confirm_btn.count() > 0:
        confirm_btn.click()

    page.wait_for_load_state("networkidle")
    console.print("  [green]✓[/green] Dataset published!")


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def run_browser_publish(file_path: str, dry_run: bool = False, slowmo: int = 600):
    from playwright.sync_api import sync_playwright

    if not Path(file_path).exists():
        console.print(f"[red]ERROR:[/red] File not found: '{file_path}'")
        sys.exit(1)

    # Check required env vars
    missing = [k for k, v in {
        "DATAVERSE_USERNAME": USERNAME,
        "DATAVERSE_PASSWORD": PASSWORD,
        "DATAVERSE_ALIAS":    ALIAS,
    }.items() if not v]
    if missing:
        console.print(
            f"[red]Missing env vars:[/red] {', '.join(missing)}\n"
            "Add them to your .env file and try again."
        )
        sys.exit(1)

    # Generate metadata
    console.print(Panel(
        f"[bold]File:[/bold] {file_path}\n"
        f"[bold]Dry run:[/bold] {'Yes — will stop before publishing' if dry_run else 'No'}",
        title="[bold blue]Dataverse Browser Agent[/bold blue]",
        border_style="blue",
    ))

    console.print("\n[bold]Step 1/2:[/bold] Generating metadata with RAG pipeline…")
    metadata = generate_metadata_rag(
        file_path,
        author_name=AUTHOR_NAME,
        author_affiliation=AUTHOR_AFF,
        contact_email=CONTACT_EMAIL,
        original_filename=Path(file_path).name,
    )
    console.print(f"  [green]✓[/green] Title: [bold]{metadata['title']}[/bold]")
    console.print(f"  [green]✓[/green] Subject: {metadata['subject']}")
    console.print(f"  [green]✓[/green] Keywords: {', '.join(metadata['keywords'][:4])}")

    console.print("\n[bold]Step 2/2:[/bold] Filling Dataverse form in browser…\n")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=slowmo)
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        page = context.new_page()

        try:
            step_login(page, BASE_URL, USERNAME, PASSWORD)
            step_navigate_to_dataverse(page, BASE_URL, ALIAS)
            step_open_new_dataset_form(page)
            step_fill_title(page, metadata["title"])
            step_fill_author(page, AUTHOR_NAME or metadata.get("data_source", "Author"), AUTHOR_AFF)
            step_fill_contact(page, AUTHOR_NAME, CONTACT_EMAIL)
            step_fill_description(page, metadata["description"])
            step_fill_subject(page, metadata["subject"])
            step_fill_keywords(page, metadata["keywords"])
            step_fill_time_period(page, metadata["time_period_start"], metadata["time_period_end"])
            step_upload_file(page, file_path)

            if dry_run:
                console.print("\n[yellow]Dry run — stopping before save. Browser stays open for 30 s.[/yellow]")
                time.sleep(30)
            else:
                step_save_dataset(page)
                step_publish_dataset(page)

                # Show final URL
                console.print(f"\n[bold green]✅ Done![/bold green]")
                console.print(f"  Dataset URL: [cyan]{page.url}[/cyan]")
                console.print("  Browser will close in 15 seconds…")
                time.sleep(15)

        except Exception as exc:
            console.print(f"\n[red]✗ Error:[/red] {exc}")
            console.print("[dim]Browser stays open — press Ctrl+C to exit.[/dim]")
            try:
                input()
            except KeyboardInterrupt:
                pass

        finally:
            browser.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Fill Harvard Dataverse web form automatically using Playwright",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--file", "-f", required=True,
                        help="Path to the dataset file to publish")
    parser.add_argument("--dry-run", action="store_true",
                        help="Fill the form but stop before saving")
    parser.add_argument("--slowmo", type=int, default=600,
                        help="Milliseconds between actions (default: 600). "
                             "Lower = faster, higher = easier to watch.")
    args = parser.parse_args()
    run_browser_publish(args.file, dry_run=args.dry_run, slowmo=args.slowmo)


if __name__ == "__main__":
    main()
