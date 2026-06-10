"""Temporary: inject X cookies from env vars, test session, upload to GitHub."""
import asyncio, base64, json, os, urllib.request
from pathlib import Path

async def run():
    from playwright.async_api import async_playwright, TimeoutError as PWT

    auth_token = os.environ["X_AUTH_TOKEN"]
    ct0        = os.environ["X_CT0"]
    twid       = os.environ["X_TWID"]
    gh_token   = os.environ["GITHUB_TOKEN"]

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox","--disable-setuid-sandbox","--disable-dev-shm-usage",
                  "--disable-blink-features=AutomationControlled"],
        )
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width":1280,"height":900},
            locale="en-US",
        )
        await ctx.add_init_script("""
            Object.defineProperty(navigator,'webdriver',{get:()=>undefined});
            Object.defineProperty(navigator,'languages',{get:()=>['en-US','en']});
            Object.defineProperty(navigator,'plugins',{get:()=>[1,2,3,4,5]});
            window.chrome={runtime:{}};
        """)
        await ctx.add_cookies([
            {"name":"auth_token","value":auth_token,"domain":".x.com","path":"/","httpOnly":True,"secure":True,"sameSite":"None"},
            {"name":"ct0",       "value":ct0,       "domain":".x.com","path":"/","httpOnly":False,"secure":True,"sameSite":"Lax"},
            {"name":"twid",      "value":twid,      "domain":".x.com","path":"/","httpOnly":False,"secure":True,"sameSite":"None"},
        ])

        page = await ctx.new_page()
        print("Loading x.com/home...")
        await page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(4000)
        print(f"URL: {page.url}")

        if "/home" not in page.url:
            await page.screenshot(path="agents/python/auth_test.png")
            print("Not on home — cookies may be expired")
            await browser.close()
            return

        print("Authenticated on home feed!")
        state = await ctx.storage_state()
        names = [c["name"] for c in state["cookies"]]
        print(f"Cookies in session: {names}")
        b64 = base64.b64encode(json.dumps(state).encode()).decode()
        print(f"Session: {len(b64)} chars")

        repo = "sifufinds/Sifufinds_Bets"
        req  = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/actions/secrets/public-key",
            headers={"Authorization":f"token {gh_token}","Accept":"application/vnd.github+json"},
        )
        with urllib.request.urlopen(req) as r:
            pk = json.loads(r.read())
        from nacl import encoding, public
        key = public.PublicKey(pk["key"].encode(), encoding.Base64Encoder)
        enc = base64.b64encode(public.SealedBox(key).encrypt(b64.encode())).decode()
        payload = json.dumps({"encrypted_value":enc,"key_id":pk["key_id"]}).encode()
        req2 = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/actions/secrets/TWITTER_SESSION",
            data=payload, method="PUT",
            headers={"Authorization":f"token {gh_token}","Accept":"application/vnd.github+json","Content-Type":"application/json"},
        )
        with urllib.request.urlopen(req2) as r:
            code = r.getcode()
        print(f"TWITTER_SESSION: HTTP {code} {'OK' if code in (201,204) else 'FAILED'}")
        await ctx.close()
        await browser.close()

asyncio.run(run())
