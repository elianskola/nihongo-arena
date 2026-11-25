"""End-to-end test against a running server: python tests/e2e_test.py [base_url]"""
import asyncio
import json
import random
import sys

import httpx
import websockets

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8765"
WS = BASE.replace("http", "ws") + "/ws"


def account(name):
    c = httpx.Client(base_url=BASE)
    r = c.post("/api/register", json={"username": name, "password": "secret123"})
    if r.status_code != 200:
        r = c.post("/api/login", json={"username": name, "password": "secret123"})
    r.raise_for_status()
    return c


async def player(client, name, start_msg, strategy, log):
    cookie = f"arena_session={client.cookies['arena_session']}"
    async with websockets.connect(WS, additional_headers={"Cookie": cookie}) as ws:
        hello = json.loads(await ws.recv())
        assert hello["type"] == "hello", hello
        if start_msg:
            await ws.send(json.dumps(start_msg))
        types = set()
        while True:
            m = json.loads(await ws.recv())
            if m["type"] == "question":
                d = m["data"]
                types.add(d["type"])
                await asyncio.sleep(random.uniform(0.2, 0.6))
                ans = strategy(d)
                await ws.send(json.dumps({"type": "answer", "match_id": m["match_id"], "q": m["q"], "answer": ans}))
            elif m["type"] == "match_end":
                log[name] = {"end": m, "types": types}
                return m
            elif m["type"] == "error":
                raise RuntimeError(f"{name}: {m['msg']}")


async def main():
    alice, bob, carol, dave, erin = (account(n) for n in ["alice", "bob", "carol", "dave", "erin"])
    log = {}
    code = dave.post("/api/challenge", json={"tc": "blitz", "rated": False}).json()["code"]
    info = erin.get(f"/api/challenge/{code}").json()
    print("challenge info:", info)

    async def erin_accept():
        await asyncio.sleep(1.0)
        return await player(erin, "erin", {"type": "accept_challenge", "code": code}, lambda d: "abc" if d["type"] == "reading" else 1, log)

    await asyncio.gather(
        player(alice, "alice", {"type": "queue", "tc": "blitz"}, lambda d: "x" if d["type"] == "reading" else 0, log),
        player(bob, "bob", {"type": "queue", "tc": "blitz"}, lambda d: "y" if d["type"] == "reading" else random.randrange(4), log),
        player(carol, "carol", {"type": "play_bot", "tc": "blitz"}, lambda d: "z" if d["type"] == "reading" else 2, log),
        player(dave, "dave", None, lambda d: "q" if d["type"] == "reading" else 3, log),
        erin_accept(),
    )
    for n, v in log.items():
        e = v["end"]
        print(f"{n:6} {e['outcome']:5} rated={e['rated']} score {e['you']['score']} vs {e['opponent']['name']} {e['opponent']['score']}"
              f"  rating {e['rating_before']}->{e['rating_after']}  missed+{e['missed_added']}  types={sorted(v['types'])}")
    a, b = log["alice"]["end"], log["bob"]["end"]
    assert a["rated"] and b["rated"]
    da, db_ = a["rating_after"] - a["rating_before"], b["rating_after"] - b["rating_before"]
    assert abs(da + db_) <= 1, (da, db_)
    assert not log["carol"]["end"]["rated"] and log["carol"]["end"]["rating_after"] == log["carol"]["end"]["rating_before"]
    assert not log["dave"]["end"]["rated"]
    me = alice.get("/api/me").json()
    print("alice blitz:", me["user"]["ratings"]["blitz"], "study:", me["study"])
    assert me["study"]["missed"] > 0
    prof = alice.get("/api/users/alice").json()
    mid = prof["matches"][0]["id"]
    rep = alice.get(f"/api/matches/{mid}").json()
    print("replay q1:", rep["questions"][0]["type"], rep["questions"][0]["card"]["word"], rep["questions"][0]["p1"], rep["questions"][0]["p2"])
    lb = alice.get("/api/leaderboard?tc=blitz").json()
    print("leaderboard:", lb)
    # SRS: missed battle cards first, then new
    seen = []
    for g in [1, 3, 3, 4, 2, 3]:
        n = alice.get("/api/study/next").json()
        seen.append((n["kind"], n["card"]["word"], {k: round(v) for k, v in n["intervals"].items()}))
        alice.post("/api/study/answer", json={"card_id": n["card"]["id"], "grade": g}).raise_for_status()
    for s in seen:
        print("study:", s)
    print("stats:", {k: v for k, v in alice.get("/api/study/stats").json().items() if k != "days"})
    print("ALL OK")


asyncio.run(main())
