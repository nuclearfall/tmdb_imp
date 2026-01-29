import json
import getpass
from pathlib import Path
from curl_cffi import requests
from .lb_login import lb_login, is_logged_in_by_cookie, IMPERSONATE

def ensure_lb_session(cookie_path: Path):
    s = requests.Session(impersonate=IMPERSONATE)
    if cookie_path.exists():
        for c in json.loads(cookie_path.read_text()):
            s.cookies.set(**c)
        if is_logged_in_by_cookie(s):
            print("[OK] Using existing Letterboxd cookies")
            return s

    print("[ACTION] Letterboxd login required")
    u = input("Username: ")
    p = getpass.getpass("Password: ")
    return lb_login(u, p)
