import re
import time
from bs4 import BeautifulSoup
from .models import ResolveResult, ResolveStatus
from .config import RESOLVE_CACHE
from .util import load_json, save_json


class MultiResolver:
    def __init__(self, lb, imdb):
        self.lb = lb
        self.imdb = imdb

    def resolve(self, src):
        if src.startswith("tt"):
            return self.imdb.resolve(src)
        if "boxd.it" in src or "letterboxd.com" in src:
            return self.lb.resolve(src)
        raise ValueError(f"Unknown source: {src}")


class LetterboxdResolver:
    def __init__(self, session):
        self.session = session
        self.cache = load_json(RESOLVE_CACHE, {})

    def resolve(self, lb_url: str) -> ResolveResult:
        url = lb_url.rstrip("/")
        cached = self.cache.get(url)

        # ---- CACHE HIT ----
        if cached and cached["status"] in {"found", "not_found", "blocked"}:
            res = ResolveResult(
                ResolveStatus(cached["status"]),
                cached.get("tmdb_id"),
                cached.get("media_type"),
                url,
            )
            res.cached = True
            return res

        # ---- LIVE FETCH ----
        r = self.session.get(url, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")

        footer = soup.select_one("p.text-link.text-footer")
        if not footer:
            return self._cache(url, ResolveStatus.NOT_FOUND)

        for a in footer.find_all("a", href=True):
            if "themoviedb.org" in a["href"]:
                m = re.search(r"/(movie|tv)/(\d+)", a["href"])
                if m:
                    return self._cache(
                        url,
                        ResolveStatus.FOUND,
                        int(m.group(2)),
                        m.group(1),
                    )

        return self._cache(url, ResolveStatus.NOT_FOUND)

    def _cache(self, url, status, tmdb_id=None, media_type=None):
        self.cache[url] = {
            "status": status.value,
            "tmdb_id": tmdb_id,
            "media_type": media_type,
            "ts": time.time(),
        }
        save_json(RESOLVE_CACHE, self.cache)

        res = ResolveResult(status, tmdb_id, media_type, url)
        res.cached = False
        return res


class IMDbResolver:
    def __init__(self, api_key):
        self.api_key = api_key

    def resolve(self, imdb_id):
        import tmdbsimple as tmdb
        tmdb.API_KEY = self.api_key

        r = tmdb.Find(imdb_id)
        res = r.info(external_source="imdb_id")

        if res.get("movie_results"):
            m = res["movie_results"][0]
            out = ResolveResult(ResolveStatus.FOUND, m["id"], "movie", imdb_id)
            out.cached = False
            return out

        if res.get("tv_results"):
            t = res["tv_results"][0]
            out = ResolveResult(ResolveStatus.FOUND, t["id"], "tv", imdb_id)
            out.cached = False
            return out

        out = ResolveResult(ResolveStatus.NOT_FOUND, None, None, imdb_id)
        out.cached = False
        return out
