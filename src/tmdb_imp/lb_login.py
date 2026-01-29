# lb_login.py
import json
import re
from pathlib import Path
from curl_cffi import requests

BASE_URL = "https://letterboxd.com"
SIGNIN_URL = f"{BASE_URL}/sign-in/"
LOGIN_POST_URL = f"{BASE_URL}/user/login.do"
IMPERSONATE = "chrome120"


def debug_cookies(session, label):
    print(f"\n[DEBUG] Cookies after {label}:")
    jar = list(session.cookies.jar)
    if not jar:
        print("  (no cookies)")
        return
    for c in jar:
        v = c.value
        v_disp = (v[:60] + "...") if len(v) > 60 else v
        print(f"  {c.name}={v_disp} domain={c.domain} path={c.path} secure={bool(c.secure)}")


def debug_set_cookie(resp, label):
    print(f"\n[DEBUG] Set-Cookie headers in {label}:")
    found = False
    for k, v in resp.headers.items():
        if k.lower() == "set-cookie":
            found = True
            print(f"  {v}")
    if not found:
        # Some libs coalesce headers; still useful to print if present
        sc = resp.headers.get("set-cookie") or resp.headers.get("Set-Cookie")
        if sc:
            print(f"  {sc}")
        else:
            print("  (none)")


def dump_response(resp, label):
    print(f"\n[DEBUG] {label}")
    print(f"  Final URL: {resp.url}")
    print(f"  Status: {resp.status_code}")
    if resp.history:
        print("  Redirect chain:")
        for h in resp.history:
            print(f"    {h.status_code} → {h.url}")
    else:
        print("  Redirect chain: (none)")
    print(f"  Content length: {len(resp.text)}")
    # Don’t spam: just show a small snippet
    print(f"  Snippet: {resp.text[:140]!r}")


def is_logged_in_by_cookie(session) -> bool:
    names = {c.name for c in session.cookies.jar}
    # These are present in your known-good Playwright state.
    return any(n.startswith("letterboxd.user") for n in names) or ("letterboxd.signed.in.as" in names)


def lb_login(username: str, password: str, cookie_path=Path("lb_cookies.json")):
    print(f"[DEBUG] Starting session (impersonate={IMPERSONATE})")
    s = requests.Session(impersonate=IMPERSONATE)

    # 1) GET sign-in page (sets csrf cookie)
    print("\n[DEBUG] STEP 1 — GET sign-in")
    r = s.get(SIGNIN_URL, allow_redirects=True)
    r.raise_for_status()
    dump_response(r, "GET /sign-in/")
    debug_set_cookie(r, "GET /sign-in/")
    debug_cookies(s, "GET /sign-in/")

    # CSRF token comes from cookie in the known working approach
    csrf = s.cookies.get("com.xk72.webparts.csrf")
    print(f"\n[DEBUG] CSRF cookie com.xk72.webparts.csrf = {csrf!r}")
    if not csrf:
        raise RuntimeError("Missing CSRF cookie after GET /sign-in/")

    # 2) POST login to the actual login endpoint
    print("\n[DEBUG] STEP 2 — POST /user/login.do")
    form = {
        "__csrf": csrf,          # IMPORTANT
        "username": username,
        "password": password,
        "remember": "true",
    }

    headers = {
        "Referer": SIGNIN_URL,
        "Origin": BASE_URL,
    }

    # Debug form keys without leaking password
    print(f"[DEBUG] POST URL: {LOGIN_POST_URL}")
    print(f"[DEBUG] POST form keys: {list(form.keys())} (password redacted)")
    pr = s.post(LOGIN_POST_URL, data=form, headers=headers, allow_redirects=True)
    pr.raise_for_status()
    dump_response(pr, "POST /user/login.do")
    debug_set_cookie(pr, "POST /user/login.do")
    debug_cookies(s, "POST /user/login.do")

    # 3) Validate
    print("\n[DEBUG] STEP 3 — Validate via /activity/")
    act = s.get(f"{BASE_URL}/activity/", allow_redirects=True)
    act.raise_for_status()
    dump_response(act, "GET /activity/")
    debug_set_cookie(act, "GET /activity/")
    debug_cookies(s, "GET /activity/")

    if is_logged_in_by_cookie(s):
        print("\n[DEBUG] ✅ Logged in (cookie-based check)")
    else:
        print("\n[DEBUG] ❌ Not logged in (cookie-based check)")
        print("[DEBUG] You should see letterboxd.user* cookies if auth succeeded.")

    # 4) Export cookies
    cookies = []
    for c in s.cookies.jar:
        cookies.append({
            "name": c.name,
            "value": c.value,
            "domain": c.domain,
            "path": c.path,
            "secure": bool(c.secure),
        })

    print(f"\n[DEBUG] Captured {len(cookies)} cookies total")
    with open(str(cookie_path), "w", encoding="utf-8") as f:
        json.dump(cookies, f, indent=2)
    print(f"[DEBUG] Wrote cookies to {str(cookie_path)}")
    return s


def main(l, p):
    login(l, p)

if __name__ == "__main__":
    import getpass
    u = input("Letterboxd username: ").strip()
    p = getpass.getpass("Letterboxd password: ")
    main(u, p)
