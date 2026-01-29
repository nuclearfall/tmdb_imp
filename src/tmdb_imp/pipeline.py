import time
from .util import sha1_json
from .progress import load_completed_ids, record_success, record_error
from .config import REQUEST_DELAY
from .models import ResolveStatus
from .progress import progress_line

def event_id(ev):
    return sha1_json({
        "kind": ev.kind,
        "lb_url": ev.lb_url,
        "date": ev.date,
        "payload": ev.payload,
    })

def run(events, resolver, sink, *, dry_run=False, resume=True):
    events = list(events)
    completed = load_completed_ids() if resume else set()
    total = len(events)

    skipped = processed = 0

    for i, ev in enumerate(events, start=1):
        eid = event_id(ev)

        if resume and eid in completed:
            skipped += 1
            progress_line(i, total, "SKIPPED", ev.lb_url, cached=True)
            continue

        try:
            res = resolver.resolve(ev.lb_url)

            progress_line(
                i, total,
                res.status.value.upper(),
                ev.lb_url,
                cached=getattr(res, "cached", False),
            )

            if res.status != ResolveStatus.FOUND:
                record_error(ev, res.status.value)
                continue

            if dry_run:
                processed += 1
                continue

            ev.tmdb_id = res.tmdb_id
            ev.media_type = res.media_type
            sink.apply(ev)
            record_success(eid, ev)
            processed += 1

        except Exception as e:
            progress_line(i, total, "ERROR", ev.lb_url)
            record_error(ev, e)

        time.sleep(REQUEST_DELAY)

    print()
