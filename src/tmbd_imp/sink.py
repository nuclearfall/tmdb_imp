import tmdbsimple as tmdb
from .util import load_json, save_json
from .config import LIST_CACHE


class TMDBSink:
    def __init__(self, session_id, list_meta):
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

    def apply(self, ev):
        if not ev.tmdb_id or not ev.media_type:
            raise ValueError("TMDBSink.apply() called with missing tmdb_id or media_type")

        mt = ev.media_type  # "movie" or "tv"

        # ---- Lists (media-agnostic, incl IMDb) ----
        if ev.kind == "list":
            if not self.list:
                raise RuntimeError("List event received but no TMDB list is configured")
            print(f"{ev.tmdb_id} of type {mt}")
            self.list.add_item(media_id=ev.tmdb_id, media_type=mt)

            # Optional rating (IMDb imports)
            if ev.payload and ev.payload.get("rating"):
                rating = round(float(ev.payload["rating"]), 1)
                if mt == "movie":
                    self.account.rated_movies(movie_id=ev.tmdb_id, value=rating)
                elif mt == "tv":
                    self.account.rated_tv(tv_id=ev.tmdb_id, value=rating)

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

        # ---- Ratings (movie vs tv split) ----
        if ev.kind == "rating":
            rating = round(ev.payload["rating"] * 2, 1)

            if mt == "movie":
                self.account.rated_movies(
                    movie_id=ev.tmdb_id,
                    value=rating,
                )
            elif mt == "tv":
                self.account.rated_tv(
                    tv_id=ev.tmdb_id,
                    value=rating,
                )
            else:
                raise ValueError(f"Unknown media_type: {mt}")

            return

        raise ValueError(f"Unhandled event kind: {ev.kind}")
