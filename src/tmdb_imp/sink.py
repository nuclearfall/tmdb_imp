import tmdbsimple as tmdb
import requests
from .util import load_json, save_json
from .config import LIST_CACHE

API_BASE = "https://api.themoviedb.org/3"

class TMDBSink:
    def __init__(self, session_id, list_meta):
        self.session_id = session_id
        self.api_key = tmdb.API_KEY

        self.account = tmdb.Account(session_id)
        self.account.info()

        self.list = None
        self.cache = load_json(LIST_CACHE, {})

        if list_meta:
            key = list_meta.url or list_meta.name
            self.list = tmdb.Lists(session_id=session_id)

            if key in self.cache:
                self.list.id = self.cache[key]
            else:
                resp = self.list.list_create(
                    name=list_meta.name,
                    description=list_meta.description or "Imported from Letterboxd",
                    language="en",
                )
                self.list.id = resp["list_id"]
                self.cache[key] = self.list.id
                save_json(LIST_CACHE, self.cache)

    # ---------- real TMDB rating writer ----------
    def _set_rating(self, media_type: str, tmdb_id: int, value: float):
        if not (0.5 <= value <= 10.0):
            raise ValueError(f"TMDB rating must be 0.5–10.0, got {value}")

        url = f"{API_BASE}/{media_type}/{tmdb_id}/rating"
        params = {
            "api_key": self.api_key,
            "session_id": self.session_id,
        }

        resp = requests.post(url, params=params, json={"value": value}, timeout=30)
        data = resp.json()

        if not resp.ok or not data.get("success"):
            raise RuntimeError(f"TMDB rating failed: {data}")

        return data

    # ---------- event applier ----------
    def apply(self, ev):
        if not ev.tmdb_id or not ev.media_type:
            raise ValueError("TMDBSink.apply() called with missing tmdb_id or media_type")

        mt = ev.media_type  # "movie" or "tv"

        # ---- Lists (media-agnostic, incl IMDb) ----
        if ev.kind == "list":
            if not self.list:
                raise RuntimeError("List event received but no TMDB list is configured")

            self.list.add_item(media_id=ev.tmdb_id, media_type=mt)

            # Optional rating
            if ev.payload and ev.payload.get("rating") is not None:
                # payload.rating is already in TMDB scale (0.5–10)
                self._set_rating(mt, ev.tmdb_id, float(ev.payload["rating"]))
            return

        # ---- Watchlist ----
        if ev.kind == "watchlist":
            self.account.watchlist(
                media_type=mt,
                media_id=ev.tmdb_id,
                watchlist=True,
            )
            return

        # ---- Watched (synthetic list) ----
        if ev.kind == "watched":
            if not self.list:
                raise RuntimeError("Watched event received but no TMDB list is configured")
            self.list.add_item(media_id=ev.tmdb_id)
            return

        # ---- Favorites / Likes ----
        if ev.kind == "like":
            self.account.favorite(
                media_type=mt,
                media_id=ev.tmdb_id,
                favorite=True,
            )
            return

        # ---- Ratings ----
        if ev.kind == "rating":
            # already converted to TMDB scale in sink earlier
            self._set_rating(mt, ev.tmdb_id, float(ev.payload["rating"]))
            return

        raise ValueError(f"Unhandled event kind: {ev.kind}")
