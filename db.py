"""SQLite data layer. One file on disk (setu.db), no server to install."""

import os
import sqlite3
import hashlib
import datetime

DB_PATH = os.environ.get("SETU_DB", os.path.join(os.path.dirname(__file__), "..", "setu.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY, email TEXT UNIQUE, name TEXT, role TEXT, org TEXT, pwd TEXT);

CREATE TABLE IF NOT EXISTS institutions(
  id INTEGER PRIMARY KEY, name TEXT, caps TEXT, district TEXT, state TEXT,
  load INTEGER, contact TEXT, mentor TEXT);

CREATE TABLE IF NOT EXISTS partners(
  id INTEGER PRIMARY KEY, name TEXT, focus TEXT, pool REAL);

CREATE TABLE IF NOT EXISTS challenges(
  id INTEGER PRIMARY KEY, code TEXT UNIQUE, title TEXT, text TEXT, raw TEXT,
  lang TEXT, district TEXT, state TEXT, domain TEXT, domain_label TEXT, priority INTEGER,
  stage INTEGER DEFAULT 1, supporters INTEGER DEFAULT 1, csr_clause TEXT,
  csr_eligible INTEGER, funded REAL DEFAULT 0, submitted_by TEXT,
  created_at TEXT, status TEXT DEFAULT 'open');

CREATE TABLE IF NOT EXISTS matches(
  id INTEGER PRIMARY KEY, challenge_id INTEGER, inst_id INTEGER, name TEXT,
  fit INTEGER, why TEXT, mentor TEXT, joined INTEGER DEFAULT 0);

CREATE TABLE IF NOT EXISTS audit(
  id INTEGER PRIMARY KEY, challenge_id INTEGER, stage TEXT, decision TEXT,
  confidence REAL, actor TEXT, override INTEGER DEFAULT 0, created_at TEXT);

CREATE TABLE IF NOT EXISTS funding(
  id INTEGER PRIMARY KEY, challenge_id INTEGER, partner TEXT, amount REAL,
  clause TEXT, created_at TEXT);

CREATE TABLE IF NOT EXISTS updates(
  id INTEGER PRIMARY KEY, challenge_id INTEGER, author TEXT, body TEXT, created_at TEXT);
"""


def connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def hash_pwd(p):
    return hashlib.sha256(("setu-salt:" + p).encode()).hexdigest()


def now():
    return datetime.datetime.now().isoformat(timespec="seconds")


INSTITUTIONS = [
    # West Bengal
    ("Jadavpur University, Kolkata", "water,environment,energy,manufacturing",
     "Kolkata", "West Bengal", 3, "innovation@jadavpuruniversity.in", "Dr. Sudeshna Banerjee"),
    ("IIT Kharagpur", "ai,agriculture,water,energy,mobility",
     "Paschim Medinipur", "West Bengal", 2, "outreach@iitkgp.ac.in", "Prof. Arnab Chatterjee"),
    ("IIEST Shibpur", "civil,materials,manufacturing,mobility,environment",
     "Howrah", "West Bengal", 1, "rnd@iiests.ac.in", "Dr. Pritam Ghosh"),
    ("University of Calcutta", "health,biotech,water,education",
     "Kolkata", "West Bengal", 4, "csr@caluniv.ac.in", "Dr. Moumita Sen"),
    ("Visva-Bharati, Santiniketan", "agriculture,livelihood,education",
     "Birbhum", "West Bengal", 2, "outreach@visvabharati.ac.in", "Dr. Anirban Dutta"),
    ("NIT Durgapur", "materials,energy,manufacturing,environment",
     "Paschim Bardhaman", "West Bengal", 2, "incubation@nitdgp.ac.in", "Dr. Rituparna Das"),
    ("University of Kalyani", "water,agriculture,health,environment",
     "Nadia", "West Bengal", 3, "research@klyuniv.ac.in", "Dr. Subhas Mondal"),
    ("University of Gour Banga, Malda", "agriculture,livelihood,health,education",
     "Malda", "West Bengal", 2, "research@ugb.ac.in", "Dr. Anwesha Roy"),
    ("IIM Calcutta", "policy,livelihood,education,operations",
     "Kolkata", "West Bengal", 1, "impactlab@iimcal.ac.in", "Prof. Ratna Mukherjee"),

    # Jharkhand
    ("IIT (ISM) Dhanbad", "materials,energy,environment,mobility",
     "Dhanbad", "Jharkhand", 2, "outreach@iitism.ac.in", "Dr. Sanjay Mahto"),
    ("BIT Mesra, Ranchi", "ai,manufacturing,sensors,energy",
     "Ranchi", "Jharkhand", 3, "incubation@bitmesra.ac.in", "Dr. Priya Tirkey"),
    ("NIT Jamshedpur", "materials,manufacturing,civil,mobility",
     "East Singhbhum", "Jharkhand", 2, "rnd@nitjsr.ac.in", "Dr. Alok Sinha"),
    ("Birsa Agricultural University, Ranchi", "agriculture,livelihood,water",
     "Ranchi", "Jharkhand", 2, "extension@bau.ac.in", "Dr. Nirmala Oraon"),
    ("Central University of Jharkhand", "environment,education,policy,health",
     "Ranchi", "Jharkhand", 1, "research@cuj.ac.in", "Dr. Vikas Munda"),
    ("XISS Ranchi", "livelihood,policy,operations,education",
     "Ranchi", "Jharkhand", 3, "outreach@xiss.ac.in", "Prof. Shalini Ekka"),

    # Other states - national capability pool
    ("IIT Bombay", "ai,energy,water,mobility,sensors",
     "Mumbai", "Maharashtra", 3, "outreach@iitb.ac.in", "Prof. Kavita Deshmukh"),
    ("IIT Madras", "water,manufacturing,ai,mobility",
     "Chennai", "Tamil Nadu", 2, "icsr@iitm.ac.in", "Dr. R. Sundaram"),
    ("IISc Bengaluru", "ai,materials,health,water,environment,sensors,energy",
     "Bengaluru", "Karnataka", 4, "outreach@iisc.ac.in", "Prof. N. Raghavan"),
    ("IIT Delhi", "ai,environment,health,energy",
     "New Delhi", "Delhi", 3, "irdunit@iitd.ac.in", "Dr. Anjali Mehra"),
    ("IIT Guwahati", "water,agriculture,environment,civil",
     "Guwahati", "Assam", 1, "outreach@iitg.ac.in", "Dr. Pranab Saikia"),
    ("NIT Rourkela", "materials,manufacturing,environment,energy",
     "Rourkela", "Odisha", 2, "rnd@nitrkl.ac.in", "Dr. Sasmita Patra"),
    ("IIT Hyderabad", "ai,sensors,mobility,manufacturing",
     "Hyderabad", "Telangana", 2, "outreach@iith.ac.in", "Dr. Srinivas Rao"),
    ("IIM Ahmedabad", "policy,operations,livelihood,education",
     "Ahmedabad", "Gujarat", 1, "ciie@iima.ac.in", "Prof. Hetal Shah"),
    ("IIT Kanpur", "agriculture,ai,energy,materials",
     "Kanpur", "Uttar Pradesh", 3, "outreach@iitk.ac.in", "Dr. Alok Verma"),
    ("Andhra University, Visakhapatnam", "water,environment,marine,civil",
     "Visakhapatnam", "Andhra Pradesh", 3, "innovation@andhrauniversity.edu.in", "Dr. S. Rajeswari"),
]

PARTNERS = [
    ("Hooghly Steel Foundation", "environment,water,mobility", 4.2),
    ("Bengal Pharma CSR Trust", "health,water", 3.0),
    ("Salt Lake Infotech Foundation", "education,livelihood", 2.5),
    ("Bhagirathi Bank Social Fund", "agriculture,livelihood,energy", 1.8),
    ("Chhotanagpur Mining CSR Board", "environment,water,livelihood", 5.0),
    ("Damodar Power Foundation", "energy,environment,education", 2.2),
    ("Subarnarekha Rural Trust", "agriculture,health,livelihood", 1.5),
]

USERS = [
    ("citizen@setu.in", "Ratna Mondal", "citizen", "Chakdaha Gram Panchayat, Nadia"),
    ("sahayak@setu.in", "Bikash Sarkar (Sahayak)", "citizen", "Common Service Centre, Chakdaha"),
    ("uni@setu.in", "Dr. Sudeshna Banerjee", "university", "Jadavpur University"),
    ("uni2@setu.in", "Dr. Priya Tirkey", "university", "BIT Mesra, Ranchi"),
    ("csr@setu.in", "Meera Nair", "csr", "Hooghly Steel Foundation"),
    ("csr2@setu.in", "Arun Kujur", "csr", "Chhotanagpur Mining CSR Board"),
    ("admin@setu.in", "State Innovation Officer", "admin", "Govt. of West Bengal"),
]

SEED_CHALLENGES = [
    # West Bengal
    ("Handpump water in 18 villages of Chakdaha block has arsenic above the safe limit and about "
     "900 families drink it because the piped supply reaches only the main road. People get skin "
     "lesions every year and the community needs a low cost way to test and treat the water locally.",
     "bn", "Nadia", 5, "Ratna Mondal"),
    ("Embankments in our Sundarban village break during every cyclone and salt water enters the "
     "ponds and the paddy fields. Around 1400 families lose their drinking water and their crop "
     "in the same week and take months to recover.",
     "bn", "South 24 Parganas", 3, "Bikash Sarkar (Sahayak)"),
    ("Brick kilns around the ward burn through the dry season and residents of the colony breathe "
     "the smoke every night. The ward wants a cleaner kiln model and a monitoring method it can "
     "run on its own.",
     "hi", "Howrah", 2, "Bikash Sarkar (Sahayak)"),
    ("Students in 11 villages drop out after class 8 because there is no science lab and the route "
     "to the block school floods in the rains. About 400 students are affected every year.",
     "en", "Purulia", 4, "Ratna Mondal"),
    ("Potato farmers here lose nearly a quarter of the harvest because cold storage is full and far "
     "away. 2500 farmers want a low cost village level storage method that works without steady power.",
     "bn", "Purba Bardhaman", 6, "Bikash Sarkar (Sahayak)"),
    ("Handloom weavers in our block cannot sell directly and the income of 800 women has fallen "
     "every year. They want a shared design and market linkage model run through the SHG.",
     "bn", "Nadia", 2, "Ratna Mondal"),

    # Jharkhand
    ("Handpump water in 22 villages of our block has high iron and fluoride and 1100 tribal "
     "families have no alternative source in summer. The panchayat wants a treatment unit the "
     "village itself can maintain.",
     "sat", "Palamu", 3, "Bikash Sarkar (Sahayak)"),
    ("Coal dust from the haulage road settles on houses, ponds and crops, and 2000 residents "
     "living along it have no way to measure how bad the air actually is or to prove it.",
     "hi", "Dhanbad", 2, "Bikash Sarkar (Sahayak)"),
    ("Lac and tasar cultivators in 15 villages lose more than a third of the produce to poor "
     "storage and to traders who fix the rate. 1800 families want grading, storage and a direct "
     "market channel.",
     "hi", "Khunti", 4, "Ratna Mondal"),
    ("Every monsoon 6 villages here are cut off because the stream crosses the only road, and "
     "700 people including school children cannot reach the block headquarters for weeks.",
     "hi", "Gumla", 1, "Ratna Mondal"),

    # Other states
    ("Ward level flooding traps 3000 households for two days after every heavy spell because the "
     "storm drains are silted and nobody knows which drain is blocked until it overflows.",
     "en", "Mumbai", 3, "Ratna Mondal"),
    ("Groundwater in 9 peri urban wards has dropped so far that 1200 families now depend on paid "
     "tankers, and the borewells that still work are drying out one by one.",
     "en", "Bengaluru", 2, "Ratna Mondal"),
]


def init(force=False):
    """Create the schema and seed reference data + demo challenges."""
    from . import engine

    fresh = force or not os.path.exists(DB_PATH)
    if force and os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = connect()
    conn.executescript(SCHEMA)

    if conn.execute("SELECT COUNT(*) c FROM institutions").fetchone()["c"] == 0:
        conn.executemany(
            "INSERT INTO institutions(name,caps,district,state,load,contact,mentor) "
            "VALUES(?,?,?,?,?,?,?)", INSTITUTIONS)
        conn.executemany("INSERT INTO partners(name,focus,pool) VALUES(?,?,?)", PARTNERS)
        conn.executemany(
            "INSERT INTO users(email,name,role,org,pwd) VALUES(?,?,?,?,?)",
            [(e, n, r, o, hash_pwd("setu123")) for e, n, r, o in USERS])
        conn.commit()

    if conn.execute("SELECT COUNT(*) c FROM challenges").fetchone()["c"] == 0:
        for text, lang, district, stage, who in SEED_CHALLENGES:
            create_challenge(conn, text, lang, district, who, stage=stage)
        conn.commit()
    conn.close()
    return fresh


def next_code(conn):
    """Highest code so far + 1, so merged duplicates never cause a collision."""
    row = conn.execute("SELECT MAX(CAST(SUBSTR(code, 9) AS INTEGER)) m FROM challenges").fetchone()
    return "SETU-26-%04d" % ((row["m"] or 0) + 1)


def title_from(text):
    first = text.strip().split(".")[0]
    return (first[:88] + "...") if len(first) > 88 else first


def create_challenge(conn, raw_text, lang, district, who, stage=1):
    """Runs the engine and persists everything it decided. Returns (result, code)."""
    from . import engine
    from .locations import state_of

    existing = [(r["code"], r["text"]) for r in
                conn.execute("SELECT code,text FROM challenges").fetchall()]
    insts = [dict(r) for r in conn.execute("SELECT * FROM institutions").fetchall()]
    partners = [dict(r) for r in conn.execute("SELECT * FROM partners").fetchall()]

    result = engine.run_pipeline(raw_text, lang, district, existing, insts, partners,
                                 state=state_of(district))

    if not result["accepted"]:
        if result["reason"] == "duplicate":
            conn.execute("UPDATE challenges SET supporters=supporters+1 WHERE code=?",
                         (result["duplicate"],))
            conn.commit()
        return result, result.get("duplicate")

    code = next_code(conn)
    cur = conn.execute(
        "INSERT INTO challenges(code,title,text,raw,lang,district,state,domain,domain_label,"
        "priority,stage,supporters,csr_clause,csr_eligible,submitted_by,created_at) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (code, title_from(result["text"]), result["text"], raw_text,
         engine.LANGUAGES.get(lang, lang), district, state_of(district), result["domain"],
         result["domain_label"], result["priority"], stage, 1,
         result["csr_clause"], int(result["csr_eligible"]), who, now()))
    cid = cur.lastrowid

    for m in result["matches"]:
        inst = conn.execute("SELECT mentor FROM institutions WHERE id=?",
                            (m["inst_id"],)).fetchone()
        conn.execute(
            "INSERT INTO matches(challenge_id,inst_id,name,fit,why,mentor,joined) "
            "VALUES(?,?,?,?,?,?,?)",
            (cid, m["inst_id"], m["name"], m["fit"], m["why"],
             inst["mentor"] if inst else "", 1 if stage >= 4 else 0))

    for s in result["steps"]:
        conn.execute(
            "INSERT INTO audit(challenge_id,stage,decision,confidence,actor,created_at) "
            "VALUES(?,?,?,?,?,?)", (cid, s["name"], s["detail"], s["conf"], "AI engine", now()))

    if stage >= 4 and result["csr_partners"]:
        amount = 0.8
        conn.execute("UPDATE challenges SET funded=? WHERE id=?", (amount, cid))
        conn.execute("INSERT INTO funding(challenge_id,partner,amount,clause,created_at) "
                     "VALUES(?,?,?,?,?)",
                     (cid, result["csr_partners"][0], amount, result["csr_clause"], now()))
    conn.commit()
    return result, code


# --------------------------------------------------------------------------
# Queries used by the routes
# --------------------------------------------------------------------------

def challenge_by_code(conn, code):
    row = conn.execute("SELECT * FROM challenges WHERE code=?", (code,)).fetchone()
    if not row:
        return None
    c = dict(row)
    c["matches"] = [dict(r) for r in conn.execute(
        "SELECT * FROM matches WHERE challenge_id=? ORDER BY id", (c["id"],))]
    c["audit"] = [dict(r) for r in conn.execute(
        "SELECT * FROM audit WHERE challenge_id=? ORDER BY id", (c["id"],))]
    c["funding"] = [dict(r) for r in conn.execute(
        "SELECT * FROM funding WHERE challenge_id=? ORDER BY id", (c["id"],))]
    c["updates"] = [dict(r) for r in conn.execute(
        "SELECT * FROM updates WHERE challenge_id=? ORDER BY id DESC", (c["id"],))]
    return c


def list_challenges(conn, domain=None, district=None, stage=None, q=None,
                    csr_only=False, state=None):
    sql = "SELECT * FROM challenges WHERE 1=1"
    args = []
    if state and state != "all":
        sql += " AND state=?"; args.append(state)
    if domain and domain != "all":
        sql += " AND domain=?"; args.append(domain)
    if district and district != "all":
        sql += " AND district=?"; args.append(district)
    if stage and stage != "all":
        sql += " AND stage=?"; args.append(int(stage))
    if csr_only:
        sql += " AND csr_eligible=1"
    if q:
        sql += " AND (text LIKE ? OR code LIKE ? OR domain_label LIKE ?)"
        args += ["%%%s%%" % q] * 3
    sql += " ORDER BY priority DESC, id DESC"
    out = []
    for r in conn.execute(sql, args):
        c = dict(r)
        lead = conn.execute(
            "SELECT * FROM matches WHERE challenge_id=? ORDER BY id LIMIT 1",
            (c["id"],)).fetchone()
        c["lead"] = dict(lead) if lead else None
        c["joined"] = [dict(m)["name"] for m in conn.execute(
            "SELECT name FROM matches WHERE challenge_id=? AND joined=1", (c["id"],))]
        out.append(c)
    return out


def stats(conn):
    from . import engine
    chs = [dict(r) for r in conn.execute("SELECT * FROM challenges")]
    total = len(chs) or 1

    def group(field):
        d = {}
        for c in chs:
            d[c[field]] = d.get(c[field], 0) + 1
        return sorted(d.items(), key=lambda kv: -kv[1])

    funnel = []
    for i, s in enumerate(engine.STAGES):
        n = sum(1 for c in chs if c["stage"] >= i + 1)
        funnel.append({"stage": s, "count": n, "pct": int(100 * n / total)})

    funded = conn.execute("SELECT COALESCE(SUM(amount),0) s FROM funding").fetchone()["s"]
    matched = sum(1 for c in chs if c["stage"] >= 3)
    return {
        "total": len(chs),
        "matched": matched,
        "match_rate": int(100 * matched / total),
        "deployed": sum(1 for c in chs if c["stage"] >= 7),
        "funded": round(funded, 2),
        "avg_priority": int(sum(c["priority"] for c in chs) / total),
        "by_domain": group("domain_label"),
        "by_district": group("district"),
        "by_state": group("state"),
        "by_lang": group("lang"),
        "funnel": funnel,
        "recent_audit": [dict(r) for r in conn.execute(
            "SELECT a.*, c.code FROM audit a JOIN challenges c ON c.id=a.challenge_id "
            "ORDER BY a.id DESC LIMIT 12")],
    }
