import os
import argparse
from pathlib import Path
import tmdbsimple as tmdb

from .lb_session import ensure_lb_session
from .tmdb_session import ensure_tmdb_session
from .resolver import LetterboxdResolver, IMDbResolver, MultiResolver
from .csv_parser import load_event_rows
from .events import parse_events
from .sink import TMDBSink
from .pipeline import run
from .config import DEFAULT_COOKIE_JAR

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="lb_sync",
        description="Synchronize Letterboxd exports into TMDB (resume-safe).",
    )

    p.add_argument(
        "mode",
        choices=["watchlist", "likes", "ratings", "reviews", "list", "imdb-list"],
        help="Type of Letterboxd export being imported",
    )

    p.add_argument(
        "csv",
        type=Path,
        help="Path to Letterboxd CSV export",
    )

    p.add_argument(
        "--cookies",
        type=Path,
        default=DEFAULT_COOKIE_JAR,
        help="Letterboxd cookie jar (default: lb_cookies.json)",
    )

    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve and cache only; do not mutate TMDB",
    )

    p.add_argument(
        "--no-resume",
        action="store_true",
        help="Ignore progress cache and reprocess everything",
    )

    p.add_argument("--title", help="Title for created TMDB list")

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    tmdb.API_KEY = os.environ.get("TMDB_API_KEY")
    if not tmdb.API_KEY:
        parser.error("TMDB_API_KEY environment variable must be set")

    # Sessions
    lb_session = ensure_lb_session(args.cookies)
    tmdb_session_id = ensure_tmdb_session()

    # Load CSV
    list_meta, rows = load_event_rows(
        args.csv,
        is_list=(args.mode == "list"),
    )

    if args.mode == "watched":
        from .models import LBListMeta
        list_meta = LBListMeta(
            date=None,
            name="Watched",
            tags=[],
            url="__synthetic_watched__",
            description="Imported from Letterboxd watched history",
        )

    if args.mode == "imdb-list":
        if not args.title:
            print("[INFO] No --title supplied, using default 'IMDb Import'")
        from .models import LBListMeta
        list_meta = LBListMeta(
            date=None,
            name=args.title or "IMDb Import",
            tags=[],
            url=f"imdb:{args.title or 'import'}",
            description="Imported from IMDb",
        )

    if args.mode == "list" and not list_meta:
        raise RuntimeError("List mode but no list metadata found")

    resolver = MultiResolver(
        LetterboxdResolver(lb_session),
        IMDbResolver(tmdb.API_KEY),
    )

    sink = TMDBSink(
        tmdb_session_id,
        list_meta if args.mode in {"list", "imdb-list", "watched"} else None,
    )

    events = parse_events(args.mode, rows)

    run(
        events=events,
        resolver=resolver,
        sink=sink,
        dry_run=args.dry_run,
        resume=not args.no_resume,
    )

