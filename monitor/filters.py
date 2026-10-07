"""Role, seniority and India-location filtering.

Scope (India, Business Analyst / Data Analyst / Product Manager track):
  - Roles: Business Analyst, Business Systems / Technical BA, Data Analyst,
    BI / Analytics (analyst, developer, engineer), Product Analyst, Product
    Manager, Product Owner. Engineer, scientist and other "analyst" jobs
    (financial, credit, security, research...) are out.
  - Seniority: tuned for ~4+ years of experience - Analyst / PM, Senior
    Analyst / Senior PM, and Lead / Manager. Interns, freshers, Associate
    Product Managers, "Analyst I" and Director / VP / Head-of titles are
    excluded. Principal / Staff are out by default; `--include-staff` lets
    them in.
  - Experience: a stated bar of 2-8 years passes (see YOE_MIN / YOE_MAX).
  - Location: India (any city, India-remote, or "India" itself).

Every rule here is a plain regex so it is easy to widen or narrow. The test
suite (tests/test_filters.py) pins the cases each one was written for.
"""
import re

# ---- role scope ------------------------------------------------------------
# A title must name one of the target jobs. Generic "Analyst" is NOT enough:
# that would admit every credit, risk, equity and security analyst in India.
ROLE_INCLUDE = re.compile(
    # business analysis
    r"business\s+(systems?\s+)?analy(st|sis)|\bba\b|systems?\s+analyst"
    r"|functional\s+analyst|techno.?functional"
    # data / BI / analytics
    r"|data\s+analy(st|tics)|analytics|business\s+intelligence"
    r"|\bbi\s+(analyst|developer|engineer|consultant)|reporting\s+analyst"
    r"|insights?\s+analyst|\bmis\s+analyst|decision\s+analyst"
    r"|analyst\W+(data|analytics|business\s+(analysis|analytics|intelligence)"
    r"|product|insights|bi\b|reporting)"
    # product
    r"|product\s+(manager|management|owner|lead|analyst)",
    re.I,
)

ROLE_EXCLUDE = re.compile(
    # leadership above the target band
    r"director|\bvp\b|\bavp\b|vice president|head of|chief|fellow|executive"
    r"|distinguished|\bcto\b|\bcpo\b|\bpresident\b"
    # engineering and science disciplines that merely mention analytics
    r"|\b(software|java|python|\.?net|web|mobile|full.?stack|front.?end|back.?end"
    r"|application|etl|sql|data|ml|ai|devops|cloud|platform|systems?|qa|test"
    r"|support|solutions?|sales|security|network|hardware|embedded|firmware"
    r"|infrastructure|reliability)\s+(engineer|developer)s?\b"
    r"|\bsde\b|\bswe\b|\bsdet\b|\bqa\b|tester|devops|\bsre\b|architect"
    r"|scientist|machine learning|\bml\b|deep learning"
    # other kinds of analyst
    r"|(security|cyber|soc|fraud|risk|credit|compliance|financial|finance|equity"
    r"|research|investment|treasury|tax|payroll|audit|quantitative|supply chain)"
    r"\s+analyst"
    r"|clinical|pharmacovigil|biostat|\bquant\b|actuar|underwrit|auditor"
    # not these jobs at all
    r"|recruit|talent acquisition|attorney|counsel|accountant",
    re.I,
)

# Titles that are below the target band no matter what else they say.
JUNIOR = re.compile(
    r"\bintern(ship)?\b|co-?op\b|trainee|fresher|apprentice|graduate|new ?grad"
    r"|campus|university|entry.?level|early.?career|junior|\bjr\.?\b"
    r"|master'?s|\bph\.?d\b"
    # \"Associate Product Manager\" / \"Associate Business Analyst\" are entry
    # grades. \"Business Analyst - Associate\" and \"Senior Associate\" are not
    # matched: at banks Associate is a mid grade.
    r"|(?<!senior )(?<!sr )(?<!sr\. )\bassociate\s+(product|business|data|bi"
    r"|systems?|functional|analyst)"
    r"|\bapm\b"
    # \"Analyst I\", \"Product Manager 1\" - but \"Analyst I/II\" is a band that
    # reaches II, so it stays.
    r"|(analyst|product manager|product owner)\s*[- ]?(i|1)\b(?!\s*[-/&]?\s*(i|ii|2)\b)",
    re.I,
)

# Principal / Staff: above the target band, admitted only by --include-staff.
STAFF = re.compile(r"(?<!technical )\bstaff\b|\bprincipal\b", re.I)

# ---- tier detection --------------------------------------------------------
# lead   - Lead / Group PM / Analytics Manager / Senior Manager
# senior - Senior / Sr / Assistant Manager / Analyst III+
# mid    - plain "Business Analyst", "Data Analyst", "Product Manager", "... II"
LEAD = re.compile(
    r"\blead\b|team lead|\bgroup product manager\b|\bgpm\b"
    r"|(?<!technical )\bstaff\b|\bprincipal\b"
    r"|\b(senior|sr\.?)\s+manager\b"
    r"|\b(analytics|business analysis|insights|data|bi|reporting)\s+manager\b"
    r"|^\s*manager\b[\s,\-:]+(analytics|business analysis|insights"
    r"|data analytics|business intelligence|bi\b)",
    re.I)
SENIOR = re.compile(
    r"\bsenior\b|\bsr\.?\b|\bassistant manager\b"
    r"|(analyst|manager|owner)\s*[- ]?(iii|3|iv|4)\b",
    re.I)

# ---- India location --------------------------------------------------------
INDIA_HINT = re.compile(
    r"\bindia\b|\bind\b|bharat"
    r"|bengaluru|bangalore|hyderabad|secunderabad|pune|chennai|mumbai|bombay"
    r"|navi mumbai|thane|gurgaon|gurugram|noida|greater noida|new delhi|\bdelhi\b"
    r"|\bncr\b|faridabad|ghaziabad|kolkata|ahmedabad|gandhinagar|gift city"
    r"|jaipur|kochi|cochin|trivandrum|thiruvananthapuram|coimbatore|mysore|mysuru"
    r"|mangalore|mangaluru|indore|bhopal|chandigarh|mohali|panchkula|nagpur"
    r"|vadodara|surat|lucknow|bhubaneswar|visakhapatnam|vizag|vijayawada"
    r"|madurai|hubli|goa|dehradun|kanpur|patna|ranchi|raipur|nashik|aurangabad"
    r"|karnataka|telangana|maharashtra|tamil nadu|haryana|uttar pradesh"
    r"|kerala|gujarat|west bengal|rajasthan|andhra pradesh|odisha",
    re.I,
)

# Indeed writes "KA, IN" / "MH, IN": an Indian state code, then the country.
# Requiring the state code keeps "Indianapolis, IN" (Indiana) out.
INDIA_STATE_CODE = re.compile(
    r"\b(KA|MH|TN|TS|TG|AP|UP|HR|DL|WB|GJ|RJ|KL|MP|PB|CH|GA|OR|OD|UK|UL|JH|BR|CG|AS)"
    r"\s*,\s*IN\s*$")

ISO_INDIA = ("in", "ind", "india", "bharat")

LOC_SPLIT = re.compile(r"\s*[;|]\s*|\s+/\s+")


def _site_is_india(loc: str) -> bool:
    # A bare ", IN" suffix is deliberately not a signal - it is also Indiana.
    return bool(INDIA_HINT.search(loc) or INDIA_STATE_CODE.search(loc))


def is_india(location: str, country: str = "") -> bool:
    """True when any site of the posting is in India.

    Unlike a "keep if unsure" rule, an unknown location ("Remote", "3
    Locations") is dropped: the boards scanned here are global, and an
    unlabelled remote role at a US company is almost never India-open. Sources
    that already restrict to India (Naukri, LinkedIn with location=India,
    Workday with country: India) supply the country explicitly.
    """
    if country and country.strip().lower() in ISO_INDIA:
        return True
    loc = (location or "").strip()
    if not loc:
        return False
    return any(_site_is_india(p.strip()) for p in LOC_SPLIT.split(loc) if p.strip())


# ---- role family -----------------------------------------------------------
# First match wins. "Business Intelligence Analyst" must land in data, not
# business, so the data pattern is checked before the business one.
ROLE_FAMILY = [
    ("product", re.compile(r"product\s+(manager|management|owner|lead|analyst)", re.I)),
    ("data", re.compile(
        r"data\s+analy|analytics|business\s+intelligence|\bbi\b|reporting"
        r"|insights?|\bmis\b|decision\s+analyst", re.I)),
    ("business", re.compile(
        r"business\s+(systems?\s+)?analy|\bba\b|systems?\s+analyst"
        r"|functional|techno.?functional", re.I)),
]


def role_family(title: str) -> str:
    """Coarse bucket, for filtering the dashboard."""
    for name, pattern in ROLE_FAMILY:
        if pattern.search(title or ""):
            return name
    return "analyst"           # an analyst title that names no discipline


def classify(title: str, include_staff: bool = False) -> str | None:
    """Return tier string if the title is in scope, else None."""
    if not title or ROLE_EXCLUDE.search(title) or JUNIOR.search(title):
        return None
    if not ROLE_INCLUDE.search(title):
        return None
    if STAFF.search(title) and not include_staff:
        return None
    if LEAD.search(title):
        return "lead"
    if SENIOR.search(title):
        return "senior"
    return "mid"


# Stated experience bars outside this band are not a fit for ~4+ years.
# parse_yoe returns the LOWEST number in the posting ("5-8 years" -> 5), so a
# floor of 2 only drops postings that are explicitly junior ("0-1 years"), and
# a ceiling of 8 drops the ones that open at 9+ years (Director-level asks).
YOE_MIN = 2
YOE_MAX = 8


def in_scope(job: dict, include_staff: bool = False) -> dict | None:
    tier = classify(job.get("title", ""), include_staff)
    if tier is None:
        return None
    if not is_india(job.get("location", ""), job.get("country", "")):
        return None
    yoe = job.get("yoe")
    if yoe is not None and not (YOE_MIN <= yoe <= YOE_MAX):
        return None
    job["tier"] = tier
    job["role"] = role_family(job.get("title", ""))
    return job


# ---- years of experience ---------------------------------------------------
# The tier a title implies is often wrong ("Software Engineer" says nothing),
# so where a posting states its own bar in prose we read it. Only a stated
# requirement counts - company history ("founded 15 years ago"), degree length
# ("4-year degree") and anniversaries must not register.

# "years" only counts when what follows reads like a requirement, never "ago".
YOE_RE = re.compile(
    r"(?:(?:minimum|min\.?|at least)\s+(?:of\s+)?)?"
    r"(\d{1,2})\s*(?:\+|plus)?\s*(?:[-–]|to)?\s*(?:\d{1,2})?\s*(?:\+|plus)?\s*"
    r"(?:years?|yrs?)\b(?!\s+ago)"
    r"\s+(?:of|in|with|working|building|developing|professional|relevant"
    r"|industry|hands.?on|post|full.?time|prior|related|applicable|exp)",
    re.I)

# Cues just before the number that mean it is describing the company, not you.
YOE_HISTORY = re.compile(
    r"(founded|formed|established|spent|celebrat|anniversary|history|been around"
    r"|over the (past|last)|in the (past|last)|for the (past|last)|since)\b[^.]{0,40}$",
    re.I)

# ...and cues just after it, for the same reason ("10 years of company history").
YOE_HISTORY_AFTER = re.compile(
    r"^\s*(of\s+)?(company|corporate|business|operation|growth|history|innovation"
    r"|partnership|service|success)", re.I)

# "4-year degree", "four year program" - length of study, not experience.
YOE_DEGREE = re.compile(r"\d\s*[-\s]?year\s+(degree|program|university|college|school)", re.I)


def parse_yoe(text: str, title: str = "") -> int | None:
    """Lowest stated years-of-experience requirement, or None if unstated.

    The minimum is taken rather than the maximum: a posting asking for "4+
    years backend, 8+ years distributed systems" is reachable at four.
    """
    if not text or re.search(r"\bintern(ship)?\b", title or "", re.I):
        return None                      # an internship never states a real bar
    best = None
    for m in YOE_RE.finditer(text):
        before = text[max(0, m.start() - 60): m.start()]
        if YOE_HISTORY.search(before):
            continue
        if YOE_HISTORY_AFTER.search(text[m.end(): m.end() + 40]):
            continue
        if YOE_DEGREE.search(text[max(0, m.start() - 20): m.end() + 20]):
            continue
        n = int(m.group(1))
        if 0 <= n <= 20:
            best = n if best is None else min(best, n)
    return best
