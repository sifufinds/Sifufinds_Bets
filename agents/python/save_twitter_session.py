"""
One-time session saver — run this ONCE on your local Mac.
Opens a visible browser, logs into X, and saves the session
as a base64 string uploaded directly to GitHub Secrets as TWITTER_SESSION.

Usage:
  X_USERNAME=SifuFinds X_PASSWORD=yourpass X_EMAIL=info@sifufinds.com \
    python save_twitter_session.py
"""
import asyncio
import base64
import json
import os
import sys
from pathlib import Path


async def main() -> None:
    from playwright.async_api import async_playwright

    username = os.environ["X_USERNAME"]
    password = os.environ["X_PASSWORD"]
    email    = os.getenv("X_EMAIL", username)

    print("Opening headed browser (visible — avoids X bot detection)...")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=False,
            slow_mo=150,
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()

        print("Navigating to X login page...")
        await page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded")

        # Username step
        await page.wait_for_selector('input[autocomplete="username"]', timeout=20_000)
        await page.fill('input[autocomplete="username"]', username)
        await page.get_by_role("button", name="Next").click()
        await page.wait_for_timeout(2_000)

        # Optional: email/phone confirmation
        try:
            confirm = page.locator('input[data-testid="ocfEnterTextTextInput"]')
            await confirm.wait_for(timeout=3_000)
            await confirm.fill(email)
            await page.get_by_role("button", name="Next").click()
            await page.wait_for_timeout(2_000)
        except Exception:
            pass

        # Password step
        await page.wait_for_selector('input[name="password"]', timeout=10_000)
        await page.fill('input[name="password"]', password)
        await page.get_by_role("button", name="Log in").click()

        print("Waiting for home feed...")
        try:
            await page.wait_for_url("**/home", timeout=30_000)
        except Exception:
            print(f"Current URL: {page.url}")
            print("Complete any 2FA/challenge in the browser window, then press Enter here.")
            input()

        print(f"Logged in — URL: {page.url}")

        state      = await context.storage_state()
        state_json = json.dumps(state)
        state_b64  = base64.b64encode(state_json.encode()).decode()

        out = Path(__file__).parent / "twitter_session_b64.txt"
        out.write_text(state_b64)
        print(f"\n✓ Session saved to: {out}")
        print(f"  Total length: {len(state_b64)} chars")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
