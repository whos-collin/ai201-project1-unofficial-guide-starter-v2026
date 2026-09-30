import re

import gate


def _norm(text: str) -> str:
    """Lowercase and drop spaces/periods/dashes, so "10 p.m." matches "10pm"
    and "20–25" matches "20 to 25"."""
    text = re.sub(r"\s*[-–—]\s*", " to ", text.lower())
    return re.sub(r"[\s.]+", "", text)


def judge(question, expects, answer, results) -> bool:
    """An answer passes only if all three hold:
    1. it wasn't a refusal and it contains the expected fact,
    2. that fact is actually in a retrieved chunk (grounded, not recalled),
    3. it names at least one of the retrieved source documents."""
    if not expects or answer.strip() == gate.REFUSAL:
        return False
    want = _norm(expects)
    in_answer = want in _norm(answer)
    in_chunks = any(want in _norm(r.text) for r in results)
    stems = {r.source.lower().removesuffix(".txt") for r in results}
    names_source = any(stem in answer.lower() for stem in stems)
    return in_answer and in_chunks and names_source
