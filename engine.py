"""
SETU intake engine.

Every function here is a stage in the AI Problem Management Module described in
the SIH26043 technical approach. Each stage returns a decision *and* a confidence
score, and every decision is written to the audit table so a district
administration can see why the platform did what it did.

Pure standard library - swap any stage for a real model later without touching
the routes (see README, "Replacing the stub models").
"""

import re
import math
import difflib
import datetime

# --------------------------------------------------------------------------
# Vocabulary and rules
# --------------------------------------------------------------------------

LANGUAGES = {
    "bn": "Bengali", "hi": "Hindi", "sat": "Santali", "kru": "Kurukh",
    "ho": "Ho", "or": "Odia", "ne": "Nepali", "ur": "Urdu", "as": "Assamese",
    "te": "Telugu", "ta": "Tamil", "mr": "Marathi", "kn": "Kannada", "en": "English",
}

STAGES = ["Submitted", "AI triaged", "Matched", "Consortium formed",
          "In development", "Field pilot", "Deployed & verified"]

DOMAINS = {
    "water": {
        "label": "Water & Sanitation",
        "vocab": ["water", "borewell", "pipe", "tap", "drinking", "fluoride", "supply",
                  "tank", "sewage", "drain", "toilet", "arsenic", "handpump", "saline", "embankment",
                  "জল", "পানি", "নলকূপ", "आर्सेनिक"],
        "clause": "Schedule VII (i) - safe drinking water and sanitation",
    },
    "health": {
        "label": "Public Health",
        "vocab": ["health", "hospital", "phc", "anaemia", "disease", "malaria", "dengue",
                  "medicine", "clinic", "maternal", "lesion", "স্বাস্থ্য", "রোগ"],
        "clause": "Schedule VII (i) - preventive health care",
    },
    "environment": {
        "label": "Environment",
        "vocab": ["pollution", "waste", "garbage", "plastic", "air", "smoke", "dumping",
                  "river", "effluent", "segregation", "kiln", "smoke", "দূষণ", "আবর্জনা"],
        "clause": "Schedule VII (iv) - environmental sustainability",
    },
    "agriculture": {
        "label": "Agriculture & Food",
        "vocab": ["crop", "farmer", "soil", "yield", "pest", "harvest", "mandi", "paddy",
                  "irrigation", "fish", "fisheries", "potato", "storage", "jute", "চাষি", "ফসল"],
        "clause": "Schedule VII (iv) - conservation of natural resources",
    },
    "education": {
        "label": "Education & Skills",
        "vocab": ["school", "student", "dropout", "learning", "teacher", "skill", "college",
                  "lab", "literacy", "শিক্ষা", "ছাত্র"],
        "clause": "Schedule VII (ii) - promoting education and vocational skills",
    },
    "livelihood": {
        "label": "Livelihood",
        "vocab": ["income", "shg", "weaver", "artisan", "market", "employment", "wage",
                  "women", "weaver", "handloom", "shg", "spoilage", "জীবিকা", "তাঁতি"],
        "clause": "Schedule VII (iii) - livelihood enhancement projects",
    },
    "energy": {
        "label": "Energy",
        "vocab": ["power", "solar", "electricity", "outage", "grid", "fuel", "biogas",
                  "pump", "बिजली", "విద్యుత్"],
        "clause": "Schedule VII (iv) - renewable energy",
    },
    "mobility": {
        "label": "Urban Mobility",
        "vocab": ["road", "bus", "traffic", "transport", "commute", "footpath", "accident",
                  "सड़क", "రోడ్డు"],
        "clause": "Schedule VII (x) - rural and urban development projects",
    },
}

GRIEVANCE_MARKERS = ["my pension", "my salary", "my application", "my certificate",
                     "my house", "my land", "not received", "refund", "transfer me",
                     "my complaint", "my ration card", "my name", "मेरा", "मुझे", "నా "]

COMMUNITY_MARKERS = ["village", "district", "community", "households", "families",
                     "students", "farmers", "residents", "ward", "block", "mandal",
                     "hamlet", "colony", "panchayat", "people"]

PII_PATTERNS = [
    (re.compile(r"\b[6-9]\d{9}\b"), "[phone redacted]"),
    (re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"), "[ID redacted]"),
    (re.compile(r"\b[\w.\-]+@[\w\-]+\.\w+\b"), "[email redacted]"),
]


# --------------------------------------------------------------------------
# Stages
# --------------------------------------------------------------------------

def redact_pii(text):
    hits = 0
    for pattern, mask in PII_PATTERNS:
        text, n = pattern.subn(mask, text)
        hits += n
    return text, hits


def normalise(text, lang):
    """Stands in for the Bhashini ASR / translate call. Offline-safe."""
    translated = lang != "en"
    return text.strip(), translated


def find_duplicate(text, existing):
    """existing = [(code, text), ...]. Blend of sequence ratio and token overlap."""
    best, score = None, 0.0
    tokens_a = set(re.findall(r"[a-z]{4,}", text.lower()))
    for code, other in existing:
        ratio = difflib.SequenceMatcher(None, text.lower(), other.lower()).ratio()
        tokens_b = set(re.findall(r"[a-z]{4,}", other.lower()))
        overlap = len(tokens_a & tokens_b) / max(1, len(tokens_a | tokens_b))
        combined = 0.45 * ratio + 0.55 * overlap
        if combined > score:
            best, score = code, combined
    return (best, round(score, 2)) if score >= 0.52 else (None, round(score, 2))


def scope_classify(text):
    """The gate that keeps SETU from becoming another complaint portal."""
    low = text.lower()
    g = sum(1 for m in GRIEVANCE_MARKERS if m in low)
    c = sum(1 for m in COMMUNITY_MARKERS if m in low)
    c += 2 * len(re.findall(
        r"\b\d+\s*(?:households|families|villages|students|farmers|people|women)\b", low))
    if g > c:
        return "grievance", round(min(0.96, 0.62 + 0.09 * (g - c)), 2)
    return "innovation", round(min(0.97, 0.66 + 0.07 * (c - g + 1)), 2)


def classify_domain(text):
    low = text.lower()
    words = set(re.findall(r"[\w\u0900-\u0D7F]+", low))
    scores = {}
    for key, meta in DOMAINS.items():
        hit = sum(2 if w in words else (1 if w in low else 0) for w in meta["vocab"])
        if hit:
            scores[key] = hit
    if not scores:
        return [("livelihood", 0.35)]
    total = sum(scores.values())
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])[:3]
    return [(k, round(v / total, 2)) for k, v in ranked]


def priority_score(text):
    """Severity x reach x equity. Deliberately transparent, not a black box."""
    low = text.lower()
    severity = 3
    for word, bump in [("death", 4), ("disease", 3), ("contaminat", 3), ("unsafe", 2),
                       ("dropout", 2), ("loss", 2), ("shortage", 2), ("sick", 2),
                       ("fail", 1), ("daily", 1)]:
        if word in low:
            severity += bump
    reach = 2
    nums = [int(n) for n in re.findall(r"\b(\d{2,7})\b", low)]
    if nums:
        reach = min(6, 1 + int(math.log10(max(nums)) * 2))
    equity = 3 if any(w in low for w in ["tribal", "rural", "women", "sc/st",
                                         "agency", "slum", "migrant"]) else 1
    return min(99, int((severity * 1.6 + reach * 1.4 + equity * 1.2) * 3.3))


def route_capabilities(domains, district, institutions, k=3, state=None):
    """Capability-graph routing with an explanation attached to every score."""
    wanted = dict(domains)
    out = []
    for inst in institutions:
        caps = [c.strip() for c in inst["caps"].split(",")]
        overlap = [c for c in caps if c in wanted]
        if not overlap:
            continue
        cap_fit = sum(wanted[c] for c in overlap)
        same_district = inst["district"].lower() == (district or "").lower()
        same_state = (inst.get("state") or "").lower() == (state or "").lower()
        proximity = 0.18 if same_district else (0.07 if same_state else 0)
        why = ["capability match: " + ", ".join(overlap)]
        if same_district:
            why.append("same district as the problem")
        elif same_state:
            why.append("same state, field visits are practical")
        if len(overlap) > 1:
            why.append("multidisciplinary cover")
        if inst["load"] < 5:
            why.append("%d project slots open" % (5 - inst["load"]))
        # Scoring, in points out of 100, so no single factor can swamp the rest:
        #   capability depth  0-65   how much of the problem the institution covers
        #   proximity         0-20   same district beats same state beats anywhere
        #   multidisciplinary 0-6    more than one matching capability
        #   free capacity     0-7.5  open project slots
        score = (cap_fit * 65
                 + (20 if same_district else (11 if same_state else 0))
                 + (6 if len(overlap) > 1 else 0)
                 + max(0, 5 - inst["load"]) * 1.5)
        out.append({
            "inst_id": inst["id"], "name": inst["name"], "district": inst["district"],
            "state_match": bool(same_state),
            "fit": min(97, int(round(score))),
            "why": " - ".join(why),
        })
    out.sort(key=lambda x: -x["fit"])

    # State preference rule: a state innovation cell wants the work to stay in the
    # state when the capability is comparable. If an institution from the same state
    # is within 8 points of the leader, it is promoted - and the reason is recorded,
    # so nobody has to guess why the ranking moved.
    if out and state:
        leader = out[0]
        if leader.get("state_match") is not True:
            for cand in out[1:]:
                if cand.get("state_match") and leader["fit"] - cand["fit"] <= 8:
                    cand["why"] += " - promoted over a higher scoring outside institution " \
                                   "under the keep-it-in-the-state rule"
                    out.remove(cand)
                    out.insert(0, cand)
                    break
    return out[:k]


def csr_match(primary, partners):
    clause = DOMAINS[primary]["clause"]
    eligible = [p for p in partners if primary in p["focus"].split(",")]
    return clause, eligible


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------

def run_pipeline(raw_text, lang, district, existing, institutions, partners, state=None):
    """Returns a dict the route layer can persist and the template can render."""
    steps = []

    def step(name, detail, conf, ok=True):
        steps.append({"name": name, "detail": detail,
                      "conf": conf, "pct": int(conf * 100), "ok": ok})

    text, translated = normalise(raw_text, lang)
    step("Voice and language intake",
         "Source language %s%s" % (LANGUAGES.get(lang, lang),
                                   " - translated to English for processing" if translated
                                   else " - no translation needed"),
         0.94 if translated else 0.99)

    clean, hits = redact_pii(text)
    step("PII detection and redaction",
         "%d identifier(s) masked before the text entered the queue" % hits if hits
         else "No direct identifiers found", 0.97)

    dup, sim = find_duplicate(clean, existing)
    if dup:
        step("Deduplicate and cluster",
             "Same issue as %s (similarity %.2f) - recorded as a supporter" % (dup, sim),
             sim, ok=False)
    else:
        step("Deduplicate and cluster",
             "New cluster. Closest open challenge scored %.2f" % sim, 0.90)

    scope, sconf = scope_classify(clean)
    if scope == "grievance":
        step("Scope classifier", "Individual grievance - outside the innovation mandate",
             sconf, ok=False)
        step("Route", "Forwarded to CPGRAMS / state grievance portal with an "
                      "acknowledgement to the citizen", sconf)
        return {"accepted": False, "reason": "grievance", "duplicate": dup,
                "steps": steps, "text": clean}

    step("Scope classifier", "Societal innovation challenge - accepted into the queue", sconf)

    domains = classify_domain(clean)
    primary = domains[0][0]
    detail = "%s (%d%%)" % (DOMAINS[primary]["label"], int(domains[0][1] * 100))
    if len(domains) > 1:
        detail += ", secondary %s" % DOMAINS[domains[1][0]]["label"]
    step("Domain classification", detail, domains[0][1])

    priority = priority_score(clean)
    step("Priority scoring", "Severity x reach x equity = %d of 99" % priority,
         round(priority / 99, 2))

    matches = route_capabilities(domains, district, institutions, state=state)
    if matches:
        step("Capability routing engine",
             "%d institutions ranked, lead fit %d%%" % (len(matches), matches[0]["fit"]),
             round(matches[0]["fit"] / 100, 2))
    else:
        step("Capability routing engine",
             "No capability match - escalated to the state nodal officer", 0.30, ok=False)

    clause, funders = csr_match(primary, partners)
    step("CSR eligibility check",
         clause if funders else "No mapped CSR partner - routed to the state R&D grant window",
         0.88 if funders else 0.50, ok=bool(funders))

    if dup:
        return {"accepted": False, "reason": "duplicate", "duplicate": dup,
                "steps": steps, "text": clean}

    return {
        "accepted": True, "text": clean, "steps": steps, "duplicate": None,
        "domain": primary, "domain_label": DOMAINS[primary]["label"],
        "priority": priority, "matches": matches, "confidence": sconf,
        "csr_clause": clause, "csr_eligible": bool(funders),
        "csr_partners": [p["name"] for p in funders],
        "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }
