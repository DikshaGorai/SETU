"""
SETU web application - SIH 2026, problem statement SIH26043, team 6ixTitans.

Server-rendered pages (Jinja2) for the demo + a JSON API under /api for the
mobile client or any integration. Sessions are in-memory: fine for a local
deployment, swap for Redis when this moves to a state cloud.
"""

import os
import uuid
import secrets

from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import db, engine
from .locations import DISTRICTS, STATES, grouped, state_of

BASE = os.path.dirname(__file__)
app = FastAPI(title="SETU", description="Crowdsourced societal challenges, "
                                        "matched to university and industry capability")
app.mount("/static", StaticFiles(directory=os.path.join(BASE, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE, "templates"))

SESSIONS = {}


@app.on_event("startup")
def startup():
    db.init()


def conn():
    c = db.connect()
    try:
        yield c
    finally:
        c.close()


def current_user(request: Request):
    return SESSIONS.get(request.cookies.get("setu_session"))


def ctx(request, **kw):
    base = {
        "request": request,
        "user": current_user(request),
        "stages": engine.STAGES,
        "domains": engine.DOMAINS,
        "languages": engine.LANGUAGES,
        "districts": DISTRICTS,
        "location_groups": grouped(),
        "states": STATES,
    }
    base.update(kw)
    return base


def require(request, *roles):
    u = current_user(request)
    if not u or (roles and u["role"] not in roles):
        return None
    return u


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def home(request: Request, c=Depends(conn)):
    s = db.stats(c)
    top = db.list_challenges(c)[:3]
    return templates.TemplateResponse(request, "home.html", ctx(request, stats=s, top=top))


@app.get("/submit", response_class=HTMLResponse)
def submit_form(request: Request):
    return templates.TemplateResponse(request, "submit.html", ctx(request))


@app.post("/submit", response_class=HTMLResponse)
def submit(request: Request, text: str = Form(...), lang: str = Form("en"),
           district: str = Form("Kolkata"), c=Depends(conn)):
    u = current_user(request)
    who = u["name"] if u else "Anonymous citizen"
    result, code = db.create_challenge(c, text, lang, district, who)
    return templates.TemplateResponse(request, "result.html", ctx(request, result=result, code=code,
                           challenge=db.challenge_by_code(c, code) if result["accepted"] else None))


@app.get("/challenges", response_class=HTMLResponse)
def marketplace(request: Request, domain: str = "all", district: str = "all",
                stage: str = "all", q: str = "", state: str = "all", c=Depends(conn)):
    items = db.list_challenges(c, domain, district, stage, q, state=state)
    return templates.TemplateResponse(
        request, "marketplace.html",
        ctx(request, items=items, f={"domain": domain, "district": district,
                                     "stage": stage, "q": q, "state": state}))


@app.get("/challenge/{code}", response_class=HTMLResponse)
def detail(request: Request, code: str, c=Depends(conn)):
    ch = db.challenge_by_code(c, code)
    if not ch:
        raise HTTPException(404, "No challenge with that ID")
    return templates.TemplateResponse(request, "challenge.html", ctx(request, c=ch))


@app.get("/csr", response_class=HTMLResponse)
def csr_portal(request: Request, c=Depends(conn)):
    items = db.list_challenges(c, csr_only=True)
    partners = [dict(r) for r in c.execute("SELECT * FROM partners")]
    committed = {}
    for f in c.execute("SELECT partner, SUM(amount) s FROM funding GROUP BY partner"):
        committed[f["partner"]] = round(f["s"], 2)
    return templates.TemplateResponse(request, "csr.html", ctx(request, items=items, partners=partners, committed=committed))


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, c=Depends(conn)):
    return templates.TemplateResponse(request, "dashboard.html", ctx(request, stats=db.stats(c),
                              institutions=[dict(r) for r in c.execute(
                                  "SELECT * FROM institutions")]))


@app.get("/track", response_class=HTMLResponse)
def track(request: Request, code: str = "", c=Depends(conn)):
    ch = db.challenge_by_code(c, code.strip().upper()) if code else None
    return templates.TemplateResponse(request, "track.html", ctx(request, c=ch, code=code, missing=bool(code and not ch)))


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

@app.post("/challenge/{code}/join")
def join(request: Request, code: str, inst: int = Form(...), c=Depends(conn)):
    u = require(request, "university", "admin")
    if not u:
        return RedirectResponse("/login?next=/challenge/" + code, 303)
    ch = db.challenge_by_code(c, code)
    c.execute("UPDATE matches SET joined=1 WHERE challenge_id=? AND inst_id=?", (ch["id"], inst))
    c.execute("UPDATE challenges SET stage=MAX(stage,4) WHERE id=?", (ch["id"],))
    name = c.execute("SELECT name FROM institutions WHERE id=?", (inst,)).fetchone()["name"]
    c.execute("INSERT INTO audit(challenge_id,stage,decision,confidence,actor,created_at) "
              "VALUES(?,?,?,?,?,?)",
              (ch["id"], "Consortium", name + " accepted the challenge", 1.0, u["name"], db.now()))
    c.commit()
    return RedirectResponse("/challenge/" + code, 303)


@app.post("/challenge/{code}/advance")
def advance(request: Request, code: str, note: str = Form(""), c=Depends(conn)):
    u = require(request, "university", "admin")
    if not u:
        return RedirectResponse("/login?next=/challenge/" + code, 303)
    ch = db.challenge_by_code(c, code)
    new = min(len(engine.STAGES), ch["stage"] + 1)
    c.execute("UPDATE challenges SET stage=? WHERE id=?", (new, ch["id"]))
    c.execute("INSERT INTO updates(challenge_id,author,body,created_at) VALUES(?,?,?,?)",
              (ch["id"], u["name"], note or ("Moved to " + engine.STAGES[new - 1]), db.now()))
    c.execute("INSERT INTO audit(challenge_id,stage,decision,confidence,actor,created_at) "
              "VALUES(?,?,?,?,?,?)",
              (ch["id"], "Lifecycle", "Stage set to " + engine.STAGES[new - 1], 1.0,
               u["name"], db.now()))
    c.commit()
    return RedirectResponse("/challenge/" + code, 303)


@app.post("/challenge/{code}/fund")
def fund(request: Request, code: str, amount: float = Form(0.5), c=Depends(conn)):
    u = require(request, "csr", "admin")
    if not u:
        return RedirectResponse("/login?next=/challenge/" + code, 303)
    ch = db.challenge_by_code(c, code)
    c.execute("INSERT INTO funding(challenge_id,partner,amount,clause,created_at) "
              "VALUES(?,?,?,?,?)", (ch["id"], u["org"], amount, ch["csr_clause"], db.now()))
    c.execute("UPDATE challenges SET funded=funded+?, stage=MAX(stage,4) WHERE id=?",
              (amount, ch["id"]))
    c.execute("INSERT INTO audit(challenge_id,stage,decision,confidence,actor,created_at) "
              "VALUES(?,?,?,?,?,?)",
              (ch["id"], "CSR", "%s committed Rs %.2f Cr under %s" % (u["org"], amount,
                                                                      ch["csr_clause"]),
               1.0, u["name"], db.now()))
    c.commit()
    return RedirectResponse("/challenge/" + code, 303)


@app.post("/challenge/{code}/override")
def override(request: Request, code: str, domain: str = Form(...),
             reason: str = Form(""), c=Depends(conn)):
    """Human-in-the-loop: a reviewer can correct the AI and the correction is logged."""
    u = require(request, "admin")
    if not u:
        return RedirectResponse("/login?next=/challenge/" + code, 303)
    ch = db.challenge_by_code(c, code)
    label = engine.DOMAINS[domain]["label"]
    c.execute("UPDATE challenges SET domain=?, domain_label=?, csr_clause=? WHERE id=?",
              (domain, label, engine.DOMAINS[domain]["clause"], ch["id"]))
    c.execute("INSERT INTO audit(challenge_id,stage,decision,confidence,actor,override,created_at)"
              " VALUES(?,?,?,?,?,?,?)",
              (ch["id"], "Human override", "Domain corrected to %s. %s" % (label, reason),
               1.0, u["name"], 1, db.now()))
    c.commit()
    return RedirectResponse("/challenge/" + code, 303)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request, next: str = "/"):
    return templates.TemplateResponse(request, "login.html", ctx(request, next=next, error=None))


@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...),
          next: str = Form("/"), c=Depends(conn)):
    row = c.execute("SELECT * FROM users WHERE email=? AND pwd=?",
                    (email.strip().lower(), db.hash_pwd(password))).fetchone()
    if not row:
        return templates.TemplateResponse(request, "login.html", ctx(request, next=next,
                              error="That email and password combination is not on the system."),
            status_code=401)
    token = secrets.token_hex(16)
    SESSIONS[token] = dict(row)
    resp = RedirectResponse(next or "/", 303)
    resp.set_cookie("setu_session", token, httponly=True, samesite="lax")
    return resp


@app.get("/logout")
def logout(request: Request):
    SESSIONS.pop(request.cookies.get("setu_session"), None)
    resp = RedirectResponse("/", 303)
    resp.delete_cookie("setu_session")
    return resp


# ---------------------------------------------------------------------------
# JSON API  (what the mobile app / PWA would call)
# ---------------------------------------------------------------------------

@app.get("/api/challenges")
def api_challenges(domain: str = "all", district: str = "all", state: str = "all",
                   c=Depends(conn)):
    return {"challenges": db.list_challenges(c, domain, district, state=state)}


@app.get("/api/challenge/{code}")
def api_challenge(code: str, c=Depends(conn)):
    ch = db.challenge_by_code(c, code)
    if not ch:
        raise HTTPException(404, "Unknown challenge code")
    return ch


@app.post("/api/submit")
async def api_submit(request: Request, c=Depends(conn)):
    body = await request.json()
    result, code = db.create_challenge(
        c, body.get("text", ""), body.get("lang", "en"),
        body.get("district", "Kolkata"), body.get("by", "API client"))
    return {"accepted": result["accepted"], "code": code,
            "reason": result.get("reason"), "steps": result["steps"]}


@app.get("/api/stats")
def api_stats(c=Depends(conn)):
    return db.stats(c)


@app.get("/healthz")
def healthz():
    return {"ok": True}
