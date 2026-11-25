import asyncio
import json
import re
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import db, srs
from .cards import CARDS, LEVELS, BY_LEVEL, card_reveal, correct_answer_text, furi_tier
from .game import TC, hub, manager

STATIC = Path(__file__).resolve().parent.parent / "static"
COOKIE = "arena_session"


@asynccontextmanager
async def lifespan(app):
    task = asyncio.create_task(manager.pair_loop())
    yield
    task.cancel()


app = FastAPI(title="Nihongo Arena", lifespan=lifespan)


def current_user(req: Request):
    return db.user_from_token(req.cookies.get(COOKIE))


def require_user(req: Request):
    u = current_user(req)
    if not u:
        raise HTTPException(401, "Not logged in")
    return u


def user_public(u):
    r = db.ratings_for(u["id"])
    return {"id": u["id"], "username": u["username"], "lang": u["lang"], "new_per_day": u["new_per_day"],
            "ratings": {tc: {"rating": round(v["rating"]), "games": v["games"], "wins": v["wins"],
                             "losses": v["losses"], "draws": v["draws"]} for tc, v in r.items()}}


class Creds(BaseModel):
    username: str
    password: str


@app.post("/api/register")
def register(c: Creds, resp: Response):
    name = c.username.strip()
    if not re.fullmatch(r"[A-Za-z0-9_\-]{3,20}", name):
        raise HTTPException(400, "Username must be 3–20 characters: letters, numbers, _ or -")
    if name.lower().startswith("bot"):
        raise HTTPException(400, "Usernames starting with 'bot' are reserved")
    if len(c.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    if db.q1("SELECT 1 FROM users WHERE username=?", name):
        raise HTTPException(400, "That username is taken")
    uid = db.create_user(name, c.password)
    resp.set_cookie(COOKIE, db.new_session(uid), httponly=True, samesite="lax", max_age=60 * 60 * 24 * 365)
    return user_public(db.q1("SELECT * FROM users WHERE id=?", uid))


@app.post("/api/login")
def login(c: Creds, resp: Response):
    u = db.check_login(c.username.strip(), c.password)
    if not u:
        raise HTTPException(400, "Wrong username or password")
    resp.set_cookie(COOKIE, db.new_session(u["id"]), httponly=True, samesite="lax", max_age=60 * 60 * 24 * 365)
    return user_public(u)


@app.post("/api/logout")
def logout(req: Request, resp: Response):
    tok = req.cookies.get(COOKIE)
    if tok:
        db.ex("DELETE FROM sessions WHERE token=?", tok)
    resp.delete_cookie(COOKIE)
    return {"ok": True}


@app.get("/api/me")
def me(req: Request):
    u = current_user(req)
    return {"user": user_public(u) if u else None, "stats": manager.stats(),
            "time_controls": TC, "study": srs.counts(u["id"]) if u else None}


class Settings(BaseModel):
    lang: str | None = None
    new_per_day: int | None = None


@app.post("/api/settings")
def settings(s: Settings, req: Request):
    u = require_user(req)
    if s.lang in ("en", "sv"):
        db.ex("UPDATE users SET lang=? WHERE id=?", s.lang, u["id"])
    if s.new_per_day is not None:
        db.ex("UPDATE users SET new_per_day=? WHERE id=?", max(0, min(100, s.new_per_day)), u["id"])
    return user_public(db.q1("SELECT * FROM users WHERE id=?", u["id"]))


@app.get("/api/leaderboard")
def leaderboard(tc: str = "blitz"):
    if tc not in TC:
        raise HTTPException(400, "bad time control")
    rows = db.q("""SELECT u.username, r.rating, r.games, r.wins, r.losses, r.draws FROM ratings r
                   JOIN users u ON u.id=r.user_id WHERE r.tc=? AND r.games>0
                   ORDER BY r.rating DESC LIMIT 100""", tc)
    return [{"username": r["username"], "rating": round(r["rating"]), "games": r["games"],
             "wins": r["wins"], "losses": r["losses"], "draws": r["draws"]} for r in rows]


def match_summary(m, uid):
    me_p1 = m["p1_id"] == uid
    mine, theirs = ("p1", "p2") if me_p1 else ("p2", "p1")
    opp = m["p2_name"] if me_p1 else db.q1("SELECT username FROM users WHERE id=?", m["p1_id"])["username"]
    res = m["result"]
    outcome = "draw" if res == "draw" else ("win" if res == mine else "loss")
    return {"id": m["id"], "tc": m["tc"], "rated": bool(m["rated"]), "bot": bool(m["bot"]), "level": m["level"],
            "opponent": opp, "outcome": outcome,
            "my_score": m[f"{mine}_score"], "opp_score": m[f"{theirs}_score"],
            "rating_before": round(m[f"{mine}_before"]), "rating_after": round(m[f"{mine}_after"]),
            "opp_rating": round(m[f"{theirs}_before"]), "ended_at": m["ended_at"]}


@app.get("/api/users/{name}")
def profile(name: str):
    u = db.q1("SELECT * FROM users WHERE username=?", name)
    if not u:
        raise HTTPException(404, "No such player")
    hist = {tc: [] for tc in TC}
    for r in db.q("SELECT tc, rating, ts FROM rating_history WHERE user_id=? ORDER BY ts", u["id"]):
        hist[r["tc"]].append([r["ts"], round(r["rating"])])
    ms = db.q("""SELECT * FROM matches WHERE p1_id=? OR p2_id=? ORDER BY ended_at DESC LIMIT 50""", u["id"], u["id"])
    pub = user_public(u)
    pub.pop("new_per_day", None)
    pub.pop("lang", None)
    pub["joined"] = u["created_at"]
    pub["history"] = hist
    pub["matches"] = [match_summary(m, u["id"]) for m in ms]
    pub["studied"] = db.q1("SELECT COUNT(*) n FROM srs WHERE user_id=? AND reps>0", u["id"])["n"]
    return pub


@app.get("/api/matches/{mid}")
def match_detail(mid: str, req: Request):
    m = db.q1("SELECT * FROM matches WHERE id=?", mid)
    if not m:
        raise HTTPException(404, "No such match")
    viewer = current_user(req)
    lang = viewer["lang"] if viewer else "en"
    data = json.loads(m["data"])
    p1name = db.q1("SELECT username FROM users WHERE id=?", m["p1_id"])["username"]
    answered = max([len(a) for a in data["answers"]] + [0])
    rows = []
    for i, qd in enumerate(data["questions"][:answered]):
        a = [next((x for x in ans if x[0] == i), None) for ans in data["answers"]]

        def given_text(x):
            if x is None:
                return None
            if qd["t"] == "reading":
                return str(x[1])
            try:
                oc = CARDS[qd["o"][int(x[1])]]
            except Exception:
                return "?"
            return {"meaning": oc["meaning"][lang], "cloze": oc["word"], "translate": oc["translation"][lang]}[qd["t"]]

        rows.append({"i": i, "type": qd["t"], "card": card_reveal(qd["c"], lang),
                     "correct": correct_answer_text(qd, lang),
                     "p1": None if a[0] is None else {"given": given_text(a[0]), "ok": a[0][2], "ms": a[0][3]},
                     "p2": None if a[1] is None else {"given": given_text(a[1]), "ok": a[1][2], "ms": a[1][3]}})
    return {"id": m["id"], "tc": m["tc"], "rated": bool(m["rated"]), "bot": bool(m["bot"]), "level": m["level"],
            "result": m["result"], "ended_at": m["ended_at"],
            "p1": {"name": p1name, "score": m["p1_score"], "correct": m["p1_correct"], "wrong": m["p1_wrong"],
                   "before": round(m["p1_before"]), "after": round(m["p1_after"])},
            "p2": {"name": m["p2_name"], "score": m["p2_score"], "correct": m["p2_correct"], "wrong": m["p2_wrong"],
                   "before": round(m["p2_before"]), "after": round(m["p2_after"])},
            "questions": rows}


class ChallengeReq(BaseModel):
    tc: str
    rated: bool = True


@app.post("/api/challenge")
def create_challenge(c: ChallengeReq, req: Request):
    u = require_user(req)
    if c.tc not in TC:
        raise HTTPException(400, "bad time control")
    return {"code": manager.create_challenge(u["id"], c.tc, c.rated)}


@app.get("/api/challenge/{code}")
def get_challenge(code: str):
    ch = manager.challenges.get(code)
    if not ch:
        raise HTTPException(404, "This challenge has expired or doesn't exist")
    u = db.q1("SELECT username FROM users WHERE id=?", ch["uid"])
    r = db.q1("SELECT rating FROM ratings WHERE user_id=? AND tc=?", ch["uid"], ch["tc"])
    return {"from": u["username"], "rating": round(r["rating"]), "tc": ch["tc"], "rated": ch["rated"],
            "online": hub.online(ch["uid"])}


# ---------- study (SRS) ----------

@app.get("/api/study/next")
def study_next(req: Request):
    u = require_user(req)
    cid, kind, prev, counts = srs.next_card(u["id"])
    if cid is None:
        return {"card": None, "counts": counts}
    best, _ = srs.user_level(u["id"])
    return {"card": card_reveal(cid, u["lang"]), "kind": kind, "intervals": prev, "counts": counts,
            "tier": furi_tier(best)}


class Grade(BaseModel):
    card_id: int
    grade: int


@app.post("/api/study/answer")
def study_answer(g: Grade, req: Request):
    u = require_user(req)
    if g.card_id not in CARDS or g.grade not in (1, 2, 3, 4):
        raise HTTPException(400, "bad answer")
    srs.answer(u["id"], g.card_id, g.grade)
    return {"ok": True}


@app.get("/api/study/stats")
def study_stats(req: Request):
    u = require_user(req)
    c = srs.counts(u["id"])
    c["by_level"] = {}
    rows = db.q("SELECT card_id, state, interval FROM srs WHERE user_id=? AND reps>0", u["id"])
    for lv in LEVELS:
        ids = {x["id"] for x in BY_LEVEL[lv]}
        mine = [r for r in rows if r["card_id"] in ids]
        c["by_level"][lv] = {"total": len(ids), "seen": len(mine),
                             "mature": sum(1 for r in mine if r["state"] == "review" and r["interval"] >= 21)}
    days = db.q("SELECT day, reviews FROM study_daily WHERE user_id=? ORDER BY day DESC LIMIT 60", u["id"])
    c["days"] = [dict(d) for d in days]
    return c


# ---------- websocket ----------

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    u = db.user_from_token(ws.cookies.get(COOKIE))
    await ws.accept()
    if not u:
        await ws.send_text(json.dumps({"type": "error", "msg": "Please log in"}))
        await ws.close()
        return
    uid = u["id"]
    hub.add(uid, ws)
    m = manager.active(uid)
    await ws.send_text(json.dumps({"type": "hello", "in_match": m.id if m else None,
                                   "queued": manager.in_queue(uid)}))
    try:
        while True:
            msg = json.loads(await ws.receive_text())
            t = msg.get("type")
            if t == "queue" and msg.get("tc") in TC:
                await manager.enqueue(uid, msg["tc"])
            elif t == "cancel_queue":
                manager.dequeue(uid)
                await hub.send(uid, {"type": "unqueued"})
            elif t == "play_bot" and msg.get("tc") in TC:
                manager.dequeue(uid)
                await manager.play_bot(uid, msg["tc"])
            elif t == "answer":
                m = manager.active(uid)
                if m and m.id == msg.get("match_id"):
                    p = m.player(uid)
                    await m.submit(p, msg.get("q"), msg.get("answer"))
            elif t == "resume":
                m = manager.active(uid)
                if m:
                    p = m.player(uid)
                    await ws.send_text(json.dumps(m.intro_msg(p), ensure_ascii=False))
                    if time.time() >= m.starts_at:
                        await ws.send_text(json.dumps(m.question_msg(p), ensure_ascii=False))
                    await m.broadcast_scores()
            elif t == "accept_challenge":
                err = await manager.accept_challenge(uid, msg.get("code", ""))
                if err:
                    await hub.send(uid, {"type": "error", "msg": err})
            elif t == "ping":
                await ws.send_text(json.dumps({"type": "pong", "stats": manager.stats()}))
    except (WebSocketDisconnect, RuntimeError, json.JSONDecodeError):
        pass
    finally:
        hub.remove(uid, ws)
        if not hub.online(uid):
            manager.dequeue(uid)


# ---------- static SPA ----------
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")
