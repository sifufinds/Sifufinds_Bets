"""
One-time session saver — run this ONCE on your local Mac.
Opens a visible browser, logs into X, and saves the session
as a base64 string you paste into GitHub Secrets as TWITTER_SESSION.

Usage:
  python save_twitter_session.py
"""
import asyncio
import base64
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")


async def main():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("Installing playwright...")
        os.system(f"{sys.executable} -m pip install playwright && playwright install chromium")
        from playwright.async_api import async_playwright

    username = os.getenv("X_USERNAME", "").strip() or input("X username: ").strip()
    password = os.getenv("X_PASSWORD", "").strip() or input("X password: ").strip()

    print("\nOpening browser (headed so X doesn't block us)...")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=False,   # visible — avoids bot detection
            slow_mo=200,
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

        print("Navigating to login page...")
        await page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded")

        # Username
        await page.wait_for_selector('input[autocomplete="username"]', timeout=20_000)
        await page.fill('input[autocomplete="username"]', username)
        await page.get_by_role("button", name="Next").click()
        await page.wait_for_timeout(2_000)

        # Possible email/phone confirmation step
        try:
            confirm = page.locator('input[data-testid="ocfEnterTextTextInput"]')
            await confirm.wait_for(timeout=3_000)
            email = os.getenv("X_EMAIL", "").strip() or input("X email/phone for confirmation: ").strip()
            await confirm.fill(email)
            await page.get_by_role("button", name="Next").click()
            await page.wait_for_timeout(2_000)
        except Exception:
            pass

        # Password
        await page.wait_for_selector('input[name="password"]', timeout=10_000)
        await page.fill('input[name="password"]', password)
        await page.get_by_role("button", name="Log in").click()

        print("Waiting for home page...")
        try:
            await page.wait_for_url("**/home", timeout=30_000)
        except Exception:
            print(f"Current URL: {page.url}")
            print("If you see a 2FA or challenge page, complete it in the browser window.")
            input("Press Enter once you're on the X home feed...")

        print(f"Logged in! URL: {page.url}")

        # Save full browser storage state
        state = await context.storage_state()
        state_json = json.dumps(state)
        state_b64 = base64.b64encode(state_json.encode()).decode()

        out_file = Path(__file__).parent / "twitter_session_b64.txt"
        out_file.write_text(state_b64)

        print(f"\n✓ Session saved to: {out_file}")
        print(f"\n--- COPY EVERYTHING BELOW THIS LINE ---")
        print(state_b64[:80] + "..." if len(state_b64) > 80 else state_b64)
        print(f"--- END (total {len(state_b64)} chars) ---")
        print("\nAdd this as a GitHub Secret named: TWITTER_SESSION")
        print("(Settings → Secrets → Actions → New repository secret)")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
