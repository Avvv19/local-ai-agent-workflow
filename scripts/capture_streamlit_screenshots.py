from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SCREENSHOT_DIR = ROOT / "docs" / "screenshots"
STREAMLIT_URL = "http://localhost:8501"


def save(page, name: str) -> None:
    page.screenshot(path=SCREENSHOT_DIR / name, full_page=True)


def main() -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    sample_text = (ROOT / "data" / "sample_requests" / "billing_05_missing_id.txt").read_text()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1100})
        page.goto(STREAMLIT_URL, wait_until="domcontentloaded")

        expect(page.get_by_text("Local AI Agent Workflow Automation System")).to_be_visible(
            timeout=30000
        )
        page.get_by_label("Document text").fill(sample_text)
        page.get_by_role("button", name="Run Workflow").click()
        expect(page.locator("span").filter(has_text="Needs Human Review").first).to_be_visible(
            timeout=30000
        )
        save(page, "process_result.png")

        page.get_by_role("tab", name="Review Queue").click()
        expect(page.get_by_text("Human Review Queue")).to_be_visible(timeout=30000)
        save(page, "review_queue.png")

        page.get_by_role("tab", name="History").click()
        expect(page.get_by_text("Workflow History")).to_be_visible(timeout=30000)
        save(page, "history.png")

        page.get_by_role("tab", name="Dashboard").click()
        expect(page.get_by_text("Metrics Dashboard")).to_be_visible(timeout=30000)
        expect(page.get_by_text("By routing decision")).to_be_visible(timeout=30000)
        save(page, "dashboard.png")

        browser.close()


if __name__ == "__main__":
    main()
