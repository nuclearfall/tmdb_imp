from pathlib import Path

REQUEST_DELAY = 0.5

CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)

RESOLVE_CACHE = CACHE_DIR / "resolve_cache.json"
PROGRESS_LOG = CACHE_DIR / "progress.jsonl"
ERROR_LOG = CACHE_DIR / "errors.jsonl"
LIST_CACHE = CACHE_DIR / "tmdb_lists.json"

DEFAULT_COOKIE_JAR = Path("lb_cookies.json")
TMDB_SESSION_FILE = Path("tmdb_session.txt")
