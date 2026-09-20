"""
Settings for The Unofficial Guide.

Everything you're likely to change lives here, at the top, on purpose.
You'll edit THRESHOLD in Milestone 4 and the chunking numbers in Milestone 3.

Anything you set in your .env file wins over the defaults here.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")


# ─── The corpus you're working with ──────────────────────────────────────────
# Change this to switch corpora, or pass --corpus on the command line.
# Options are the folder names inside corpora/. See corpora/README.md.

CORPUS = os.getenv("AI201_CORPUS", "campus_life")
#this is the corpus i am going to use

# ─── Chunking (Milestone 3) ──────────────────────────────────────────────────
# These two numbers mean something different now than they did in the starter.
#
# campus_life documents run 300-554 characters each, so the starter's 800-
# character window never cut anything: 88 documents came out as 88 chunks.
# chunker.py::split_documents groups related documents together instead —
# one dorm, one course or one dining venue per chunk — so CHUNK_SIZE is a
# CEILING on a merged chunk rather than a length to cut at.
#
# 1400 is measured, not guessed. The 23 merged groups in campus_life run from
# 788 characters (dining_north_kitchen) to 1400 (housing_old_brewhouse); all 7
# dining and all 9 course groups are under 1070, and only housing reaches up
# here. A 1200 ceiling split five housing groups, one of them six characters
# over the line, which is an arbitrary place to cut a building in half.
#
# This is knowingly a little above what the embedder reads. all-MiniLM-L6-V2
# takes 256 tokens (~1,000-1,200 characters) and silently ignores the rest.
# Only the vector is truncated — Chroma stores and returns the whole chunk — so
# the cost is that the tail of the longest housing groups is retrievable but
# not matchable, and the two-line header in chunker.py::_header is what pays
# for it: the building name and "laundry, noise" sit in the first 80
# characters, inside the window, whatever falls off the end.
#
# That trade only works at this scale. Grouping a whole category instead —
# "all housing" is ~10,000 characters — would put roughly 88% of the corpus
# past the window with nothing in the pipeline reporting it.
CHUNK_SIZE = 1400       # ceiling on a merged chunk, in characters

# The ceiling used when a single document has to be cut up, rather than when
# several are merged. It is lower than CHUNK_SIZE on purpose: a merged chunk
# can afford to overshoot the embedding window because its header keeps the
# subject inside it, and a cut-up document has no such guarantee.
#
# Nothing in the provided corpora is inherently longer than this — city_guides
# has 98 markdown sections and the largest is 711 characters. What this really
# controls is how many neighbouring sections get packed into one chunk before
# the next one starts.
EMBED_LIMIT = 1100      # ceiling when splitting one long document

# Only applies where a single document is genuinely too long for one chunk —
# the city_guides corpus, whose guides run ~2,000 characters. Merged
# campus_life chunks are split at document boundaries instead, and repeat their
# header, so they never need character overlap.
CHUNK_OVERLAP = 150     # characters carried across a split inside one document


# ─── Retrieval (Milestone 4) ─────────────────────────────────────────────────

TOP_K = 5               # how many chunks to pull back per question

# The relevance gate. If the best chunk is further away than this, the system
# refuses to answer instead of handing the model thin material.
#
# LOWER IS BETTER: 0.3 is a close match, 0.9 is unrelated.
#
# 0.6 is a reasonable starting point, not a right answer. Milestone 4 has you
# measure your own two groups of distances and put the cutoff in the gap.
# Most corpora land somewhere between 0.45 and 0.75.
THRESHOLD = 0.6


# ─── Models ──────────────────────────────────────────────────────────────────
# Embeddings run on your own machine and cost no API quota.
# Only generation calls out to a service.

# This is the model Chroma bundles, and leaving it alone is the fast path: it
# downloads about 80 MB from Chroma's own CDN and needs nothing else installed.
#
# Setting it to any other name — unit 2's "try a second embedding model"
# stretch option — switches to loading that model from Hugging Face instead,
# which needs `pip install 'sentence-transformers>=3.4,<3.5'` first. store.py
# says so with a real error message rather than a stack trace if you forget.
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
MODEL = os.getenv("AI201_MODEL", "gemini-3.5-flash-lite")


# ─── Rate limiting and quota guards ──────────────────────────────────────────
# You should not need to touch these. They exist so that a runaway loop costs
# you a warning instead of your whole day's allowance.

REQUESTS_PER_MINUTE = 30       # outgoing calls the limiter will allow per minute
SESSION_REQUEST_BUDGET = 300   # stop and warn rather than draining the daily quota
MAX_RETRIES = 4                # on 429 / resource-exhausted, with backoff

CACHE_ENABLED = os.getenv("AI201_CACHE", "1") != "0"
CACHE_DIR = ROOT / ".cache"


# ─── Paths ───────────────────────────────────────────────────────────────────

CORPORA_DIR = ROOT / "corpora"
CHROMA_DIR = ROOT / "chroma_db"
RESULTS_DIR = ROOT / "results"


def corpus_path(name: str | None = None) -> Path:
    """Folder holding the documents for a corpus."""
    return CORPORA_DIR / (name or CORPUS) / "documents"


def collection_name(name: str | None = None, variant: str = "default") -> str:
    """
    Name of the vector-store collection for a corpus.

    `variant` lets you index the same corpus two different ways and query both
    without deleting anything — you'll want that in unit 2 when you compare
    chunking strategies.

    Chroma is fussy about collection names: 3 to 63 characters, starting and
    ending with a letter or digit, and nothing but letters, digits, underscores
    and hyphens in between. If you bring your own corpus and name the folder
    something Chroma won't accept, this cleans it up rather than failing.
    """
    import re

    raw = f"{name or CORPUS}__{variant}"
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "-", raw)
    cleaned = cleaned.strip("_-")          # must start and end alphanumeric
    if not cleaned or not cleaned[0].isalnum():
        cleaned = f"c{cleaned}"
    if not cleaned[-1].isalnum():
        cleaned = f"{cleaned}0"
    return cleaned[:63].rstrip("_-") or "collection"
