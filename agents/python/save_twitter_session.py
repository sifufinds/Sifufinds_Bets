"""
Extracts X.com cookies from your real Chrome browser on macOS,
converts them to a Playwright storage_state, and uploads to GitHub Secrets.

You MUST be logged in to x.com in Chrome before running this.

Usage:
  GITHUB_TOKEN=ghp_... python save_twitter_session.py
"""
import base64
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path


# ── macOS Chrome cookie decryption ──────────────────────────────────────────

def _chrome_key() -> bytes:
    """Fetch Chrome's cookie encryption key from macOS Keychain."""
    result = subprocess.run(
        [
            "security", "find-generic-password",
            "-w",                        # print password only
            "-s", "Chrome Safe Storage",
            "-a", "Chrome",
        ],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError("Could not read Chrome key from Keychain. Is Chrome installed?")
    password = result.stdout.strip()
    # Chrome derives the AES key via PBKDF2
    import hashlib
    key = hashlib.pbkdf2_hmac(
        "sha1", password.encode("utf-8"), b"saltysalt", 1003, dklen=16
    )
    return key


def _decrypt_value(encrypted: bytes, key: bytes) -> str:
    """Decrypt a Chrome cookie value (AES-128-CBC with a fixed IV of spaces)."""
    if not encrypted:
        return ""
    # Chrome prefix: b"v10" (macOS)
    if encrypted[:3] == b"v10":
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        iv  = b" " * 16
        ct  = encrypted[3:]
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        dec = cipher.decryptor()
        raw = dec.update(ct) + dec.finalize()
        # Strip PKCS7 padding
        pad = raw[-1]
        return raw[:-pad].decode("utf-8", errors="replace")
    # Old-format unencrypted value
    return encrypted.decode("utf-8", errors="replace")


# ── extract cookies ──────────────────────────────────────────────────────────

COOKIE_DOMAINS = ("x.com", ".x.com", "twitter.com", ".twitter.com")

def _chrome_cookies_path() -> Path:
    """Find Chrome's Cookies SQLite file."""
    candidates = [
        Path.home() / "Library/Application Support/Google/Chrome/Default/Cookies",
        Path.home() / "Library/Application Support/Google/Chrome/Profile 1/Cookies",
        Path.home() / "Library/Application Support/Chromium/Default/Cookies",
        Path.home() / "Library/Application Support/BraveSoftware/Brave-Browser/Default/Cookies",
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(
        "Could not find Chrome Cookies file. "
        "Tried:\n" + "\n".join(str(c) for c in candidates)
    )


def get_x_cookies() -> list[dict]:
    cookies_db = _chrome_cookies_path()
    print(f"Reading cookies from: {cookies_db}")

    # Chrome locks the DB while running — copy it first
    tmp = Path(tempfile.mktemp(suffix=".db"))
    shutil.copy2(cookies_db, tmp)

    key = _chrome_key()
    rows = []
    try:
        con = sqlite3.connect(str(tmp))
        cur = con.cursor()
        cur.execute(
            "SELECT host_key, name, encrypted_value, path, expires_utc, is_secure, is_httponly "
            "FROM cookies WHERE host_key LIKE '%x.com' OR host_key LIKE '%twitter.com'"
        )
        rows = cur.fetchall()
        con.close()
    finally:
        tmp.unlink(missing_ok=True)

    result = []
    for host, name, enc_val, path, expires, secure, httponly in rows:
        value = _decrypt_value(enc_val, key)
        # Convert Chrome epoch (microseconds since 1601) → Unix seconds
        unix_exp = (expires / 1_000_000) - 11644473600 if expires > 0 else -1
        result.append({
            "name": name,
            "value": value,
            "domain": host,
            "path": path,
            "expires": unix_exp,
            "httpOnly": bool(httponly),
            "secure": bool(secure),
            "sameSite": "Lax",
        })

    return result


# ── build storage state ──────────────────────────────────────────────────────

def build_storage_state(cookies: list[dict]) -> dict:
    return {"cookies": cookies, "origins": []}


# ── GitHub secret upload ──────────────────────────────────────────────────────

def _upload_secret(token: str, repo: str, name: str, value: str) -> None:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/actions/secrets/public-key",
        headers={"Authorization": f"token {token}", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req) as r:
        pk_data = json.loads(r.read())

    try:
        from nacl import encoding, public
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "PyNaCl", "-q"])
        from nacl import encoding, public

    pk  = public.PublicKey(pk_data["key"].encode(), encoding.Base64Encoder)
    box = public.SealedBox(pk)
    encrypted = base64.b64encode(box.encrypt(value.encode())).decode()

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
        print(f"✓ GitHub secret '{name}' uploaded")
    else:
        print(f"✗ Secret upload HTTP {code}")


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    gh_token = os.getenv("GITHUB_TOKEN", "").strip()
    if not gh_token:
        # Try gh CLI
        result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            gh_token = result.stdout.strip()

    try:
        from cryptography.hazmat.primitives.ciphers import Cipher
    except ImportError:
        print("Installing cryptography...")
        subprocess.run([sys.executable, "-m", "pip", "install", "cryptography", "-q"])

    print("Extracting X.com cookies from Chrome...")
    cookies = get_x_cookies()
    if not cookies:
        print("\n✗ No X.com / Twitter cookies found in Chrome.")
        print("Make sure you are logged into x.com in Chrome and try again.")
        sys.exit(1)

    # Check for auth token
    names = {c["name"] for c in cookies}
    print(f"Found {len(cookies)} cookies: {sorted(names)}")

    if "auth_token" not in names:
        print("\n✗ 'auth_token' cookie not found — Chrome session may not be logged in.")
        print("Log in to x.com in Chrome, then re-run this script.")
        sys.exit(1)

    state     = build_storage_state(cookies)
    state_b64 = base64.b64encode(json.dumps(state).encode()).decode()

    out = Path(__file__).parent / "twitter_session_b64.txt"
    out.write_text(state_b64)
    print(f"\n✓ Session file: {out}  ({len(state_b64)} chars)")

    if gh_token:
        _upload_secret(gh_token, "sifufinds/Sifufinds_Bets", "TWITTER_SESSION", state_b64)
    else:
        print("\nNo GITHUB_TOKEN set — add the secret manually:")
        print("  Repo → Settings → Secrets → Actions → New secret")
        print("  Name: TWITTER_SESSION   Value: (contents of the file above)")


if __name__ == "__main__":
    main()
