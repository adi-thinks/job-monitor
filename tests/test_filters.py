"""Scope rules: India location, BA / Data Analyst / Product role, seniority tier, experience.

These are the judgements every posting passes through, and getting one wrong is
silent - the run succeeds, the log looks tidy, and postings quietly stop
arriving (or the wrong ones start to). Most cases below are real titles seen
on the boards this repo scans.
"""
import pytest

from monitor import filters as F
from monitor.fetchers.generic import _find_facet, workday_country


# ---- India location --------------------------------------------------------

@pytest.mark.parametrize("loc", [
    "Bengaluru, Karnataka, India", "Bangalore", "Hyderabad", "Pune, MH, IN",
    "Gurugram, Haryana", "Gurgaon", "Noida, Uttar Pradesh, India", "Chennai",
    "Mumbai", "Navi Mumbai", "New Delhi", "Kochi", "Remote - India", "India",
    "Pune Division, Maharashtra, India",
    "KA, IN", "MH, IN",                         # Indeed's state-code format
    "San Francisco, CA; Bengaluru, India",      # one Indian site carries it
])
def test_india_locations_are_kept(loc):
    assert F.is_india(loc) is True


@pytest.mark.parametrize("loc", [
    "San Francisco, CA", "London, UK", "Singapore", "Remote",
    "3 Locations", "", "Indianapolis, IN", "Indiana", "Dublin, Ireland",
])
def test_non_india_or_unknown_locations_are_dropped(loc):
    """Unknown is dropped: on a global board it is almost never India-open."""
    assert F.is_india(loc) is False


def test_an_explicit_country_settles_it():
    assert F.is_india("3 Locations", country="India") is True
    assert F.is_india("Remote", country="IN") is True
    assert F.is_india("Remote", country="US") is False


def test_workday_country_reads_the_url_slug():
    assert workday_country("/job/BangaloreIndia/SWE_R5") == "India"
    assert workday_country("/job/India-Hyderabad/SWE_R6") == "India"
    assert workday_country("/job/US-CA-Santa-Clara/SWE_R1") == "US"
    assert workday_country("/job/Somewhere-Odd/SWE_R6") == ""


def test_workday_blank_location_falls_back_to_the_url_slug():
    """Accenture leaves locationsText empty; the city is still in the URL."""
    from monitor.fetchers.generic import workday_slug_location
    assert workday_slug_location("/job/Pune/Java-Dev_R1") == "Pune"
    assert workday_slug_location("/job/India-Hyderabad/SWE_R6") == "India Hyderabad"
    assert workday_slug_location("") == ""


def test_workday_india_facet_is_found_even_when_nested():
    facets = [
        {"facetParameter": "jobFamilyGroup", "values": [{"descriptor": "Engineering", "id": "e1"}]},
        {"facetParameter": "locationMainGroup", "values": [
            {"facetParameter": "locationCountry", "descriptor": "Country", "values": [
                {"descriptor": "United States of America", "id": "us1"},
                {"descriptor": "India", "id": "in1"},
            ]},
        ]},
    ]
    assert _find_facet(facets, "India") == {"locationCountry": ["in1"]}
    assert _find_facet(facets, "Narnia") == {}


# ---- role and tier ---------------------------------------------------------

@pytest.mark.parametrize("title,tier", [
    ("Business Analyst", "mid"),
    ("Technical Business Analyst", "mid"),
    ("Business Systems Analyst", "mid"),
    ("Business Analyst II", "mid"),
    ("Business Analyst I/II", "mid"),                  # a band reaching II
    ("Business Analyst - Associate", "mid"),           # bank grade, not entry
    ("Data Analyst", "mid"),
    ("Business Intelligence Analyst", "mid"),
    ("Analytics Engineer", "mid"),
    ("Power BI Developer", "mid"),
    ("Product Manager", "mid"),
    ("AI Product Manager", "mid"),
    ("Product Manager, Data Platform", "mid"),         # 'data' here is not a manager title
    ("Product Manager - Software Products", "mid"),    # 'software' alone is fine
    ("Product Owner", "mid"),
    ("Senior Business Analyst", "senior"),
    ("Sr. BA", "senior"),
    ("Business Analyst III", "senior"),
    ("Senior Data Analyst", "senior"),
    ("Senior Business Intelligence Engineer", "senior"),
    ("Senior Associate, Data Analyst", "senior"),
    ("Assistant Manager - Business Analytics", "senior"),
    ("Senior Product Manager", "senior"),
    ("Senior Product Analyst", "senior"),
    ("Lead Business Analyst", "lead"),
    ("Analytics Manager", "lead"),
    ("Manager - Data Analytics", "lead"),
    ("Group Product Manager", "lead"),
    ("Senior Manager, Product Management", "lead"),
])
def test_in_scope_titles_get_a_tier(title, tier):
    assert F.classify(title) == tier


@pytest.mark.parametrize("title", [
    # below the band
    "Associate Product Manager", "Associate Business Analyst", "Business Analyst I",
    "Product Manager I", "Data Analyst Intern", "Graduate Data Analyst",
    "Business Analyst Trainee", "Junior Data Analyst", "Data Analyst - Fresher",
    # above the band
    "Director, Product Management", "VP Product", "Head of Product",
    "Principal Product Manager", "Staff Product Manager", "AVP - Business Analytics",
    # engineering and science
    "Data Scientist", "Senior Data Engineer", "Software Engineer",
    "Sr Software Engineer, Product Analytics", "Machine Learning Engineer, Analytics",
    "Senior Backend Engineer", "Applied Scientist",
    # other kinds of analyst
    "Financial Analyst", "Credit Analyst", "Senior Security Analyst",
    "Senior Risk Analyst", "Fraud Analyst", "Equity Research Analyst",
    "Clinical Data Analyst",
    # near misses on the word 'product' or 'manager'
    "Product Designer", "Product Marketing Manager", "Production Manager",
    "Engineering Manager", "Project Manager", "Program Manager",
    # not these jobs
    "Technical Recruiter", "Java Developer",
])
def test_out_of_scope_titles_are_rejected(title):
    assert F.classify(title) is None


def test_include_staff_opens_the_door_deliberately():
    assert F.classify("Principal Product Manager") is None
    assert F.classify("Principal Product Manager", include_staff=True) == "lead"
    assert F.classify("Staff Product Manager") is None
    assert F.classify("Staff Product Manager", include_staff=True) == "lead"


@pytest.mark.parametrize("title,family", [
    ("Senior Product Manager", "product"),
    ("Product Owner", "product"),
    ("Senior Product Analyst", "product"),
    ("Data Analyst", "data"),
    ("Business Intelligence Analyst", "data"),     # not 'business'
    ("Analytics Engineer", "data"),
    ("Senior Business Analyst", "business"),
    ("Technical BA", "business"),
    ("Business Systems Analyst", "business"),
    ("Analyst", "analyst"),
])
def test_role_family_buckets(title, family):
    assert F.role_family(title) == family


def test_in_scope_annotates_and_filters_in_one_pass():
    job = {"title": "Senior Business Analyst", "location": "Bengaluru, India"}
    out = F.in_scope(dict(job))
    assert out["tier"] == "senior" and out["role"] == "business"
    assert F.in_scope(dict(job, location="Austin, TX")) is None
    assert F.in_scope(dict(job, title="Director of Product")) is None


@pytest.mark.parametrize("yoe,kept", [
    (None, True), (2, True), (4, True), (5, True), (8, True),
    (0, False), (1, False),        # explicitly junior
    (9, False), (12, False),       # explicitly director-level
])
def test_a_stated_experience_bar_outside_the_band_drops_the_posting(yoe, kept):
    job = {"title": "Senior Business Analyst", "location": "Pune", "yoe": yoe}
    assert (F.in_scope(dict(job)) is not None) is kept


# ---- years of experience ---------------------------------------------------

@pytest.mark.parametrize("text,want", [
    ("We require 5+ years of professional business analysis experience.", 5),
    ("You have at least 4 years of relevant experience", 4),
    ("Minimum of 8 years in industry", 8),
    ("4-8 years of experience in data analytics", 4),
    ("6+ yrs of experience with Power BI", 6),
    ("10+ years working on product strategy", 10),
    # the lowest stated bar is the reachable one
    ("3+ years of experience with SQL; 6+ years of Tableau", 3),
])
def test_a_stated_requirement_is_read(text, want):
    assert F.parse_yoe(text) == want


@pytest.mark.parametrize("text", [
    "Founded 15 years ago, we...",
    "5 years of company history",
    "Over the past 10 years of innovation",
    "A 4-year degree in CS",
    "Three years of experience",                # spelled out, not parsed
    "",
])
def test_things_that_are_not_a_requirement_are_ignored(text):
    assert F.parse_yoe(text) is None
