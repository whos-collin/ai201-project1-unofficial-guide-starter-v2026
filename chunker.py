"""
Stage 2 of the pipeline: splitting documents into chunks.

⚠️ THIS IS THE FILE YOU CHANGE IN MILESTONE 3.

`fallback_split` is the starter's original: fixed-size character windows with a
fixed overlap, paying no attention to where sentences or paragraphs end.

On `campus_life` it does nothing at all. Every document in that corpus is
between ~300 and 554 characters and `CHUNK_SIZE` was 800, so the loop runs once
per file and 88 documents come out as 88 chunks. Tuning the window down would
only cut 400-character posts in half, which is strictly worse than leaving them
whole. The problem in this corpus is not that documents are too long — it is
that a single answer is scattered across several files.

`split_documents` below therefore *groups* rather than splits. The filenames
encode the structure plainly:

    housing_fenwick_court.txt          course_cs_340.txt
    housing_fenwick_court_laundry.txt  course_cs_340_exams.txt
    housing_fenwick_court_noise.txt    course_cs_340_workload.txt

Three files, one building. `housing_fenwick_court.txt` gives the laundry prices
and `housing_fenwick_court_laundry.txt` gives the machine counts and the best
time to go — a question about doing laundry in Fenwick Court needs both, and as
separate chunks they compete for the same TOP_K slots as six other buildings.
Merging them turns one entity into one chunk.

Two things constrain how far that grouping can go, and both are why this stops
at the entity and not at the category ("all housing", "all dining"):

  1. `all-MiniLM-L6-v2` accepts 256 tokens, roughly 1,000-1,200 characters, and
     silently drops the rest. Only the *embedding* is truncated — Chroma still
     stores and returns the whole chunk — so overshooting costs recall on the
     tail, not the answer. A ~1,200-character entity chunk loses very little. A
     ~10,000-character "all housing" chunk would have most of its content
     unsearchable, with nothing in the pipeline saying so.

  2. TOP_K is 5. Roughly 10 category chunks would return half the corpus for
     every question, including the out-of-scope ones, and the two groups of
     distances Milestone 4 asks you to separate would stop separating.

`CHUNK_SIZE` is now the ceiling on a merged chunk rather than a blind cut
length, and `CHUNK_OVERLAP` applies only where a single document really is too
long for one chunk (the `city_guides` corpus, whose guides run ~2,000
characters under `##` headings).
"""

import re
from dataclasses import dataclass

import config
from ingest import Document


@dataclass
class Chunk:
    """One piece of one document."""

    text: str
    source: str        # which file it came from
    index: int         # which chunk within that file, starting at 0
    produced_by: str   # the function that made it — cite this in your README

    @property
    def label(self) -> str:
        return f"{self.source}#{self.index}"


def fallback_split(
    documents: list[Document],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """
    The starter's original chunker. Fixed-size character windows with overlap.

    Keep this function. Milestone 3's stop rule points back at it, and having
    something to compare your own strategy against is useful in unit 2.
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP

    if overlap >= chunk_size:
        raise ValueError("overlap has to be smaller than chunk_size")

    chunks: list[Chunk] = []
    for doc in documents:
        start = 0
        index = 0
        while start < len(doc.text):
            piece = doc.text[start : start + chunk_size].strip()
            if piece:
                chunks.append(
                    Chunk(
                        text=piece,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::fallback_split",
                    )
                )
                index += 1
            start += chunk_size - overlap

    return chunks


# ─── Working out which documents belong together ─────────────────────────────

# The suffixes campus_life uses to split one subject across several files.
# Everything else is treated as a subject in its own right, which is what makes
# this safe to run on the other corpora: if nothing matches, every document
# becomes its own group and only the length rules below apply.
TOPIC_SUFFIXES = ("laundry", "noise", "followup", "exams", "workload")

_EXTENSION = re.compile(r"\.(txt|md)$", re.IGNORECASE)
_HEADING = re.compile(r"^#{1,6} +\S", re.MULTILINE)


def entity_of(source: str) -> tuple[str, str]:
    """
    Split a filename into the thing it is about and the angle it takes.

        housing_fenwick_court_laundry.txt -> ("housing_fenwick_court", "laundry")
        housing_fenwick_court.txt         -> ("housing_fenwick_court", "overview")
        admin_library_holds.txt           -> ("admin_library_holds", "overview")
    """
    stem = _EXTENSION.sub("", source)
    for suffix in TOPIC_SUFFIXES:
        if stem.endswith(f"_{suffix}"):
            return stem[: -(len(suffix) + 1)], suffix
    return stem, "overview"


def group_documents(
    documents: list[Document],
) -> dict[str, list[tuple[str, Document]]]:
    """
    Collect documents by the subject their filename names.

    Within a group the overview comes first and the angles follow in a fixed
    order, so that re-running the indexer produces the same chunks — and so
    that if a long group does get truncated at embedding time, what falls off
    the end is the most specific material rather than the introduction.
    """
    groups: dict[str, list[tuple[str, Document]]] = {}
    for doc in documents:
        key, topic = entity_of(doc.source)
        groups.setdefault(key, []).append((topic, doc))

    for members in groups.values():
        members.sort(key=lambda m: (m[0] != "overview", m[0], m[1].source))

    return groups


# ─── Turning a group into chunk text ─────────────────────────────────────────


def _header(members: list[tuple[str, Document]]) -> str:
    """
    A two-line preamble naming the subject and the angles covered below.

    This exists for the embedder, not the reader. It puts "laundry" and "noise"
    in the first forty characters of the chunk, where they are certain to be
    inside the 256-token window however long the rest of the group runs.
    """
    title = members[0][1].text.splitlines()[0].strip()
    topics = ", ".join(topic for topic, _ in members)
    return f"{title}\nTopics covered: {topics}"


def _document_title(text: str) -> str:
    """
    The first non-empty line of a document, with any markdown hashes removed.

    For a city guide that is `# Brightwater`. When such a guide is cut into
    sections, every piece after the first would otherwise be a paragraph about
    trains or restaurants with nothing in it naming the town.
    """
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped.lstrip("#").strip()
    return ""


def _render(
    header: str,
    members: list[tuple[str, Document]],
    label_files: bool,
) -> str:
    """
    Lay a group out as one piece of text.

    When documents are merged, each one keeps a header carrying its real
    filename. generate.py tells the model to name the document an answer came
    from, and these are the names it uses — so a fact merged in from
    `..._laundry.txt` still gets cited as that file rather than as the group.

    A standalone document gets no such header: `Chunk.source` is already its
    filename and generate.py prints it as `[from ...]`, so repeating it inside
    the text would only spend embedding budget saying the same thing twice.
    """
    if label_files:
        body = "\n\n".join(f"=== {doc.source} ===\n{doc.text}" for _, doc in members)
    else:
        body = "\n\n".join(doc.text for _, doc in members)
    return f"{header}\n\n{body}" if header else body


def _pack(
    header: str,
    members: list[tuple[str, Document]],
    limit: int,
    label_files: bool,
) -> list[list[tuple[str, Document]]]:
    """
    Fill chunks with whole documents, never going over `limit`.

    A group that fits becomes one chunk. A group that doesn't is broken at a
    document boundary rather than mid-sentence, and the header is repeated on
    each piece so both halves still say which building they are about.
    """
    packs: list[list[tuple[str, Document]]] = []
    current: list[tuple[str, Document]] = []

    for member in members:
        if current and len(_render(header, current + [member], label_files)) > limit:
            packs.append(current)
            current = [member]
        else:
            current.append(member)

    if current:
        packs.append(current)

    return packs


def _blocks(text: str) -> list[str]:
    """
    The natural break points in a document.

    Markdown sections if it has any — splitting `city_guides` on blank lines
    would orphan every `## Getting there` from the paragraph underneath it —
    and paragraphs otherwise.
    """
    if _HEADING.search(text):
        parts = re.split(r"\n(?=#{1,6} +\S)", text)
    else:
        parts = text.split("\n\n")
    return [part.strip() for part in parts if part.strip()]


def _hard_split(text: str, limit: int, overlap: int) -> list[str]:
    """Last resort: one block that is on its own longer than a whole chunk."""
    pieces: list[str] = []
    start = 0
    while start < len(text):
        piece = text[start : start + limit].strip()
        if piece:
            pieces.append(piece)
        start += limit - overlap
    return pieces


def _split_long_text(
    text: str,
    limit: int,
    overlap: int,
    carry: str = "",
) -> list[str]:
    """
    Cut one over-long document at section or paragraph boundaries.

    `carry` is repeated at the top of every piece after the first — the group
    header for a merged chunk, the document title for a standalone one. It is
    the same trick `_header` uses: whatever else a piece contains, it says what
    it is about in its first line, where the embedder is certain to read it.
    """
    room = limit - (len(carry) + 2) if carry else limit
    pieces: list[str] = []
    current = ""

    for block in _blocks(text):
        if len(block) > room:
            if current:
                pieces.append(current)
                current = ""
            pieces.extend(_hard_split(block, room, overlap))
            continue

        candidate = f"{current}\n\n{block}" if current else block
        if len(candidate) > room:
            pieces.append(current)
            # Carry the tail of the previous piece forward, so a sentence
            # split across the boundary is still readable in both.
            tail = current[-overlap:].lstrip() if overlap else ""
            current = f"{tail}\n\n{block}" if tail else block
            if len(current) > room:
                current = block
        else:
            current = candidate

    if current:
        pieces.append(current)

    if not carry:
        return pieces
    # The first piece already opens with the title or header it came from.
    return pieces[:1] + [f"{carry}\n\n{piece}" for piece in pieces[1:]]


# ─── The chunker ─────────────────────────────────────────────────────────────


def split_documents(documents: list[Document]) -> list[Chunk]:
    """
    Group each subject's documents into one chunk, splitting only if too long.

    On `campus_life` this turns 88 documents into roughly 49 chunks: 23 of them
    merged (7 halls, 9 courses, 7 dining venues) and 26 standalone admin, study
    and transit posts that have nothing to merge with and stay exactly as they
    were.

    `Chunk.source` is the subject for a merged chunk and the filename for a
    standalone one. The original filenames are never lost — they are headers
    inside the text, which is what the model cites.
    """
    limit = config.CHUNK_SIZE
    overlap = config.CHUNK_OVERLAP
    split_limit = min(config.EMBED_LIMIT, limit)

    if overlap >= split_limit:
        raise ValueError("overlap has to be smaller than the smaller ceiling")

    chunks: list[Chunk] = []

    for key, members in group_documents(documents).items():
        merged = len(members) > 1
        header = _header(members) if merged else ""
        source = key if merged else members[0][1].source
        index = 0

        for pack in _pack(header, members, limit, merged):
            rendered = _render(header, pack, merged)
            if len(rendered) <= limit:
                pieces = [rendered]
            else:
                pieces = _split_long_text(
                    rendered,
                    split_limit,
                    overlap,
                    carry=header or _document_title(rendered),
                )
            for piece in pieces:
                text = piece.strip()
                if not text:
                    continue
                chunks.append(
                    Chunk(
                        text=text,
                        source=source,
                        index=index,
                        produced_by="chunker.py::split_documents",
                    )
                )
                index += 1

    return chunks


def describe(chunks: list[Chunk]) -> str:
    """A one-line summary, printed after indexing."""
    if not chunks:
        return "0 chunks"
    lengths = [len(c.text) for c in chunks]
    return (
        f"{len(chunks)} chunks, "
        f"{sum(lengths) // len(lengths)} characters on average "
        f"(shortest {min(lengths)}, longest {max(lengths)}), "
        f"produced by {chunks[0].produced_by}"
    )


if __name__ == "__main__":
    from ingest import load_documents

    chunks = split_documents(load_documents())
    print(describe(chunks))
