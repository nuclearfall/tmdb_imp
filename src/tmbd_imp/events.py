from .models import LBEvent

def parse_events(mode, rows):
    for r in rows:
        if mode == "watchlist":
            yield LBEvent("watchlist", r.get("Date"), r["Letterboxd URI"], {})
        elif mode == "likes":
            yield LBEvent("like", r.get("Date"), r["Letterboxd URI"], {})
        elif mode == "ratings":
            yield LBEvent("rating", r.get("Date"), r["Letterboxd URI"], {
                "rating": float(r["Rating"])
            })
        elif mode == "watched":
            yield LBEvent("watched", r.get("Date"), r["Letterboxd URI"], {})
        elif mode == "list":
            yield LBEvent("list", "", r["URL"], {"position": r["Position"]})
        elif mode == "imdb-list":
            tt = r.get("Title Type", "").lower()
            is_movie = tt == "movie"

            raw = r.get("Your Rating")
            rating = float(raw) if raw and raw.strip().isdigit() else None

            yield LBEvent(
                kind="list",
                date=r.get("Date Rated"),
                lb_url=r["Const"],  # imdb id
                payload={
                    "rating": rating,
                    "media_hint": "movie" if is_movie else "tv",
                    "source": "imdb",
                }
            )

