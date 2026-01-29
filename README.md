# tmdb-imp

**tmdb-imp** is a command-line tool for importing film data from **Letterboxd and IMDb** into your **The Movie Database (TMDB)** account.

It reads CSV exports, resolves each title to the correct TMDB entry, and creates or updates TMDB lists and watchlists. The tool is designed to be **resume-safe** and **idempotent**, making it suitable for large personal archives and repeat sync workflows.

---

## Features

* Import **Letterboxd**:

  * watchlist
  * likes
  * ratings
  * reviews
  * lists
* Import **IMDb** lists
* Automatically create or update TMDB lists
* Resolve titles and IDs (Letterboxd → TMDB, IMDb → TMDB)
* Cache sessions and progress for safe re-runs
* Optional dry-run mode (no TMDB changes)

---

## Requirements

* Python **3.10+**
* A **TMDB account**
* CSV export data from Letterboxd or IMDb
* A **TMDB API key**

---

## Installation

```bash
git clone https://github.com/yourname/tmdb-imp.git
cd tmdb-imp
pip install -e .
```

Verify:

```bash
tmdb-imp --help
```

---

## Getting a TMDB API Key

1. Create or log into your account:
   [https://www.themoviedb.org/](https://www.themoviedb.org/)

2. Go to **Account Settings → API**:
   [https://www.themoviedb.org/settings/api](https://www.themoviedb.org/settings/api)

3. Click **Create** and choose *Developer*.

4. Complete the short form (personal use is fine).

5. Copy your **API Key (v3 auth)**.

---

## Set the API Key

You must set:

```bash
export TMDB_API_KEY="your_api_key_here"
```

Persist in zsh:

```bash
echo 'export TMDB_API_KEY="your_api_key_here"' >> ~/.zshrc
source ~/.zshrc
```

---

## Usage

```bash
tmdb-imp <mode> <csv> [options]
```

### Modes

| Mode      | Description                            |
| --------- | -------------------------------------- |
| watchlist | Letterboxd watchlist export            |
| likes     | Letterboxd likes export                |
| ratings   | Letterboxd ratings export              |
| reviews   | Letterboxd reviews export              |
| list      | Letterboxd list export (with metadata) |
| imdb-list | IMDb list CSV                          |

---

### Options

| Flag          | Description                                                |
| ------------- | ---------------------------------------------------------- |
| `--cookies`   | Path to Letterboxd cookie jar (default: `lb_cookies.json`) |
| `--dry-run`   | Resolve and cache only; do not modify TMDB                 |
| `--no-resume` | Ignore progress cache and reprocess everything             |
| `--title`     | Title for created TMDB list (used for `imdb-list`)         |

---

## Examples

### Import a Letterboxd list

```bash
tmdb-imp list my_list.csv
```

### Import your Letterboxd watchlist

```bash
tmdb-imp watchlist watchlist.csv
```

### Import IMDb list

```bash
tmdb-imp imdb-list imdb_watchlist.csv --title "IMDb Watchlist"
```

### Dry run (no TMDB changes)

```bash
tmdb-imp list films.csv --dry-run
```

### Re-run without resume cache

```bash
tmdb-imp ratings ratings.csv --no-resume
```

---

## What Happens

1. A TMDB session is created or reused.
2. List metadata is read (or synthesized for IMDb).
3. Each row is resolved to a TMDB ID.
4. Items are added to the TMDB list (unless `--dry-run` is used).

The pipeline is safe to re-run without duplicating items.

---

## Project Structure

```text
src/tmdb_imp/
├── cli.py
├── config.py
├── csv_parser.py
├── events.py
├── lb_login.py
├── lb_session.py
├── models.py
├── pipeline.py
├── progress.py
├── resolver.py
├── sink.py
├── tmdb_session.py
└── util.py
```

---

## Security

* Authentication/session files are excluded via `.gitignore`
* Your TMDB API key remains local in your environment
* No credentials are committed or transmitted outside official APIs

---

## License

MIT License
