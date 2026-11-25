"""Anki-style SM-2 scheduler with learning steps."""
import time
from datetime import datetime

from . import db
from .cards import BY_LEVEL, CARDS, LEVELS, level_for_rating

LEARN_STEPS = [60, 600]          # 1 min, 10 min
RELEARN_STEPS = [600]            # 10 min
GRADUATE_IVL = 1.0               # days
EASY_IVL = 4.0
MIN_EASE = 1.3
DAY = 86400
LEARN_AHEAD = 20 * 60


def today():
    return datetime.now().strftime("%Y-%m-%d")


def _schedule(row, grade, now):
    """Return the new card state for grade 1=Again 2=Hard 3=Good 4=Easy."""
    s = dict(row) if row else {"state": "learning", "step": 0, "ease": 2.5, "interval": 0.0, "reps": 0, "lapses": 0}
    s["reps"] += 1
    if s["state"] in ("learning", "relearning"):
        steps = LEARN_STEPS if s["state"] == "learning" else RELEARN_STEPS
        if grade == 1:
            s["step"] = 0
            s["due"] = now + steps[0]
        elif grade == 2:
            s["due"] = now + steps[min(s["step"], len(steps) - 1)] * 1.5
        elif grade == 3:
            s["step"] += 1
            if s["step"] >= len(steps):
                ivl = GRADUATE_IVL if s["state"] == "learning" else max(1.0, s["interval"])
                s.update(state="review", step=0, interval=ivl, due=now + ivl * DAY)
            else:
                s["due"] = now + steps[s["step"]]
        else:
            ivl = EASY_IVL if s["state"] == "learning" else max(2.0, s["interval"] * 1.5)
            s.update(state="review", step=0, interval=ivl, due=now + ivl * DAY)
    else:  # review
        ivl = s["interval"]
        if grade == 1:
            s["lapses"] += 1
            s["ease"] = max(MIN_EASE, s["ease"] - 0.2)
            s.update(state="relearning", step=0, interval=max(1.0, ivl * 0.5), due=now + RELEARN_STEPS[0])
        elif grade == 2:
            s["ease"] = max(MIN_EASE, s["ease"] - 0.15)
            s["interval"] = max(ivl + 1, ivl * 1.2)
            s["due"] = now + s["interval"] * DAY
        elif grade == 3:
            s["interval"] = max(ivl + 1, ivl * s["ease"])
            s["due"] = now + s["interval"] * DAY
        else:
            s["ease"] += 0.15
            s["interval"] = max(ivl + 1, ivl * s["ease"] * 1.3)
            s["due"] = now + s["interval"] * DAY
    return s


def preview(row, now=None):
    now = now or time.time()
    return {g: _schedule(row, g, now)["due"] - now for g in (1, 2, 3, 4)}


def answer(uid, card_id, grade):
    now = time.time()
    row = db.q1("SELECT * FROM srs WHERE user_id=? AND card_id=?", uid, card_id)
    is_new = row is None
    s = _schedule(row, grade, now)
    db.ex("""INSERT INTO srs (user_id, card_id, state, step, ease, interval, reps, lapses, due, last, source)
             VALUES (?,?,?,?,?,?,?,?,?,?,?)
             ON CONFLICT(user_id, card_id) DO UPDATE SET state=excluded.state, step=excluded.step,
             ease=excluded.ease, interval=excluded.interval, reps=excluded.reps, lapses=excluded.lapses,
             due=excluded.due, last=excluded.last""",
          uid, card_id, s["state"], s["step"], s["ease"], s["interval"], s["reps"], s["lapses"], s["due"], now,
          row["source"] if row else "study")
    day = today()
    db.ex("INSERT INTO study_daily (user_id, day) VALUES (?,?) ON CONFLICT DO NOTHING", uid, day)
    db.ex("UPDATE study_daily SET reviews=reviews+1, new_count=new_count+? WHERE user_id=? AND day=?",
          1 if is_new else 0, uid, day)


def add_missed(uid, card_id):
    """Words missed in battle go straight into the review queue."""
    now = time.time()
    row = db.q1("SELECT due FROM srs WHERE user_id=? AND card_id=?", uid, card_id)
    if row is None:
        db.ex("INSERT INTO srs (user_id, card_id, due, source) VALUES (?,?,?,'battle')", uid, card_id, now)
    elif row["due"] > now:
        db.ex("UPDATE srs SET due=? WHERE user_id=? AND card_id=?", now, uid, card_id)


def user_level(uid):
    best = db.q1("SELECT MAX(rating) m FROM ratings WHERE user_id=?", uid)["m"] or db.START_RATING
    return best, level_for_rating(best)


def counts(uid):
    now = time.time()
    u = db.q1("SELECT new_per_day FROM users WHERE id=?", uid)
    d = db.q1("SELECT new_count FROM study_daily WHERE user_id=? AND day=?", uid, today())
    new_left = max(0, u["new_per_day"] - (d["new_count"] if d else 0))
    learning = db.q1("SELECT COUNT(*) n FROM srs WHERE user_id=? AND state!='review' AND reps>0 AND due<=?",
                     uid, now + LEARN_AHEAD)["n"]
    review = db.q1("SELECT COUNT(*) n FROM srs WHERE user_id=? AND state='review' AND due<=?", uid, now)["n"]
    missed = db.q1("SELECT COUNT(*) n FROM srs WHERE user_id=? AND reps=0 AND due<=?", uid, now)["n"]
    total = db.q1("SELECT COUNT(*) n FROM srs WHERE user_id=?", uid)["n"]
    mature = db.q1("SELECT COUNT(*) n FROM srs WHERE user_id=? AND state='review' AND interval>=21", uid)["n"]
    return {"new": new_left, "learning": learning, "review": review, "missed": missed,
            "total": total, "mature": mature, "deck_size": len(CARDS)}


def next_card(uid):
    now = time.time()
    c = counts(uid)
    # 1. learning/relearning due now, 2. battle-missed, 3. reviews, 4. new, 5. learn ahead
    row = (db.q1("SELECT * FROM srs WHERE user_id=? AND state!='review' AND reps>0 AND due<=? ORDER BY due LIMIT 1", uid, now)
           or db.q1("SELECT * FROM srs WHERE user_id=? AND reps=0 AND due<=? ORDER BY due LIMIT 1", uid, now)
           or db.q1("SELECT * FROM srs WHERE user_id=? AND state='review' AND due<=? ORDER BY due LIMIT 1", uid, now))
    kind = None
    if row:
        kind = "missed" if row["reps"] == 0 else row["state"]
        return row["card_id"], kind, preview(row if row["reps"] else None, now), c
    if c["new"] > 0:
        _, lv = user_level(uid)
        seen = {r["card_id"] for r in db.q("SELECT card_id FROM srs WHERE user_id=?", uid)}
        li = LEVELS.index(lv)
        order = [lv] + LEVELS[:li][::-1]
        for level in order:
            for card in BY_LEVEL[level]:
                if card["id"] not in seen:
                    return card["id"], "new", preview(None, now), c
    row = db.q1("SELECT * FROM srs WHERE user_id=? AND state!='review' AND due<=? ORDER BY due LIMIT 1",
                uid, now + LEARN_AHEAD)
    if row:
        return row["card_id"], row["state"], preview(row, now), c
    nxt = db.q1("SELECT MIN(due) d FROM srs WHERE user_id=?", uid)["d"]
    c["next_due"] = nxt
    return None, None, None, c
