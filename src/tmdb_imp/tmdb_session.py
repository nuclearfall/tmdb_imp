import os
import webbrowser
import tmdbsimple as tmdb
from .config import TMDB_SESSION_FILE

def ensure_tmdb_session():
    if os.environ.get("TMDB_SESSION_ID"):
        return os.environ["TMDB_SESSION_ID"]

    if TMDB_SESSION_FILE.exists():
        return TMDB_SESSION_FILE.read_text().strip()

    auth = tmdb.Authentication()
    token = auth.token_new()["request_token"]
    webbrowser.open(f"https://www.themoviedb.org/authenticate/{token}")
    input("Approve TMDB access, then press ENTER...")
    sid = auth.session_new(request_token=token)["session_id"]
    TMDB_SESSION_FILE.write_text(sid)
    return sid
