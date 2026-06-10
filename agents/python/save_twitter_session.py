"""
One-time session saver — run once on your local Mac.
Opens a Chromium browser, logs into X, saves cookies as TWITTER_SESSION secret.

Usage:
  X_USERNAME=SifuFinds X_PASSWORD=yourpass X_EMAIL=info@sifufinds.com \
    GITHUB_TOKEN=ghp_... python save_twitter_session.py
"""
import asyncio
import base64
import json
import os
from pathlib import Path


async def main() -> None:
    from playwright.async_api import async_playwright, TimeoutError as PWTimeout

    username = os.environ.get("X_USERNAME", "SifuFinds")
    password = os.environ.get("X_PASSWORD", "")
    email    = os.environ.get("X_EMAIL", "info@sifufinds.com")
    gh_token = os.environ.get("GITHUB_TOKEN", "").strip()

    if not password:
        raise SystemExit("Set X_PASSWORD env var")

    print("Opening Chromium browser...")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=False,
            slow_mo=120,
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
            locale="en-US",
        )
        page = await context.new_page()

        print("Navigating to x.com...")
        await page.goto("https://x.com", wait_until="domcontentloaded", timeout=30_000)
        await page.wait_for_timeout(2_000)

        # Accept cookies if the banner is up
        for cookie_sel in ['button:has-text("Accept all cookies")', 'button:has-text("Accept")']:
            try:
                btn = page.locator(cookie_sel).first
                await btn.wait_for(state="visible", timeout=2_000)
                await btn.click()
                print("Accepted cookie banner")
                await page.wait_for_timeout(1_000)
                break
            except PWTimeout:
                pass

        # Fill username — the landing page uses placeholder="Email or username"
        # The /i/flow/login page uses autocomplete="username"
        username_sel = None
        for sel in [
            'input[placeholder="Email or username"]',
            'input[autocomplete="username"]',
            'input[name="text"]',
            'input[type="text"]',
        ]:
            try:
                inp = page.locator(sel).first
                await inp.wait_for(state="visible", timeout=4_000)
                username_sel = sel
                break
            except PWTimeout:
                pass

        if username_sel is None:
            shot = Path(__file__).parent / "x_debug_noselector.png"
            await page.screenshot(path=str(shot))
            print(f"Could not find username field. Screenshot: {shot}")
            print(f"URL: {page.url}")
            # Wait up to 60s for manual login then capture cookies
            print("\nBrowser is open. Please log in manually in the browser window.")
            print("After you reach the home feed, wait 5 seconds — cookies will be captured.")
            for _ in range(60):
                await page.wait_for_timeout(1_000)
                if "/home" in page.url:
                    break
            await _finish(context, browser, gh_token)
            return

        await page.locator(username_sel).first.fill(username)
        print(f"Filled username via {username_sel}")

        # Click Continue or Next
        for btn_text in ["Continue", "Next"]:
            try:
                btn = page.get_by_role("button", name=btn_text)
                await btn.wait_for(state="visible", timeout=3_000)
                await btn.click()
                print(f"Clicked '{btn_text}'")
                break
            except PWTimeout:
                pass

        await page.wait_for_timeout(2_000)

        # Optional: email/phone confirmation
        try:
            confirm = page.locator('input[data-testid="ocfEnterTextTextInput"]')
            await confirm.wait_for(timeout=3_000)
            print("Filling email/phone confirmation...")
            await confirm.fill(email)
            await page.get_by_role("button", name="Next").click()
            await page.wait_for_timeout(2_000)
        except PWTimeout:
            pass

        # Fill password
        pw_sel = None
        for sel in ['input[name="password"]', 'input[type="password"]']:
            try:
                inp = page.locator(sel).first
                await inp.wait_for(state="visible", timeout=8_000)
                pw_sel = sel
                break
            except PWTimeout:
                pass

        if pw_sel:
            await page.locator(pw_sel).first.fill(password)
            print("Filled password")
            # Click Log in
            for btn_text in ["Log in", "Login", "Sign in"]:
                try:
                    btn = page.get_by_role("button", name=btn_text)
                    await btn.wait_for(state="visible", timeout=3_000)
                    await btn.click()
                    print(f"Clicked '{btn_text}'")
                    break
                except PWTimeout:
                    pass
        else:
            print("Password field not found — waiting for manual login...")

        # Wait for home feed (up to 40s)
        print("Waiting for home feed...")
        for _ in range(40):
            await page.wait_for_timeout(1_000)
            if "/home" in page.url:
                print(f"Logged in — {page.url}")
                break
        else:
            shot = Path(__file__).parent / "x_debug_postlogin.png"
            await page.screenshot(path=str(shot))
            print(f"Timed out waiting for home. Current: {page.url}. Screenshot: {shot}")

        await _finish(context, browser, gh_token)


async def _finish(context, browser, gh_token: str) -> None:
    state     = await context.storage_state()
    state_b64 = base64.b64encode(json.dumps(state).encode()).decode()

    out = Path(__file__).parent / "twitter_session_b64.txt"
    out.write_text(state_b64)
    print(f"\n✓ Session saved: {out}  ({len(state_b64)} chars)")

    if gh_token:
        _upload_secret(gh_token, "TWITTER_SESSION", state_b64)
    else:
        print("\nNo GITHUB_TOKEN — add secret manually:")
        print("  Repo → Settings → Secrets → Actions → New secret")
        print("  Name: TWITTER_SESSION   Value: (contents of above file)")

    await context.close()
    await browser.close()


def _upload_secret(token: str, name: str, value: str) -> None:
    import base64 as _b64
    import urllib.request

    repo = "sifufinds/Sifufinds_Bets"

    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/actions/secrets/public-key",
        headers={"Authorization": f"token {token}", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req) as r:
        pk_data = json.loads(r.read())

    try:
        from nacl import encoding, public
    except ImportError:
        import subprocess, sys
        subprocess.run([sys.executable, "-m", "pip", "install", "PyNaCl", "-q"])
        from nacl import encoding, public

    pk  = public.PublicKey(pk_data["key"].encode(), encoding.Base64Encoder)
    box = public.SealedBox(pk)
    encrypted = _b64.b64encode(box.encrypt(value.encode())).decode()

    payload = json.dumps({"encrypted_value": encrypted, "key_id": pk_data["key_id"]}).encode()
    req2 = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/actions/secrets/{name}",
        data=payload, method="PUT",
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req2) as r:
        code = r.getcode()

    if code in (201, 204):
        print(f"✓ GitHub secret '{name}' uploaded OK")
    else:
        print(f"✗ Secret upload HTTP {code}")


if __name__ == "__main__":
    asyncio.run(main())
