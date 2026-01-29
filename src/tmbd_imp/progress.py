import json
import time
from .config import PROGRESS_LOG, ERROR_LOG

def load_completed_ids() -> set[str]:
    if not PROGRESS_LOG.exists():
        return set()
    return {
        json.loads(line)["event_id"]
        for line in PROGRESS_LOG.read_text().splitlines()
    }

def record_success(event_id, ev):
    with PROGRESS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "event_id": event_id,
            "kind": ev.kind,
            "lb_url": ev.lb_url,
            "tmdb_id": ev.tmdb_id,
            "media_type": ev.media_type,
            "ts": time.time(),
        }) + "\n")

def record_error(ev, err):
    with ERROR_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "kind": ev.kind,
            "lb_url": ev.lb_url,
            "payload": ev.payload,
            "error": str(err),
            "ts": time.time(),
        }) + "\n")

def progress_line(i, total, status, url, cached=False):
    tag = "CACHED" if cached else "LIVE"
    msg = f"[{i}/{total}] {status:<9} {tag:<6} {url}"
    print("\r" + msg[:120].ljust(120), end="", flush=True)

