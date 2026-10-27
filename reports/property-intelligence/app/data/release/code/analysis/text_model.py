"""Description text / topic analysis for Auckland Property Scout.

This module turns the free-text ``listings.body`` field into:

* a cleaned description (agency / URL / contact boilerplate removed),
* a 12-topic TF-IDF + NMF decomposition with human labels and top terms,
* eight interpretable lexicon scores (urgency, luxury, condition, views, family, investment,
  risk, readability) plus word and exclamation counts,
* association tests between text features and two price signals, controlling for suburb,
  property type, size, days on market, tenure and sale method (OLS, HC3 robust SE, BH FDR),
* an incremental out-of-fold Ridge test: structural features only vs structural + text,
* an exploratory price-change test on the Homes AVM estimate history,
* ``text_features.description_index``: a cross-fitted, standardised percent premium/discount
  implied by the description language after stripping structural expectations (0 = neutral).

Everything is stored in four tables created here (``text_topics``, ``listing_topics``,
``text_features``, ``text_metrics``); the existing schema is never modified.

Usage::

    from analysis import text_model
    summary = text_model.run(connection)

    # or, from the command line
    python -m analysis.text_model --db data/auckland_property.db

The model is deterministic: fixed random seed, deterministic near-duplicate filter, sorted
vocabulary. Re-running on the same data reproduces the same topics and metrics.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sqlite3
import sys
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import sparse
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, r2_score
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.multitest import multipletests

MODEL_VERSION = "text-nmf-v1"
N_TOPICS = 12
RANDOM_SEED = 42
N_SPLITS = 5
RIDGE_ALPHA = 1.0
DESCRIPTION_INDEX_CLIP_Z = 3.0

# TF-IDF settings (unigrams + bigrams).
MIN_DF = 6
MAX_DF = 0.45
MAX_FEATURES = 4500

# Near-duplicate descriptions are excluded from the NMF *fit* (but still transformed), because
# several developers list 4-10 near-identical spec homes; without this the topics are dominated
# by marketing copy shared across those listings.
NEAR_DUP_COSINE = 0.50

# A line repeated verbatim across at least this many listings is treated as cross-listing
# developer/agency boilerplate and removed from descriptions.
REPEATED_LINE_MIN_LISTINGS = 6
REPEATED_LINE_MIN_WORDS = 5

# Fallback: if dropping repeated lines leaves almost nothing, keep them (some spec-home
# descriptions are almost entirely shared copy); topic weights then reflect that.
MIN_CLEANED_WORDS = 20

# A listing with only a title/search record has no usable description. Exclude it from
# the text model instead of pretending the empty string is a document.
MIN_DESCRIPTION_CHARS = 50

MIN_LISTINGS = 24

TOP_TERMS_PER_TOPIC = 12

# The 17 target suburbs (Trade Me / display names). Used to redact suburb names before topic
# modelling so topics capture property characteristics rather than location branding. The
# structural model already controls for suburb.
TARGET_SUBURB_NAMES: tuple[str, ...] = (
    "Browns Bay", "Murrays Bay", "Mairangi Bay", "Rothesay Bay", "Campbells Bay",
    "Castor Bay", "Milford", "Long Bay", "Waiake", "Torbay", "Takapuna", "Devonport",
    "Mission Bay", "Kohimarama", "Saint Heliers", "St Heliers", "Glendowie", "Orakei",
    "Ōrākei", "Orākei",
)

# ---------------------------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------------------------

_URL_RE = re.compile(r"(?:https?://\S+|www\.\S+|\b[\w.+-]+@[\w-]+\.[\w.]+)", re.IGNORECASE)
_PHONE_RE = re.compile(r"(?:\+?64[\s-]?|0)(?:\d[\s()\-]?){7,12}\b")
_RAW_LINE_SPLIT_RE = re.compile(r"[\r\n]+")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_BULLET_RE = re.compile(r"^[\s\u2022\u25aa\u25cf\u25e6\u00b7\u2013\u2014*\-\u2023]+")
_ENUM_RE = re.compile(r"^\d{1,2}[.)]\s+")
_NON_TEXT_RE = re.compile(r"[^a-z0-9\u00c0-\u024f\s]")
_NZ_M2_RE = re.compile(r"(\d+)\s?(?:m2|m\u00b2|sq\.?\s?m|sqm)\b", re.IGNORECASE)
_LEADING_O_RE = re.compile(r"^[oO]\s+(?=\d)")

# Sentence/line-level boilerplate. These patterns are narrow on purpose: property language
# (e.g. "open plan", "call this home", "private view") must survive.
_BOILERPLATE_PATTERNS: tuple[str, ...] = (
    r"see interactive features",
    r"view (?:the )?office website",
    r"copy (?:and|&) paste",
    r"click (?:the|here|on)\b",
    r"barfoot(?:\.co\.nz|\s*&?\s*thompson)?",
    r"harcourts",
    r"ray white",
    r"bayleys",
    r"sotheby",
    r"\bre/?max\b",
    r"keller williams",
    r"century 21",
    r"lj hooker",
    r"conjunctional|conjunctions? (?:from|are|welcome)|all agencies conjunction",
    r"\bcontact (?:us|me|our|the agent|the team)\b",
    r"\bcall [a-z]+",
    r"\b(?:phone|mobile|email|e-mail)\b",
    r"trade ?me",
    r"licensed (?:salesperson|agent)|real estate agents act|\breaa\b",
    r"this property may be marketed as suitable|constitute confirmation of eligibility",
    r"overseas investment (?:laws?|act|office|consent)|subject to new zealand|"
    r"independent legal advice|obtain your own|requirement to obtain consent",
    r"we cannot guarantee|all information (?:provided|contained)|"
    r"information (?:is )?believed to be (?:correct|accurate)",
    r"\bdisclaimer\b",
    r"\bviewings?\b",
    r"\bopen (?:home|homes|house|houses)\b",
    r"\bby appointment\b",
    r"\bdeadline (?:sale|treaty|closes|close)\b|\bunless sold prior\b|"
    r"\b(?:offers?|tenders?) (?:close|closes|by|on)\b",
    r"\bzero deposit\b|\boffer ends\b|\bshow ?home\b",
    r"wolfbrook|david reid homes|g\.?j\.? gardner|jennian|signature homes|"
    r"landmark homes|fletcher living|universal homes|stamford build",
    r"for (?:more|further) (?:details|information)",
    r"\benquir(?:y|ies|e)\b",
    r"please contact|if you can'?t reach|\btext (?:us|me)\b",
    r"\bref(?:erence)?\s*(?:#|no\.?|number)",
    r"\b(?:mon|tues|wednes|thurs|fri|satur|sun)day\s+\d{1,2}(?:st|nd|rd|th)?\s+"
    r"(?:january|february|march|april|may|june|july|august|september|october|november|december)",
    r"\b\d{1,2}[.:]\d{2}\s*(?:am|pm|a m|p m)?\s*(?:-|to|until)\s*\d{1,2}[.:]\d{2}",
    r"download (?:view|the)|particulars",
    r"photo(?:s|graph)? (?:are|is) (?:indicative|an artist|artist)",
)
_BOILERPLATE_RE = re.compile(r"(?:" + r"|".join(_BOILERPLATE_PATTERNS) + r")", re.IGNORECASE)


def _strip_accents_preserve_macrons(text: str) -> str:
    """NFKC-normalise but keep Latin macrons (used in Māori place names)."""
    return unicodedata.normalize("NFKC", text)


def normalise_line(line: str) -> str:
    """Normalise a raw line for cross-listing duplication detection."""
    line = line.lower().strip()
    line = re.sub(r"[^a-z0-9\s]", " ", line)
    return re.sub(r"\s+", " ", line).strip()


def detect_repeated_lines(
    bodies: Sequence[str],
    *,
    min_listings: int = REPEATED_LINE_MIN_LISTINGS,
    min_words: int = REPEATED_LINE_MIN_WORDS,
) -> frozenset[str]:
    """Find lines that appear verbatim in at least ``min_listings`` distinct listings.

    These are cross-listing developer / agency boilerplate (e.g. the same "why you'll love it"
    paragraph reused across a development's listings). They are excluded from topic fitting.
    """
    counts: Counter[str] = Counter()
    for body in bodies:
        seen = set()
        for line in _RAW_LINE_SPLIT_RE.split(body or ""):
            if len(line.strip()) < 12:
                continue
            norm = normalise_line(line)
            if len(norm.split()) < min_words:
                continue
            seen.add(norm)
        counts.update(seen)
    return frozenset(line for line, n in counts.items() if n >= min_listings)


def _clean_sentences(line: str) -> list[str]:
    """Clean one raw line into a list of kept sentences."""
    line = _BULLET_RE.sub("", line.strip())
    line = _LEADING_O_RE.sub("", line)
    line = _ENUM_RE.sub("", line)
    line = _URL_RE.sub(" ", line)
    if not line.strip():
        return []
    kept: list[str] = []
    for sentence in _SENTENCE_SPLIT_RE.split(line):
        sentence = sentence.strip(' .,;:!?-\u2013\u2014"\'')
        if len(sentence.split()) < 3:
            continue
        if _BOILERPLATE_RE.search(sentence):
            continue
        kept.append(sentence)
    return kept


def clean_text(body: str | None, *, drop_lines: frozenset[str] | None = None) -> str:
    """Clean a listing description into normalised property language.

    Pipeline: NFKC normalise, strip HTML, remove apostrophes inside words (``don't`` -> ``dont``),
    drop repeated cross-listing lines, strip bullets/numbering/URLs/emails/phones, split into
    sentences, drop short fragments and agency/contact/legal boilerplate sentences, strip
    remaining punctuation, normalise area units (``683m2`` -> ``683 sqm``), lowercase and
    collapse whitespace.

    The function is pure so it can be unit-tested on arbitrary strings.
    """
    drop = drop_lines or frozenset()
    text = _strip_accents_preserve_macrons(body or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = (
        text.replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("&", " and ")
    )
    text = re.sub(r"(?<=\w)['](?=\w)", "", text)

    kept: list[str] = []
    for raw_line in _RAW_LINE_SPLIT_RE.split(text):
        if raw_line.strip() and normalise_line(raw_line) in drop:
            continue
        kept.extend(_clean_sentences(raw_line))

    cleaned = " ".join(kept)
    cleaned = re.sub(r"(?<=\w)['](?=\w)", "", cleaned)
    cleaned = _NZ_M2_RE.sub(r"\1 sqm", cleaned)
    cleaned = _NON_TEXT_RE.sub(" ", cleaned.lower())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def clean_corpus(bodies: Sequence[str]) -> tuple[list[str], dict[str, Any]]:
    """Clean a corpus, detecting and dropping cross-listing boilerplate first.

    Returns the cleaned texts and cleaning statistics used in the research write-up.
    """
    repeated = detect_repeated_lines(bodies)
    cleaned: list[str] = []
    fallback_docs = 0
    raw_words = 0
    clean_words = 0
    for body in bodies:
        raw_words += len((body or "").split())
        text = clean_text(body, drop_lines=repeated)
        if len(text.split()) < MIN_CLEANED_WORDS:
            text = clean_text(body)  # keep shared copy rather than losing the description
            fallback_docs += 1
        clean_words += len(text.split())
        cleaned.append(text)
    stats = {
        "documents": len(cleaned),
        "raw_words": raw_words,
        "cleaned_words": clean_words,
        "word_retention": round(clean_words / raw_words, 4) if raw_words else 0.0,
        "repeated_lines_dropped": len(repeated),
        "fallback_documents": fallback_docs,
        "empty_documents": sum(1 for text in cleaned if not text.strip()),
    }
    return cleaned, stats


# ---------------------------------------------------------------------------------------------
# Suburb redaction
# ---------------------------------------------------------------------------------------------

def _suburb_pattern(suburb_names: Iterable[str]) -> re.Pattern[str]:
    names = sorted({n.strip() for n in suburb_names if n and n.strip()}, key=len, reverse=True)
    if not names:
        return re.compile(r"(?!)")  # never matches
    return re.compile(r"\b(?:" + "|".join(re.escape(n) for n in names) + r")\b", re.IGNORECASE)


def redact_suburbs(text: str, suburb_names: Iterable[str] = TARGET_SUBURB_NAMES) -> str:
    """Replace target-suburb names with the token ``suburb``.

    Location branding otherwise dominates topic modelling (five of twelve topics were pure
    suburb-name clusters), while the structural model already controls for suburb.
    """
    return _suburb_pattern(suburb_names).sub(" suburb ", text)


# ---------------------------------------------------------------------------------------------
# Tokenisation & stopwords
# ---------------------------------------------------------------------------------------------

# Generic marketing puffery that carries no property information. These words stay available
# to the lexicon scores (a luxury listing still scores high on the luxury lexicon) but are
# excluded from the topic vocabulary so topics describe concrete property attributes.
TOPIC_FLUFF_STOPWORDS: frozenset[str] = frozenset(
    """
    absolute absolutely amazing awesome beautiful beautifully breathtaking charming delightful
    easily effortless effortlessly enviable everyday exceptional exquisite fabulous fantastic
    gorgeous great greatest ideal impeccable incredible lovely meticulously perfect perfectly
    plenty precisely prestigious rare remarkable renowned sensational simply sought stunning
    superb truly ultimate ultimately unparalleled vibrant wonderful
    """.split()
)

DOMAIN_STOPWORDS: frozenset[str] = frozenset(
    """
    located location situated offering offers opportunity opportunities features featuring ample
    approx approximately today available also dont miss just whether theres youll youre didnt cant
    wont welcome discover imagine experience boasts boast boasting offer offered provides
    providing ensures ensuring enables allows allowing creates creating giving gives make makes
    made look looks looking love loved loves enjoy enjoys enjoying get gets come comes take takes
    """.split()
)

TOPIC_STOPWORDS: frozenset[str] = (
    frozenset(ENGLISH_STOP_WORDS) | TOPIC_FLUFF_STOPWORDS | DOMAIN_STOPWORDS
)

_TOKEN_RE = re.compile(r"[a-z][a-z']{1,}")


def tokenize(text: str) -> list[str]:
    """Tokenise cleaned text for TF-IDF (letters only, stopwords and 1-char tokens removed)."""
    tokens = []
    for raw in _TOKEN_RE.findall(text):
        token = raw.replace("'", "")
        if len(token) >= 2 and token not in TOPIC_STOPWORDS:
            tokens.append(token)
    return tokens


# ---------------------------------------------------------------------------------------------
# Lexicon features
# ---------------------------------------------------------------------------------------------

LEXICONS: dict[str, tuple[str, ...]] = {
    "urgency": (
        "must sell", "must be sold", "motivated", "motivated vendor", "motivated seller",
        "vendor motivated", "urgent", "urgently", "asap", "quick sale", "sell quickly",
        "priced to sell", "price reduced", "price reduction", "reduced", "reduction",
        "negotiable", "serious buyers", "genuine buyers", "no time wasters", "will consider",
        "all offers", "offers over", "offers welcome", "offers invited", "bring offers",
        "present all offers", "vendor wants", "needs sold", "must go", "dont miss",
        "act now", "now is the time", "overseas vendor", "relocating", "relocation",
        "downsizing", "estate sale", "deceased estate", "mortgagee", "walk in walk out",
        "sold as is", "opportunity not to be missed", "submit your offer",
    ),
    "luxury": (
        "luxury", "luxurious", "prestigious", "premium", "executive", "architectural",
        "architecturally designed", "designer", "bespoke", "high end", "high spec",
        "high specification", "stunning", "exquisite", "elegant", "sophisticated", "resort",
        "infinity pool", "spa pool", "gourmet", "chef kitchen", "designer kitchen", "grand",
        "masterpiece", "award winning", "five star", "world class", "exclusive",
        "private lift", "gated", "top of the line", "exceptional", "remarkable", "breathtaking",
        "plush", "opulent", "sumptuous", "deluxe",
    ),
    "condition_renovation": (
        "renovated", "renovation", "renovations", "refurbished", "modernised", "modernized",
        "updated", "new kitchen", "new bathroom", "new roof", "double glazed", "double glazing",
        "insulated", "heat pump", "central heating", "air conditioning", "rewired", "replumbed",
        "repainted", "freshly painted", "polished floors", "move in ready", "immaculate",
        "pristine", "meticulously maintained", "well maintained", "tidy", "low maintenance",
        "do up", "original condition", "requires work", "renovation project", "add value",
        "blank canvas", "handyman", "needs work", "deferred maintenance", "character",
        "native timber", "villa", "bungalow", "weatherboard", "brick", "single level",
        "rumpus", "sleepout", "granny flat", "minor dwelling", "reclad", "as is",
        "as is where is", "potential to add", "unrenovated", "dated", "original",
    ),
    "views_waterfront": (
        "sea view", "sea views", "water view", "water views", "ocean view", "ocean views",
        "harbour view", "harbour views", "city view", "city views", "skyline", "island view",
        "bay view", "bay views", "beach view", "waterfront", "beachfront", "absolute waterfront",
        "seafront", "coastal", "cliff top", "clifftop", "elevated", "panoramic", "vista",
        "vistas", "outlook", "sea", "harbour", "gulf", "lake view", "lake views", "lake",
        "rangitoto", "hauraki gulf", "sunset", "north facing", "north-facing",
    ),
    "family_school": (
        "family", "families", "children", "kids", "school", "schools", "in zone",
        "school zone", "school zones", "zoned for", "grammar", "college", "primary school",
        "intermediate", "kindergarten", "playground", "fenced", "fully fenced", "lawn",
        "garden", "cul de sac", "cul-de-sac", "quiet street", "safe", "park", "beach",
        "walk to school", "family friendly", "extended family", "teenagers", "pets",
        "family home", "families", "play area",
    ),
    "investment": (
        "investment", "investor", "investors", "rental", "rent", "rental return",
        "rental appraisal", "rental income", "yield", "gross yield", "net yield", "return",
        "returns", "tenant", "tenanted", "tenant in place", "land bank", "land banking",
        "development", "development opportunity", "subdivision", "subdividable",
        "resource consent", "thab", "terraced housing", "mixed housing", "home and income",
        "income", "portfolio", "capital gain", "capital growth", "high growth", "cashflow",
        "positive cashflow", "upside", "good investment", "blue chip", "passive income",
        "rental property", "investment property",
    ),
    "risk": (
        "leasehold", "leasehold title", "cross lease", "crosslease", "plaster", "monolithic",
        "leaky", "leaky home", "weathertight", "weathertightness", "reclad", "recladding",
        "remediation", "earthquake", "asbestos", "flood", "flooding", "overland flow",
        "vulnerable", "unconsented", "no consent", "no code of compliance", "defects",
        "defect", "damp", "dampness", "moisture", "mould", "mold", "draughty", "drafty",
        "deferred maintenance", "do up", "as is", "as is where is", "sold as is", "hard yakka",
        "mortgagee", "deceased estate", "estate sale", "stucco", "plaster over", "eifs",
        "high body corporate", "body corporate levy", "strictly as is",
    ),
}

# Longest phrases first so "sea views" consumes the match before "sea"/"views".
_LEXICON_RES: dict[str, re.Pattern[str]] = {
    name: re.compile(
        r"\b(?:" + "|".join(re.escape(p) for p in sorted(phrases, key=lambda p: -len(p.split())))
        + r")\b"
    )
    for name, phrases in LEXICONS.items()
}

_LEXICON_COLUMNS: tuple[str, ...] = (
    "urgency", "luxury", "condition_renovation", "views_waterfront",
    "family_school", "investment", "risk",
)


def lexicon_hits(text: str) -> dict[str, int]:
    """Raw phrase-match counts per lexicon for one cleaned description."""
    return {name: len(pattern.findall(text)) for name, pattern in _LEXICON_RES.items()}


def _syllables(word: str) -> int:
    """Rough syllable count (vowel groups), for a Flesch readability placeholder."""
    groups = re.findall(r"[aeiouy]+", word)
    count = len(groups)
    if word.endswith("e") and not word.endswith(("le", "ee")) and count > 1:
        count -= 1
    return max(1, count)


def readability_placeholder(cleaned_text: str, raw_body: str) -> float:
    """Flesch Reading Ease rescaled to 0-1, a placeholder not a validated readability test.

    Sentence boundaries are approximated from the raw body (the cleaned text has punctuation
    stripped); syllables are estimated from vowel groups. Property copy is short and
    elliptical, so treat this as a descriptive feature only.
    """
    words = cleaned_text.split()
    if not words:
        return 0.0
    sentences = max(1, len(_SENTENCE_SPLIT_RE.split(_URL_RE.sub(" ", raw_body or ""))))
    syllables = sum(_syllables(word) for word in words)
    flesch = 206.835 - 1.015 * (len(words) / sentences) - 84.6 * (syllables / len(words))
    return round(min(100.0, max(0.0, flesch)) / 100.0, 4)


def build_lexicon_frame(cleaned_texts: Sequence[str], raw_bodies: Sequence[str]) -> pd.DataFrame:
    """Compute lexicon hits and 0-1 normalised scores for every listing.

    Raw density is hits per 100 cleaned words. Scores are scaled by the 95th percentile of
    positive density (clipped to 0-1), so a score of 1 means "unusually heavy use of this
    lexicon relative to the corpus" rather than an absolute count. This keeps scores comparable
    across short and long descriptions.
    """
    rows = []
    hits_rows = []
    for text, body in zip(cleaned_texts, raw_bodies):
        hits = lexicon_hits(text)
        hits["word_count"] = len(text.split())
        hits["exclamations"] = (body or "").count("!")
        hits["readability"] = readability_placeholder(text, body or "")
        hits_rows.append(hits)
    raw = pd.DataFrame(hits_rows)

    out = pd.DataFrame(index=raw.index)
    word_counts = raw["word_count"].clip(lower=1)
    for name in _LEXICON_COLUMNS:
        density = raw[name].astype(float) / word_counts * 100.0
        positive = density[density > 0]
        scale = float(np.percentile(positive, 95)) if len(positive) else 0.0
        scale = max(scale, 0.05)
        out[name] = np.clip(density / scale, 0.0, 1.0).round(4)
    out["word_count"] = raw["word_count"].astype(int)
    out["exclamations"] = raw["exclamations"].astype(int)
    out["readability"] = raw["readability"].astype(float)
    # Keep raw hits for auditability (one JSON object per row).
    out["lexicon_hits_json"] = [
        json.dumps({name: int(raw.loc[i, name]) for name in _LEXICON_COLUMNS})
        for i in raw.index
    ]
    return out


# ---------------------------------------------------------------------------------------------
# Topic model
# ---------------------------------------------------------------------------------------------

def _independent_documents(tfidf: sparse.spmatrix, threshold: float = NEAR_DUP_COSINE) -> np.ndarray:
    """Greedy near-duplicate filter: keep a document only if no earlier kept doc is similar."""
    kept: list[int] = []
    for idx in range(tfidf.shape[0]):
        if not kept:
            kept.append(idx)
            continue
        sims = (tfidf[kept] @ tfidf[idx].T).toarray().ravel()
        if float(sims.max()) < threshold:
            kept.append(idx)
    return np.asarray(kept, dtype=int)


_TOPIC_RULES: tuple[tuple[str, frozenset[str]], ...] = (
    ("Westlake school zone", frozenset("westlake girls boys normal".split())),
    ("Rangitoto & Northcross school zones", frozenset(
        "rangitoto northcross sherwood intermediate college zoned".split())),
    ("Development & land potential", frozenset(
        "development site land subdivision consent housing mixed thab terrace existing zoning "
        "subdividable potential future council".split())),
    ("Sea views & coastal outlook", frozenset(
        "sea harbour gulf waterfront beachfront coastal elevated panoramic rangitoto "
        "hauraki outlook view views vista".split())),
    ("Luxury, architectural & prestige", frozenset(
        "luxury premium designer architectural residence prestige prestigious executive "
        "bespoke grand remarkable award architect kitchen appliances finishes sophisticated".split())),
    ("Apartment / lock-up-and-leave", frozenset(
        "apartment apartments lock leave balcony lift complex body corporate".split())),
    ("New build / brand-new quality", frozenset(
        "brand new standalone built construction build appliances quality finishes flooring "
        "modern".split())),
    ("Renovation & character", frozenset(
        "renovated renovation modernised refurbished original character do condition dated "
        "project value".split())),
    ("Resort amenities (pool / tennis / spa)", frozenset(
        "pool tennis spa gym resort court sauna swimming".split())),
    ("Brick / tile / low-maintenance units", frozenset(
        "brick tile unit units low maintenance sunny single".split())),
    ("Coastal village & park proximity", frozenset(
        "park village regional walking community centre shops cafes".split())),
    ("Auction / campaign logistics", frozenset(
        "auction sold prior unless november wednesday pm".split())),
    ("Investment & rental income", frozenset(
        "investment rental yield tenant income return investors rent".split())),
    ("Family living & entertaining", frozenset(
        "friends relaxed entertaining setting summer children outdoor family deck".split())),
    ("Bedrooms, bathrooms & layout", frozenset(
        "bedroom bedrooms bathroom bathrooms ensuite wardrobe lounge dining kitchen layout "
        "level suite master upstairs".split())),
    ("Parking, garden & section", frozenset(
        "parking garage garden deck fenced lawn section street".split())),
    ("School zones & catchments", frozenset(
        "school schools college intermediate grammar zoned zone catchment".split())),
)


def _topic_label_candidates(top_terms: Sequence[str]) -> list[str]:
    """Rank human labels for a topic from its top terms (keyword scoring, rank-weighted)."""
    scored: list[tuple[float, int, str]] = []
    for order, (label, keywords) in enumerate(_TOPIC_RULES):
        score = 0.0
        for rank, term in enumerate(top_terms):
            if set(term.split()) & keywords:
                score += 1.0 / (rank + 1)
        if score > 0:
            scored.append((score, order, label))
    scored.sort(key=lambda item: (-item[0], item[1]))
    candidates = [label for _, _, label in scored]
    if not candidates:
        fallback = [t for t in top_terms[:2] if t]
        candidates = [" & ".join(w.title() for w in fallback) if fallback else "General description"]
    return candidates


def _unique_labels(candidate_lists: Sequence[Sequence[str]]) -> dict[int, str]:
    """Assign each topic the best label not already used; suffix duplicates if necessary."""
    used: set[str] = set()
    result: dict[int, str] = {}
    for topic_id, candidates in enumerate(candidate_lists):
        chosen = None
        for candidate in candidates:
            if candidate not in used:
                chosen = candidate
                break
        if chosen is None:
            chosen = f"{candidates[0]} II"
        # Deterministic disambiguation if the fallback is also taken.
        suffix = 2
        while chosen in used:
            chosen = f"{candidates[0]} {suffix}"
            suffix += 1
        used.add(chosen)
        result[topic_id] = chosen
    return result


def fit_topic_model(
    texts: Sequence[str],
    *,
    n_topics: int = N_TOPICS,
    seed: int = RANDOM_SEED,
    min_df: int = MIN_DF,
    max_df: float = MAX_DF,
    max_features: int = MAX_FEATURES,
) -> dict[str, Any]:
    """Fit TF-IDF + NMF topics and return weights, top terms and labels.

    NMF is fitted only on near-duplicate-filtered documents, then all documents are transformed.
    Row weights are normalised to sum to 1 so they read as within-listing topic shares.
    """
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=min_df,
        max_df=max_df,
        sublinear_tf=True,
        tokenizer=tokenize,
        token_pattern=None,
        max_features=max_features,
        dtype=np.float64,
    )
    tfidf = vectorizer.fit_transform(texts)
    if tfidf.shape[1] < n_topics:
        raise ValueError(f"Not enough TF-IDF features ({tfidf.shape[1]}) for {n_topics} topics")
    fit_idx = _independent_documents(tfidf)
    if len(fit_idx) < n_topics:
        raise ValueError("Not enough distinct documents to fit topics")

    nmf = NMF(
        n_components=n_topics,
        init="nndsvda",
        random_state=seed,
        max_iter=800,
        beta_loss="frobenius",
    )
    nmf.fit(tfidf[fit_idx])
    weights = nmf.transform(tfidf)
    row_sums = weights.sum(axis=1, keepdims=True)
    empty = row_sums.ravel() == 0
    row_sums[empty, 0] = 1.0
    weights = weights / row_sums
    if empty.any():
        weights[empty] = 1.0 / n_topics

    feature_names = np.asarray(vectorizer.get_feature_names_out())
    components = nmf.components_
    topic_terms: list[list[str]] = []
    candidates: list[list[str]] = []
    for topic_id in range(n_topics):
        order = np.argsort(components[topic_id])[::-1][:TOP_TERMS_PER_TOPIC]
        terms = [str(feature_names[i]) for i in order]
        topic_terms.append(terms)
        candidates.append(_topic_label_candidates(terms))
    labels = _unique_labels(candidates)

    return {
        "vectorizer": vectorizer,
        "nmf": nmf,
        "weights": weights,
        "top_terms": topic_terms,
        "labels": labels,
        "fit_documents": len(fit_idx),
        "n_features": int(tfidf.shape[1]),
    }


# ---------------------------------------------------------------------------------------------
# Structural design matrix
# ---------------------------------------------------------------------------------------------

TENURE_CONTROL_MAP = {
    "freehold": "freehold",
    "crosslease": "crosslease",
    "leasehold": "leasehold",
    "unit title": "other",
    "unknown": "unknown",
    None: "unknown",
    "": "unknown",
}


def build_structural_design(df: pd.DataFrame) -> pd.DataFrame:
    """Build the structural control matrix used by every model in this module.

    Controls: suburb, property type, bedrooms, bathrooms, land area, floor area, days on market,
    tenure and sale method. Log areas are imputed within property type and carry missing
    indicators so the imputation does not hide systematic missingness (apartments often have no
    land area; sections often have no floor area).
    """
    out = pd.DataFrame(index=df.index)
    out["bedrooms"] = pd.to_numeric(df["bedrooms"], errors="coerce")
    out["bathrooms"] = pd.to_numeric(df["bathrooms"], errors="coerce")
    beds_missing = out["bedrooms"].isna().astype(float)
    baths_missing = out["bathrooms"].isna().astype(float)
    out["bedrooms"] = out["bedrooms"].fillna(out["bedrooms"].median())
    out["bathrooms"] = out["bathrooms"].fillna(out["bathrooms"].median())

    land = pd.to_numeric(df["land_area"], errors="coerce")
    floor = pd.to_numeric(df["floor_area"], errors="coerce")
    log_land = np.log1p(land.clip(lower=0))
    log_floor = np.log1p(floor.clip(lower=0))
    type_series = df["property_type"].fillna("Unknown").astype(str)
    out["log_land_area"] = log_land.groupby(type_series).transform("median")
    out["log_land_area"] = out["log_land_area"].fillna(log_land.median())
    out["log_floor_area"] = log_floor.groupby(type_series).transform("median")
    out["log_floor_area"] = out["log_floor_area"].fillna(log_floor.median())
    out["land_area_missing"] = log_land.isna().astype(float)
    out["floor_area_missing"] = log_floor.isna().astype(float)

    dom = pd.to_numeric(df["days_on_market"], errors="coerce").fillna(0).clip(lower=0)
    out["log_days_on_market"] = np.log1p(dom)
    out["bedrooms_missing"] = beds_missing
    out["bathrooms_missing"] = baths_missing

    tenure = df["tenure"].map(lambda v: TENURE_CONTROL_MAP.get(v, "unknown"))
    categoricals = {
        "suburb": df["suburb_slug"].fillna("unknown").astype(str),
        "property_type": type_series,
        "tenure": tenure.astype(str),
        "sale_method": df["sale_method"].fillna("unknown").astype(str),
    }
    for name, series in categoricals.items():
        categories = sorted(series.unique())
        for category in categories[1:]:  # first (sorted) category is the reference level
            out[f"{name}={category}"] = (series == category).astype(float)
    return out.astype(float)


def build_text_design(
    topics: np.ndarray,
    lexicon: pd.DataFrame,
    *,
    topic_columns: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Text feature matrix for the predictive / description-residual models."""
    topics_frame = pd.DataFrame(
        topics,
        columns=topic_columns
        or [f"topic_{i:02d}" for i in range(topics.shape[1])],
        index=lexicon.index,
    )
    lex_columns = list(_LEXICON_COLUMNS)
    out = pd.concat([topics_frame, lexicon[lex_columns].astype(float)], axis=1)
    out["log_word_count"] = np.log1p(lexicon["word_count"].clip(lower=0).astype(float))
    out["exclamations"] = lexicon["exclamations"].astype(float)
    out["readability"] = lexicon["readability"].astype(float)
    return out.astype(float)


# ---------------------------------------------------------------------------------------------
# Association tests
# ---------------------------------------------------------------------------------------------

def _bh_fdr(pvalues: Sequence[float]) -> np.ndarray:
    """Benjamini-Hochberg FDR q-values (NaN-safe)."""
    pvalues = np.asarray(pvalues, dtype=float)
    result = np.full_like(pvalues, np.nan)
    mask = ~np.isnan(pvalues)
    if mask.any():
        _, qvals, _, _ = multipletests(pvalues[mask], method="fdr_bh")
        result[mask] = qvals
    return result


def run_association(
    *,
    name: str,
    dependent_label: str,
    y: pd.Series,
    structural: pd.DataFrame,
    text_features: pd.DataFrame,
    text_meta: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """OLS with suburb/type/size/DOM/tenure/method controls, HC3 robust SE and BH FDR.

    ``text_meta`` maps text column names to metadata (kind/label/topic_id). Returns a
    JSON-serialisable dict with the coefficient table.
    """
    mask = y.notna().reindex(structural.index, fill_value=False)
    y_sub = y.astype(float).reindex(structural.index)[mask]
    X = pd.concat([structural[mask], text_features[mask]], axis=1).astype(float)
    X = sm.add_constant(X, has_constant="add")
    model = sm.OLS(y_sub, X).fit(cov_type="HC3")

    # Joint test that all text coefficients are zero (HC3 robust Wald), plus the incremental R²
    # of the text block over structural controls only. Individual coefficients can fail FDR while
    # the block as a whole adds explanatory power; both are reported.
    control_only = sm.OLS(
        y_sub, sm.add_constant(structural[mask].astype(float), has_constant="add")
    ).fit(cov_type="HC3")
    parameter_names = list(model.params.index)
    restrictions = np.zeros((text_features.shape[1], len(parameter_names)))
    for row, column in enumerate(text_features.columns):
        restrictions[row, parameter_names.index(column)] = 1.0
    try:
        joint = model.wald_test(restrictions, use_f=True, scalar=True)
        joint_record = {
            "statistic": round(float(joint.statistic), 4),
            "p": round(float(joint.pvalue), 6),
            "df_num": int(text_features.shape[1]),
            "df_denom": int(model.df_resid),
        }
    except Exception as exc:  # pragma: no cover - defensive
        joint_record = {"error": str(exc)}
    joint_record.update(
        {
            "r2_structural_only": round(float(control_only.rsquared), 4),
            "r2_with_text": round(float(model.rsquared), 4),
            "delta_r2": round(float(model.rsquared - control_only.rsquared), 4),
            "delta_adj_r2": round(
                float(model.rsquared_adj - control_only.rsquared_adj), 4
            ),
        }
    )

    feature_records: list[dict[str, Any]] = []
    pvals: list[float] = []
    for column in text_features.columns:
        meta = dict(text_meta.get(column, {}))
        p = float(model.pvalues.get(column, float("nan")))
        pvals.append(p)
        feature_records.append(
            {
                "feature": column,
                "kind": meta.get("kind", "lexicon"),
                "topic_id": meta.get("topic_id"),
                "label": meta.get("label", column),
                "coef": round(float(model.params.get(column, float("nan"))), 6),
                "se": round(float(model.bse.get(column, float("nan"))), 6),
                "t": round(float(model.tvalues.get(column, float("nan"))), 4),
                "p": round(p, 6),
            }
        )
    qvals = _bh_fdr(pvals)
    for record, q in zip(feature_records, qvals):
        record["q"] = round(float(q), 6) if not math.isnan(float(q)) else None
        record["significant_fdr_05"] = bool(q < 0.05) if not math.isnan(float(q)) else False
        record["significant_fdr_10"] = bool(q < 0.10) if not math.isnan(float(q)) else False

    significant = [
        r for r in feature_records
        if r["significant_fdr_05"]
    ]
    significant_sorted = sorted(
        significant, key=lambda r: abs(r["coef"]), reverse=True
    )
    return {
        "name": name,
        "dependent": dependent_label,
        "n": int(len(y_sub)),
        "r2": round(float(model.rsquared), 4),
        "adj_r2": round(float(model.rsquared_adj), 4),
        "fdr": "Benjamini-Hochberg across the %d text features" % len(feature_records),
        "n_significant_fdr_05": len(significant),
        "n_significant_fdr_10": sum(1 for r in feature_records if r["significant_fdr_10"]),
        "significant": significant_sorted,
        "features": feature_records,
        "joint_text_test": joint_record,
        "controls": [c for c in structural.columns],
    }


# ---------------------------------------------------------------------------------------------
# Predictive tests
# ---------------------------------------------------------------------------------------------

def _cv_predictions(X: pd.DataFrame, y: pd.Series, seed: int = RANDOM_SEED) -> np.ndarray:
    """5-fold out-of-fold predictions from standardised Ridge."""
    pipeline = make_pipeline(StandardScaler(), Ridge(alpha=RIDGE_ALPHA))
    kfold = KFold(n_splits=N_SPLITS, shuffle=True, random_state=seed)
    return cross_val_predict(pipeline, X.to_numpy(dtype=float), y.to_numpy(dtype=float), cv=kfold)


def _fit_ridge(X: pd.DataFrame, y: pd.Series) -> Any:
    pipeline = make_pipeline(StandardScaler(), Ridge(alpha=RIDGE_ALPHA))
    pipeline.fit(X.to_numpy(dtype=float), y.to_numpy(dtype=float))
    return pipeline


def _dollar_metrics(y_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    y = np.exp(y_log)
    pred = np.exp(pred_log)
    return {
        "r2_log": round(float(r2_score(y_log, pred_log)), 4),
        "r2_dollar": round(float(r2_score(y, pred)), 4),
        "mae_dollar": round(float(mean_absolute_error(y, pred)), 1),
        "mape_pct": round(float(mean_absolute_percentage_error(y, pred) * 100.0), 3),
    }


def incremental_model_test(
    df: pd.DataFrame,
    structural: pd.DataFrame,
    text_features: pd.DataFrame,
) -> dict[str, Any]:
    """5-fold Ridge on Homes-AVM listings: structural only vs structural + text.

    Target is ``log(value_mid)`` where the value is the Homes AVM. Dollar metrics invert the log
    prediction. This is exploratory: it measures whether description language adds predictive
    information for AVM-valued listings, not a causal effect.
    """
    mask = df["value_source"].eq("homes_avm") & df["value_mid"].notna()
    y_log = np.log(df.loc[mask, "value_mid"].astype(float))
    X_struct = structural[mask]
    X_text = pd.concat([structural[mask], text_features[mask]], axis=1)

    pred_struct = _cv_predictions(X_struct, y_log)
    pred_text = _cv_predictions(X_text, y_log)
    base = _dollar_metrics(y_log.to_numpy(), pred_struct)
    with_text = _dollar_metrics(y_log.to_numpy(), pred_text)
    return {
        "n": int(mask.sum()),
        "folds": N_SPLITS,
        "alpha": RIDGE_ALPHA,
        "target": "log(value_mid) for Homes AVM listings",
        "structural": base,
        "structural_plus_text": with_text,
        "delta": {
            "r2_log": round(with_text["r2_log"] - base["r2_log"], 4),
            "r2_dollar": round(with_text["r2_dollar"] - base["r2_dollar"], 4),
            "mae_dollar": round(with_text["mae_dollar"] - base["mae_dollar"], 1),
            "mape_pct": round(with_text["mape_pct"] - base["mape_pct"], 3),
        },
    }


def description_index(
    df: pd.DataFrame,
    structural: pd.DataFrame,
    text_features: pd.DataFrame,
) -> dict[str, Any]:
    """Cross-fitted text premium/discount signal after removing structural expectations.

    Step 1: an out-of-fold structural Ridge predicts log(AVM value); the residual is the part of
    price the structural controls do not explain. The residual target is winsorised at the
    2.5/97.5 percentiles before fitting, because a handful of ultra-luxury listings would
    otherwise dominate the text model.

    Step 2: an out-of-fold text Ridge predicts that structural residual from the description
    features. The fitted text model is applied to every listing and the predictions are
    standardised across the 998-listing corpus:

    ``description_index``: z-score of the text-implied premium (0 = typical description language
    in the corpus, +1 = one standard deviation more premium language). Clipped to +/-3.
    ``description_premium_pct``: the same signal as a percent premium/discount, derived from the
    clipped index.

    "Neutral" means the description language is typical for this corpus; it is a relative
    marketing-language signal, not a valuation. Values are exploratory and should be read as a
    ranking signal, not a literal price adjustment.
    """
    mask = df["value_source"].eq("homes_avm") & df["value_mid"].notna()
    y_log = np.log(df.loc[mask, "value_mid"].astype(float))
    X_struct = structural[mask]
    X_text = text_features[mask]

    structural_oof = _cv_predictions(X_struct, y_log)
    residual = y_log.to_numpy() - structural_oof
    winsor_lo, winsor_hi = np.quantile(residual, [0.025, 0.975])
    target = np.clip(residual, winsor_lo, winsor_hi)

    kfold = KFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_SEED)
    text_pipeline = make_pipeline(StandardScaler(), Ridge(alpha=RIDGE_ALPHA))
    text_oof = cross_val_predict(
        text_pipeline, X_text.to_numpy(dtype=float), target, cv=kfold
    )

    # Fit on the full AVM sample and apply to every listing.
    final_text_model = _fit_ridge(X_text, pd.Series(target, index=X_text.index))
    predicted_log_premium = final_text_model.predict(text_features.to_numpy(dtype=float))

    corpus_mean = float(np.mean(predicted_log_premium))
    corpus_sd = float(np.std(predicted_log_premium))
    if not np.isfinite(corpus_sd) or corpus_sd <= 0:
        corpus_sd = 1e-9
    centred = predicted_log_premium - corpus_mean
    raw_index = centred / corpus_sd
    index = np.clip(raw_index, -DESCRIPTION_INDEX_CLIP_Z, DESCRIPTION_INDEX_CLIP_Z)
    premium_pct = 100.0 * (np.exp(index * corpus_sd) - 1.0)

    top_text_features = []
    ridge = final_text_model.named_steps["ridge"]
    scaler = final_text_model.named_steps["standardscaler"]
    coefficients = ridge.coef_ / np.where(scaler.scale_ == 0, 1.0, scaler.scale_)
    for column, coef in sorted(
        zip(text_features.columns, coefficients), key=lambda item: -abs(item[1])
    )[:10]:
        top_text_features.append(
            {"feature": column, "log_points_per_unit": round(float(coef), 6)}
        )

    def example(pos: int) -> dict[str, Any]:
        row = df.iloc[pos]
        return {
            "listing_id": int(row["id"]),
            "suburb": row.get("suburb_name") or row.get("suburb_slug"),
            "property_type": row.get("property_type"),
            "value_mid": None if pd.isna(row.get("value_mid")) else int(row["value_mid"]),
            "description_index": round(float(index[pos]), 3),
            "description_premium_pct": round(float(premium_pct[pos]), 2),
            "snippet": _snippet(_cleaned_cache.get(int(row["id"]), ""), 22),
        }

    order = np.argsort(raw_index)
    return {
        "n_calibration": int(mask.sum()),
        "index": index,
        "premium_pct": premium_pct,
        "top_text_features": top_text_features,
        "most_positive": [example(int(i)) for i in order[-3:][::-1]],
        "most_negative": [example(int(i)) for i in order[:3]],
        "stats": {
            "corpus_mean_log_premium": round(corpus_mean, 6),
            "corpus_sd_log_premium": round(corpus_sd, 6),
            "winsorise_residual_pct": 2.5,
            "clip_z": DESCRIPTION_INDEX_CLIP_Z,
            "share_clipped": round(float((np.abs(raw_index) > DESCRIPTION_INDEX_CLIP_Z).mean()), 4),
            "mean_index_corpus": round(float(np.mean(index)), 4),
            "sd_index_corpus": round(float(np.std(index)), 4),
            "premium_pct_p10": round(float(np.percentile(premium_pct, 10)), 2),
            "premium_pct_p90": round(float(np.percentile(premium_pct, 90)), 2),
            "premium_pct_sd": round(float(np.std(premium_pct)), 2),
            "text_model_oof_sd_log": round(float(np.std(text_oof)), 4),
        },
    }


# ---------------------------------------------------------------------------------------------
# Price-change test
# ---------------------------------------------------------------------------------------------

def _estimate_trends(conn: sqlite3.Connection) -> pd.DataFrame:
    """Per-listing Homes AVM trend over the last up-to-8 weekly observations."""
    history = pd.read_sql_query(
        "SELECT listing_id, date, estimate_mid FROM estimate_history "
        "WHERE estimate_mid IS NOT NULL AND estimate_mid > 0 ORDER BY listing_id, date",
        conn,
    )
    if history.empty:
        return pd.DataFrame(columns=["listing_id", "trend_8w_log_per_week", "change_pct", "n_points"])
    records = []
    for listing_id, group in history.groupby("listing_id", sort=True):
        values = group["estimate_mid"].to_numpy(dtype=float)
        if len(values) < 6:
            continue
        tail = values[-8:]
        x = np.arange(len(tail), dtype=float)
        slope = float(np.polyfit(x, np.log(tail), 1)[0])
        records.append(
            {
                "listing_id": int(listing_id),
                "trend_8w_log_per_week": slope,
                "change_pct": float((tail[-1] / tail[0] - 1.0) * 100.0),
                "n_points": int(len(tail)),
                "start_estimate": int(tail[0]),
                "end_estimate": int(tail[-1]),
            }
        )
    return pd.DataFrame(records)


def _snapshot_summary(conn: sqlite3.Connection) -> dict[str, Any]:
    try:
        frame = pd.read_sql_query(
            "SELECT listing_id, COUNT(*) AS n, COUNT(DISTINCT value_mid) AS distinct_values "
            "FROM listing_snapshots GROUP BY listing_id",
            conn,
        )
    except Exception:  # pragma: no cover - schema is expected to be present
        return {"available": False}
    if frame.empty:
        return {"available": False}
    return {
        "available": True,
        "listings_with_snapshots": int(len(frame)),
        "listings_with_multiple_snapshots": int((frame["n"] > 1).sum()),
        "listings_with_changing_value": int((frame["distinct_values"] > 1).sum()),
        "max_snapshots": int(frame["n"].max()),
        "note": (
            "Snapshot history is too thin (mostly one capture per listing) to measure price "
            "changes; the AVM estimate history is used instead."
        ),
    }


def price_change_test(
    conn: sqlite3.Connection,
    df: pd.DataFrame,
    structural: pd.DataFrame,
    text_features: pd.DataFrame,
    text_meta: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Exploratory test: do text features track the 8-week Homes AVM revision trend?

    The dependent variable is the per-week slope of log(Homes AVM midpoint) over the last eight
    weekly estimate points (listings with at least six observations), expressed in percent per
    week. Controls are the same as the other association models. Limitations are severe: this is
    the AVM's own revision history, not transaction prices; Homes updates estimates for many
    listings at once, so idiosyncratic variance is small and the test is underpowered.
    """
    trends = _estimate_trends(conn)
    mask = df["id"].isin(trends["listing_id"])
    merged = df.loc[mask].copy()
    merged = merged.merge(trends, left_on="id", right_on="listing_id", how="left")
    y = (merged["trend_8w_log_per_week"] * 100.0).rename("pct_per_week")
    structural_sub = structural.loc[merged.index]
    text_sub = text_features.loc[merged.index]
    result = run_association(
        name="estimate_history_trend_8w",
        dependent_label="Homes AVM 8-week trend (% per week)",
        y=y,
        structural=structural_sub,
        text_features=text_sub,
        text_meta=text_meta,
    )
    result["n_listings_with_history"] = int(trends.shape[0])
    result["mean_abs_change_8w_pct"] = round(
        float(trends["change_pct"].abs().mean()), 3
    )
    result["share_changed_gt_half_pct"] = round(
        float((trends["change_pct"].abs() > 0.5).mean()), 3
    )
    result["snapshots"] = _snapshot_summary(conn)
    result["limitations"] = (
        "AVM revision history, not transaction prices. 8 weekly points at most. Homes AVM "
        "revisions are largely market-wide, and the text model observes marketing language at "
        "one point in time, so this test detects association at best; it is not a causal or "
        "predictive price-change model. Daily snapshots would be required to study true asking-"
        "price changes."
    )
    return result


# ---------------------------------------------------------------------------------------------
# Database storage
# ---------------------------------------------------------------------------------------------

DDL = """
CREATE TABLE IF NOT EXISTS text_topics (
    topic_id INTEGER PRIMARY KEY,
    label TEXT NOT NULL,
    top_terms TEXT NOT NULL,
    mean_weight REAL,
    max_weight REAL,
    n_listings INTEGER,
    model_version TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS listing_topics (
    listing_id INTEGER NOT NULL,
    topic_id INTEGER NOT NULL,
    weight REAL NOT NULL,
    PRIMARY KEY (listing_id, topic_id)
);
CREATE INDEX IF NOT EXISTS idx_listing_topics_topic ON listing_topics(topic_id);

CREATE TABLE IF NOT EXISTS text_features (
    listing_id INTEGER PRIMARY KEY,
    word_count INTEGER NOT NULL,
    exclamations INTEGER NOT NULL,
    urgency REAL NOT NULL,
    luxury REAL NOT NULL,
    condition_renovation REAL NOT NULL,
    views_waterfront REAL NOT NULL,
    family_school REAL NOT NULL,
    investment REAL NOT NULL,
    risk REAL NOT NULL,
    readability REAL NOT NULL,
    description_premium_pct REAL,
    description_index REAL,
    lexicon_hits_json TEXT,
    model_version TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_text_features_index ON text_features(description_index);

CREATE TABLE IF NOT EXISTS text_metrics (
    name TEXT PRIMARY KEY,
    value REAL,
    detail_json TEXT,
    updated_at TEXT NOT NULL
);
"""


def _store(
    conn: sqlite3.Connection,
    *,
    listings: pd.DataFrame,
    topics: dict[str, Any],
    lexicon: pd.DataFrame,
    index_result: dict[str, Any],
    association_premium: dict[str, Any],
    association_ask_gap: dict[str, Any],
    model_comparison: dict[str, Any],
    price_change: dict[str, Any],
    summary: dict[str, Any],
    now: str,
) -> None:
    """Replace the four text-analysis tables inside ``conn`` (idempotent)."""
    conn.executescript(DDL)
    n_listings = len(listings)
    weights = topics["weights"]
    n_topics = weights.shape[1]

    conn.execute("DELETE FROM text_topics")
    conn.execute("DELETE FROM listing_topics")
    conn.execute("DELETE FROM text_features")
    conn.execute("DELETE FROM text_metrics")

    topic_rows = []
    for topic_id in range(n_topics):
        topic_weights = weights[:, topic_id]
        topic_rows.append(
            (
                topic_id,
                topics["labels"][topic_id],
                json.dumps(topics["top_terms"][topic_id], ensure_ascii=False),
                round(float(topic_weights.mean()), 6),
                round(float(topic_weights.max()), 6),
                int((topic_weights > 0.10).sum()),
                MODEL_VERSION,
                now,
            )
        )
    conn.executemany(
        "INSERT INTO text_topics (topic_id, label, top_terms, mean_weight, max_weight, "
        "n_listings, model_version, updated_at) VALUES (?,?,?,?,?,?,?,?)",
        topic_rows,
    )

    listing_topic_rows = [
        (int(listing_id), int(topic_id), round(float(weights[row, topic_id]), 6))
        for row, listing_id in enumerate(listings["id"].astype(int))
        for topic_id in range(n_topics)
    ]
    conn.executemany(
        "INSERT INTO listing_topics (listing_id, topic_id, weight) VALUES (?,?,?)",
        listing_topic_rows,
    )

    feature_rows = []
    for row, listing_id in enumerate(listings["id"].astype(int)):
        feature_rows.append(
            (
                int(listing_id),
                int(lexicon.iloc[row]["word_count"]),
                int(lexicon.iloc[row]["exclamations"]),
                round(float(lexicon.iloc[row]["urgency"]), 4),
                round(float(lexicon.iloc[row]["luxury"]), 4),
                round(float(lexicon.iloc[row]["condition_renovation"]), 4),
                round(float(lexicon.iloc[row]["views_waterfront"]), 4),
                round(float(lexicon.iloc[row]["family_school"]), 4),
                round(float(lexicon.iloc[row]["investment"]), 4),
                round(float(lexicon.iloc[row]["risk"]), 4),
                round(float(lexicon.iloc[row]["readability"]), 4),
                round(float(index_result["premium_pct"][row]), 4),
                round(float(index_result["index"][row]), 6),
                str(lexicon.iloc[row]["lexicon_hits_json"]),
                MODEL_VERSION,
                now,
            )
        )
    conn.executemany(
        "INSERT INTO text_features (listing_id, word_count, exclamations, urgency, luxury, "
        "condition_renovation, views_waterfront, family_school, investment, risk, readability, "
        "description_premium_pct, description_index, lexicon_hits_json, model_version, "
        "updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        feature_rows,
    )

    metrics: list[tuple[str, float | None, str, str]] = []

    def metric(name: str, value: float | None, detail: Any) -> None:
        metrics.append(
            (name, None if value is None else round(float(value), 6),
             json.dumps(detail, ensure_ascii=False, default=str), now)
        )

    metric("text_model_version", None, {"model_version": MODEL_VERSION,
                                        "n_listings": n_listings,
                                        "n_topics": n_topics,
                                        "generated_at": now})
    metric("n_listings", float(n_listings), {"n_listings": n_listings})
    metric("n_topics", float(n_topics), {"n_topics": n_topics})
    metric("vocabulary_size", float(topics["n_features"]),
           {"vocabulary_size": topics["n_features"],
            "fit_documents": topics["fit_documents"]})
    metric("cleaning", None, summary["cleaning"])
    metric("topics", None, summary["topics"])
    metric("lexicons", None, summary["lexicons"])
    metric("association_value_cv_ratio", float(association_premium["n_significant_fdr_05"]),
           association_premium)
    metric("association_ask_gap", float(association_ask_gap["n_significant_fdr_05"]),
           association_ask_gap)
    for feature in association_premium["features"]:
        metric(
            f"assoc:value_cv_ratio:{feature['feature']}",
            feature["coef"],
            {"p": feature["p"], "q": feature["q"],
             "significant_fdr_05": feature["significant_fdr_05"],
             "n": association_premium["n"]},
        )
    for feature in association_ask_gap["features"]:
        metric(
            f"assoc:ask_gap:{feature['feature']}",
            feature["coef"],
            {"p": feature["p"], "q": feature["q"],
             "significant_fdr_05": feature["significant_fdr_05"],
             "n": association_ask_gap["n"]},
        )
    metric("incremental_model", float(model_comparison["delta"]["r2_log"]), model_comparison)
    metric("price_change_test", float(price_change["n_significant_fdr_05"]), price_change)
    metric("description_index", float(index_result["stats"]["premium_pct_sd"]),
           index_result["stats"])
    metric("description_examples", None, {
        "most_positive": index_result["most_positive"],
        "most_negative": index_result["most_negative"],
        "top_text_features": index_result["top_text_features"],
    })

    conn.executemany(
        "INSERT INTO text_metrics (name, value, detail_json, updated_at) VALUES (?,?,?,?)",
        metrics,
    )
    conn.commit()


# ---------------------------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------------------------

_cleaned_cache: dict[int, str] = {}  # used only for example snippets in the returned summary


def _snippet(text: str, n_words: int = 22) -> str:
    words = (text or "").split()
    suffix = " ..." if len(words) > n_words else ""
    return " ".join(words[:n_words]) + suffix


def load_listings(conn: sqlite3.Connection) -> pd.DataFrame:
    """Load the standard, active listings used for text analysis, ordered by id."""
    query = """
        SELECT id, suburb_slug, suburb_name, property_type, bedrooms, bathrooms, land_area,
               floor_area, tenure, sale_method, days_on_market, asking_price, ask_gap,
               value_mid, value_low, value_high, value_source, value_confidence,
               estimate_mid, cv, title, address, body
        FROM listings
        WHERE is_standard = 1 AND status IN ('active', 'delisted')
        ORDER BY id
    """
    frame = pd.read_sql_query(query, conn)
    if "body" not in frame.columns:
        frame["body"] = ""
    frame["body"] = frame["body"].fillna("")
    frame = frame[frame["body"].str.strip().str.len() >= MIN_DESCRIPTION_CHARS].copy()
    # Text/topic matrices use positional indices; reset after filtering out empty bodies.
    return frame.reset_index(drop=True)


def _topic_meta(labels: Mapping[int, str], n_topics: int) -> dict[str, dict[str, Any]]:
    """Column metadata for topic feature columns."""
    return {
        f"topic_{i:02d}": {"kind": "topic", "topic_id": i, "label": labels[i]}
        for i in range(n_topics)
    }


def run(conn: sqlite3.Connection, *, n_topics: int = N_TOPICS) -> dict[str, Any]:
    """Run the full text/topic pipeline against an open SQLite connection.

    Reads standard active listings, fits the topic model, computes lexicon and description
    signals, runs the association / incremental / price-change analyses, and replaces the four
    text tables in the database. Returns a JSON-serialisable summary dict.

    The function does not modify any pre-existing table. Runtime is a few seconds on ~1,000
    listings.
    """
    global _cleaned_cache
    started = datetime.now(timezone.utc)
    now = started.isoformat()

    listings = load_listings(conn)
    if len(listings) < MIN_LISTINGS:
        raise ValueError(
            f"Need at least {MIN_LISTINGS} standard active listings with bodies, "
            f"found {len(listings)}"
        )
    bodies = listings["body"].astype(str).tolist()
    cleaned, cleaning_stats = clean_corpus(bodies)
    _cleaned_cache = {int(listing_id): text for listing_id, text in zip(listings["id"], cleaned)}

    # Redact suburb names so topics describe property attributes, not location branding.
    suburb_names = set(TARGET_SUBURB_NAMES)
    try:
        db_suburbs = [
            str(row[0]) for row in conn.execute("SELECT name FROM suburbs")
            if row and row[0]
        ]
        suburb_names.update(db_suburbs)
    except sqlite3.Error:
        pass
    pattern = _suburb_pattern(suburb_names)
    model_texts = [pattern.sub(" suburb ", text) for text in cleaned]
    cleaning_stats["suburb_names_redacted"] = len(suburb_names)

    n_topics = int(min(n_topics, max(4, len(listings) // 12)))
    topics = fit_topic_model(model_texts, n_topics=n_topics)
    weights = topics["weights"]
    labels = topics["labels"]

    lexicon = build_lexicon_frame(cleaned, bodies)
    structural = build_structural_design(listings)
    text_features_full = build_text_design(weights, lexicon)
    topic_meta = _topic_meta(labels, n_topics)

    # --- association A: homes AVM premium over council CV --------------------------------
    premium_mask = (
        listings["value_source"].eq("homes_avm")
        & listings["value_mid"].notna()
        & listings["cv"].notna()
        & (listings["cv"] > 0)
    )
    premium_y = pd.Series(
        np.log(
            listings.loc[premium_mask, "value_mid"].astype(float)
            / listings.loc[premium_mask, "cv"].astype(float)
        ),
        index=listings.index[premium_mask],
    )
    reference_topic = int(np.argmax(weights.mean(axis=0)))
    association_columns = [
        f"topic_{i:02d}" for i in range(n_topics) if i != reference_topic
    ] + list(_LEXICON_COLUMNS)
    association_text = text_features_full[association_columns]
    association_meta = {c: topic_meta[c] for c in association_columns if c in topic_meta}
    for column in _LEXICON_COLUMNS:
        association_meta[column] = {"kind": "lexicon", "label": column}

    association_premium = run_association(
        name="value_cv_ratio",
        dependent_label="log(value_mid / cv)",
        y=premium_y,
        structural=structural,
        text_features=association_text,
        text_meta=association_meta,
    )
    association_premium["reference_topic"] = {
        "topic_id": reference_topic,
        "label": labels[reference_topic],
    }
    association_premium["note"] = (
        "Only Homes AVM listings with a council CV are used (the comp-model CV ratio is "
        "mechanically CV-normalised). Coefficients are topic/lexicon effects relative to the "
        f"reference topic '{labels[reference_topic]}' and the omitted structural baselines."
    )

    # --- association B: advertised-price gap -------------------------------------------
    ask_mask = listings["ask_gap"].notna()
    association_ask_gap = run_association(
        name="ask_gap",
        dependent_label="ask_gap = (asking - value_mid) / value_mid",
        y=listings.loc[ask_mask, "ask_gap"].astype(float),
        structural=structural,
        text_features=association_text,
        text_meta=association_meta,
    )
    association_ask_gap["reference_topic"] = {
        "topic_id": reference_topic,
        "label": labels[reference_topic],
    }
    association_ask_gap["note"] = (
        "Only listings with a reliable advertised price and a high/medium-confidence value "
        "signal have ask_gap (selection). Auction/tender/negotiation listings are absent, so "
        "this is a biased sample and coefficients are descriptive, not causal."
    )

    # --- incremental predictive test ----------------------------------------------------
    model_comparison = incremental_model_test(listings, structural, text_features_full)

    # --- description index --------------------------------------------------------------
    index_result = description_index(listings, structural, text_features_full)

    # --- price-change test --------------------------------------------------------------
    price_change = price_change_test(
        conn, listings, structural, association_text, association_meta
    )

    # --- topic prevalence / examples ----------------------------------------------------
    topic_summary = []
    for topic_id in range(n_topics):
        topic_weights = weights[:, topic_id]
        top_idx = np.argsort(topic_weights)[::-1][:3]
        topic_summary.append(
            {
                "topic_id": topic_id,
                "label": labels[topic_id],
                "top_terms": topics["top_terms"][topic_id],
                "mean_weight": round(float(topic_weights.mean()), 4),
                "share_docs_weight_gt_10pct": round(float((topic_weights > 0.10).mean()), 4),
                "examples": [
                    {
                        "listing_id": int(listings.iloc[int(i)]["id"]),
                        "suburb": listings.iloc[int(i)].get("suburb_name"),
                        "weight": round(float(topic_weights[int(i)]), 3),
                    }
                    for i in top_idx
                ],
            }
        )

    lexicon_summary = {
        column: {
            "mean": round(float(lexicon[column].mean()), 4),
            "p90": round(float(lexicon[column].quantile(0.9)), 4),
            "share_positive": round(float((lexicon[column] > 0).mean()), 4),
        }
        for column in _LEXICON_COLUMNS
    }
    lexicon_summary["word_count"] = {
        "mean": round(float(lexicon["word_count"].mean()), 1),
        "median": round(float(lexicon["word_count"].median()), 1),
        "p90": round(float(lexicon["word_count"].quantile(0.9)), 1),
    }

    summary = {
        "model_version": MODEL_VERSION,
        "generated_at": now,
        "runtime_seconds": round((datetime.now(timezone.utc) - started).total_seconds(), 2),
        "n_listings": int(len(listings)),
        "n_topics": n_topics,
        "cleaning": cleaning_stats,
        "topics": topic_summary,
        "lexicons": lexicon_summary,
        "associations": {
            "value_cv_ratio": association_premium,
            "ask_gap": association_ask_gap,
        },
        "incremental_model": model_comparison,
        "description_index": {
            **index_result["stats"],
            "most_positive": index_result["most_positive"],
            "most_negative": index_result["most_negative"],
            "top_text_features": index_result["top_text_features"],
        },
        "price_change_test": price_change,
    }

    _store(
        conn,
        listings=listings,
        topics=topics,
        lexicon=lexicon,
        index_result=index_result,
        association_premium=association_premium,
        association_ask_gap=association_ask_gap,
        model_comparison=model_comparison,
        price_change=price_change,
        summary=summary,
        now=now,
    )
    return summary


# ---------------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------------

DEFAULT_DB = Path(__file__).resolve().parents[1] / "data" / "auckland_property.db"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build description text/topic features")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite database path")
    parser.add_argument(
        "--topics", type=int, default=N_TOPICS, help="number of NMF topics (10-14 recommended)"
    )
    args = parser.parse_args(argv)
    if not args.db.exists():
        print(f"Database not found: {args.db}", file=sys.stderr)
        return 1
    conn = sqlite3.connect(args.db)
    try:
        summary = run(conn, n_topics=args.topics)
    finally:
        conn.close()
    print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
