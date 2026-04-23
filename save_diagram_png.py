"""
save_diagram_png.py
-------------------
Uses Playwright to render MASBIO_Agent_Diagram.html and save a
high-resolution PNG — ready to paste into Word, PowerPoint, or any doc.

Usage:
    python save_diagram_png.py

Output:
    MASBIO_Agent_Diagram.png  (saved next to this script)
"""

from pathlib import Path
from playwright.sync_api import sync_playwright

HTML_FILE = Path(__file__).parent / "MASBIO_Agent_Diagram.html"
PNG_FILE  = Path(__file__).parent / "MASBIO_Agent_Diagram.png"


def main():
    print("Launching browser…")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 900})

        # Load the local HTML file
        page.goto(HTML_FILE.as_uri())

        # Wait for Mermaid to finish rendering the SVG
        page.wait_for_selector("#diagram-container svg", timeout=15_000)
        page.wait_for_timeout(1500)  # let fonts settle

        # Grab the diagram container element and screenshot just that
        container = page.locator("#diagram-container")
        container.screenshot(
            path=str(PNG_FILE),
            type="png",
            scale="device",       # native resolution
        )

        browser.close()

    print(f"Saved → {PNG_FILE}")
    print("You can now insert this PNG directly into Word or PowerPoint.")


if __name__ == "__main__":
    main()
