"""
Your test questions.

Milestone 2 asks you to write five questions your system should be able to
answer from your corpus, specific enough to have a right answer.

  ✗ "What are good dining halls?"          — no right answer
  ✓ "What do students say about wait times at Commons during lunch?"

Fill in `QUESTIONS` below. `expects` is a word or short phrase you'd expect a
correct answer to contain — you'll use it in unit 2 when you build a scorer,
and having written it now means you decided what "correct" meant before you saw
any results.

`OUT_OF_SCOPE` holds five questions your documents clearly don't cover. You
need these in Milestone 4 to find where your relevance cutoff belongs, and
again in unit 2, where `run_eval.py` runs them through the gate and writes what
happened into your run log — that's the evidence for criterion 3.

Swap them for your own if you like. Keep five of them either way: criterion 3
names a target of "4 of 5", and four of three is not a thing.
"""

# Every `expects` below is a literal lifted from the document that answers the
# question, not a paraphrase of it. That matters for the scorer in unit 2: a
# correct answer to the HIST 118 question says "about 120 pages a week", which
# is what course_hist_118_workload.txt says — it does not say "moderate
# workload", so an `expects` of "moderate workload" would mark a right answer
# wrong. The source file is named after each one so the expectation can be
# checked against the corpus rather than trusted.
QUESTIONS = [
    # {"question": "...", "expects": "..."},

    # dining_kestrel_commons.txt + dining_kestrel_commons_followup.txt.
    # Both files give this figure; the merged chunk carries both.
    {"question": "How long are the lunch waits at Kestrel Commons between 12:15 and 1:00?", "expects": "20 to 25 minutes"},

    # course_hist_118_workload.txt — "a lot of reading, about 120 pages a week"
    {"question": "What is the expected weekly reading load for HIST 118?", "expects": "120 pages"},

    # study_library_hours.txt — the reading-week hours are the counterintuitive
    # part ("until 2am during term, until 10pm during reading week").
    {"question": "How late is the library open during reading week?", "expects": "10pm"},

    # housing_fenwick_court.txt has the prices, housing_fenwick_court_laundry.txt
    # has the timing. Answering both halves needs both files, which is exactly
    # what chunker.py::split_documents merges into one chunk.
    {"question": "In Fenwick Court, what does laundry cost and when is the best time to go?", "expects": "Tuesday"},

    # money_jobs.txt — "Maximum is 20 hours a week during term."
    {"question": "What is the maximum number of hours a week you can work on campus during term?", "expects": "20 hours"},
]

# Questions from a different world entirely. Your gate should refuse all five.
#
# There are five of these because criterion 3 in criteria.md names a target of
# "at least 4 of 5" — you need five things to try before you can report 4 of 5.
# `run_eval.py` runs these through retrieval and the gate on every eval and
# records what happened, so criterion 3 has evidence in the run log alongside
# the others. They cost no model calls: a refusal never reaches the model.
OUT_OF_SCOPE = [
    "What is the capital of Mongolia?",
    "How do I change the oil in a diesel engine?",
    "Who won the 1994 World Cup?",
    "What is the recommended dosage of ibuprofen for a headache?",
    "How do I write a for loop in Rust?",
]


def answered() -> list[dict]:
    """The questions you've actually filled in."""
    return [q for q in QUESTIONS if q.get("question", "").strip()]
