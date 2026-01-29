import csv
from .models import LBListMeta


def load_event_rows(path, is_list=False):
    with open(path, newline="", encoding="utf-8") as f:
        if is_list:
            rows = list(csv.reader(f))
            meta, data = strip_header(rows)
            return meta, data
        else:
            return None, list(csv.DictReader(f))


def strip_header(rows):
    if not rows:
        return None, []

    if not rows[0][0].startswith("Letterboxd list export"):
        raise ValueError("Not a Letterboxd list export")

    if len(rows) < 6:
        raise ValueError("List export is too short to parse")

    meta_row = rows[2]
    meta = LBListMeta(
        date=meta_row[0],
        name=meta_row[1],
        tags=meta_row[2].split(",") if meta_row[2] else [],
        url=meta_row[3],
        description=meta_row[4] if len(meta_row) > 4 else "",
    )

    header = [h.strip() for h in rows[4]]
    data_rows = rows[5:]

    return meta, [dict(zip(header, r)) for r in data_rows]
