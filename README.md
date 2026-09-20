# The Unofficial Guide

<!-- Replace this line with your name and which corpus you picked. -->

> **This file is your submission.** Fill it in as you go — most sections get
> written during the milestone that produces them, not at the end.
>
> How the starter works, and every command you'll need, is in `RUNNING.md`.
> Leave that file alone.
>
> **Paste everything as text.** No screenshots, no video. A typed table gets
> full credit; a picture of the same table gets none.
>
> Delete these instruction blocks as you replace them. The `<!-- -->` comments
> are notes to you and don't show up when the page renders — you can leave them
> or remove them.

---

# Unit 1

## What This Does

I picked the campus life corpus as I am currentl in college and information like this is used in my day to day life all the time. This model answers many types of questions pertaining to the college experience, including housing, transit, campus jobs, dining and more. 


<!-- Three or four sentences. Which corpus you picked, and the kinds of
     questions your system answers. Write it for someone who has never seen
     this repo.

     Milestone 5. -->

## Chunking Strategy

 These two numbers mean something different now than they did in the starter.
 campus_life documents run 300-554 characters each, so the starter's 800-
 character window never cut anything: 88 documents came out as 88 chunks.
 chunker.py::split_documents groups related documents together instead —
 one dorm, one course or one dining venue per chunk — so CHUNK_SIZE is a
 CEILING on a merged chunk rather than a length to cut at.

 1400 is measured, not guessed. The 23 merged groups in campus_life run from
 788 characters (dining_north_kitchen) to 1400 (housing_old_brewhouse); all 7
 dining and all 9 course groups are under 1070, and only housing reaches up
 here. A 1200 ceiling split five housing groups, one of them six characters
 over the line, which is an arbitrary place to cut a building in half.

 This is knowingly a little above what the embedder reads. all-MiniLM-L6-V2
 takes 256 tokens (~1,000-1,200 characters) and silently ignores the rest.
 Only the vector is truncated — Chroma stores and returns the whole chunk — so
 the cost is that the tail of the longest housing groups is retrievable but
 not matchable, and the two-line header in chunker.py::_header is what pays
 for it: the building name and "laundry, noise" sit in the first 80
 characters, inside the window, whatever falls off the end.

 That trade only works at this scale. Grouping a whole category instead —
 "all housing" is ~10,000 characters — would put roughly 88% of the corpus
 past the window with nothing in the pipeline reporting it.
**CHUNK_SIZE = 1400**    # ceiling on a merged chunk, in characters

 The ceiling used when a single document has to be cut up, rather than when
 several are merged. It is lower than CHUNK_SIZE on purpose: a merged chunk
 can afford to overshoot the embedding window because its header keeps the
 subject inside it, and a cut-up document has no such guarantee.

 Nothing in the provided corpora is inherently longer than this — city_guides
 has 98 markdown sections and the largest is 711 characters. What this really
 controls is how many neighbouring sections get packed into one chunk before
 the next one starts.
**EMBED_LIMIT** = 1100 **     # ceiling when splitting one long document

 Only applies where a single document is genuinely too long for one chunk —
 the city_guides corpus, whose guides run ~2,000 characters. Merged
 campus_life chunks are split at document boundaries instead, and repeat their
 header, so they never need character overlap.
**CHUNK_OVERLAP = 150 **    # characters carried across a split inside one document



<!-- What about YOUR documents made you pick these numbers? Short posts and
     long sectioned guides don't want the same chunking, and "800 seemed
     reasonable" earns nothing. Point at something you noticed when you read
     the documents in Milestone 1.

     If you changed your mind partway through, say so and say why. That's worth
     more than pretending you got it right first time.

     Milestone 3. -->

## Sample Chunks

======================================================================
Chunk 1  |  source: admin_add_drop_deadline.txt#0  |  produced by: chunker.py::split_documents
======================================================================
On the add/drop deadline

You can add a course through the end of the second week. Dropping is a longer window — through the end of week six — but a drop after week two shows as a W on your transcript. Nothing anywhere on the registrar's site says this plainly, and students find out from each other.

======================================================================
Chunk 2  |  source: admin_parking_permits.txt#0  |  produced by: chunker.py::split_documents
======================================================================
On the parking permits

Student permits for the west lots go on sale in August and sell out in about three days. The east lot never sells out because it's a 12-minute walk. There is no waitlist — people who miss the window park on Verrill Street and walk in, which is legal but unmarked and confuses everyone.

======================================================================
Chunk 3  |  source: course_cs_210#0  |  produced by: chunker.py::split_documents
======================================================================
CS 210 Data Structures
Topics covered: overview, exams, workload

=== course_cs_210.txt ===
CS 210 Data Structures

I'm a junior and I've done this twice now. Format is lecture with weekly labs; slides go up after class, not before. Assessment: two midterms and a final, all drawn from lecture material rather than the textbook. Midterms are curved, the final is not.

Expect 8 to 10 hours a week outside class.

The one piece of advice: do the labs even though they're only 10% — the exams reuse the lab problems.

=== course_cs_210_exams.txt ===
CS 210 Data Structures — assessment

Two midterms and a final, all drawn from lecture material rather than the textbook. Midterms are curved, the final is not.

Do the labs even though they're only 10% — the exams reuse the lab problems.

=== course_cs_210_workload.txt ===
Workload for CS 210 Data Structures

People keep asking so: 8 to 10 hours a week outside class. That's real time, not optimistic time.

It's front-loaded — the first month is heavier than the rest, partly because you're learning the format.

======================================================================
Chunk 4  |  source: dining_kestrel_commons#0  |  produced by: chunker.py::split_documents
======================================================================
Kestrel Commons
Topics covered: overview, followup

=== dining_kestrel_commons.txt ===
Kestrel Commons

I'm a junior and I've done this twice now. Wait times: 20 to 25 minutes between 12:15 and 1:00, under 5 minutes before 11:45. The thing worth going for is the stir-fry station, made to order. The thing to know is that the salad bar wilts after 1:30.

Hours are 7:00am to 9:00pm weekdays, 9:00am to 8:00pm weekends. Costs one meal swipe, or $12.50 cash.

=== dining_kestrel_commons_followup.txt ===
Re: Kestrel Commons

Adding to what people have said about Kestrel Commons. The wait figure of 20 to 25 minutes between 12:15 and 1:00 matches what I've seen. If you're trying to eat between classes, go before 11:45 and it's a different building entirely.

Also worth saying: the salad bar wilts after 1:30. Nobody tells you this at orientation.

======================================================================
Chunk 5  |  source: housing_fenwick_court#0  |  produced by: chunker.py::split_documents
======================================================================
Fenwick Court — what it's actually like
Topics covered: overview, laundry, noise

=== housing_fenwick_court.txt ===
Fenwick Court — what it's actually like

Just finished a year in this building. Built 2015. Rooms are suites of four with a shared kitchenette.

The good: in-suite bathrooms, and the kitchenette means you can skip a meal plan tier.

The bad: the furthest housing from central campus, about 18 minutes on foot.

Laundry costs $2.00 wash, $1.75 dry, app-based. On noise: thin walls between suites; the kitchenettes carry sound.

=== housing_fenwick_court_laundry.txt ===
Laundry in Fenwick Court

Machines take $2.00 wash, $1.75 dry, app-based. There are eight washers and six dryers for the building, which is the wrong ratio and means the dryers back up on Sunday evenings.

Best time to do laundry here is Tuesday or Wednesday morning. Sunday after 6pm you will wait.

=== housing_fenwick_court_noise.txt ===
Noise levels in Fenwick Court

Asked about this a lot so writing it down. Thin walls between suites; the kitchenettes carry sound.

If you're someone who needs quiet to work, the library is open until 2am during term and that's what most people in this building end up doing.

For each one, ask: could someone answer a question using only this,
without reading what came before or after?

## Sample Answer

<!-- One complete question and answer, pasted as text, with the source line
     visible. Milestone 4. -->

**Question:**
Why am i unable to use leftover di
ning dollars from the previous autum semester this spring. Answer using only the information in the documents below. If they don't cover it, say you don't have enough information."
**Answer:**
Dining dollars roll over from the autumn semester to the spring, but whatever is left in May disappears. (Source: admin_dining_dollars.txt)

Sources retrieved: admin_dining_dollars.txt, admin_meal_plan_changes.txt, course_econ_101, dining_north_kitchen, dining_pellew_dining_hall
```
```

**My relevance cutoff:**
     0.5
<!-- The number you set in config.py, and how you got there.

     You ran five questions your corpus covers and the five in OUT_OF_SCOPE
     that it clearly doesn't, and wrote down the best distance for each. What
     did those two groups look like? Where was the gap? Put the actual numbers
     here — the table below wants all ten rows.

Q1: (best distance 0.203, cutoff 0.6)

Q2: (best distance 0.375, cutoff 0.6)

Q3: (best distance 0.274, cutoff 0.6)

Q4: (best distance 0.467, cutoff 0.6)

Q5: (best distance 0.427, cutoff 0.6)

OOSQ1: (best distance 0.913, cutoff 0.6)

OOSQ2: (best distance 0.934, cutoff 0.6)

OOSQ3: (best distance 0.942, cutoff 0.6)

OOSQ4: (best distance 0.844, cutoff 0.6)

OOSQ5: (best distance 0.877, cutoff 0.6)


     Milestone 4. -->

| Question | In corpus? | Best distance |
|---|---|---|
|  |  |  |

## How I Used AI

I used AI to firstly help me write the chunking function. I wanted to create a function that strayed slightly differently from what I was asked to do, but made sense to me. It made the most sense to chunk documents my the specific topic they were talking about (i.e. first into housing, then into laundry in the housing topic). I initially wanted to chunk by overall topic, however as I was promting claude, I then brought up that it was actually bad practice, and had claude go away from that route, instead coming to the solution we have here. 

Secondly, I had it help me search for a term. Even if this seems rudimentary, and I could have searched through all the files my self, the projects instructions did not define where top-k was located. I prompted claude to look for it for me and it promptly returned all the locations that term was located. It also returned all the variations of that term (top-k vs TOP_K).

<!-- Two specific moments. For each: what you asked for, what came back, and
     what you changed about it.

     "I asked Claude to write the chunking function from my notes. It ignored
     the overlap, so I added that myself" is the level of detail we're after.
     "I used AI to help me code" is not.

     Milestone 5. -->

**1.**

**2.**

<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Unit 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     unit 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

<!-- Your five criteria, three runs each. `python run_eval.py --label before`
     runs the questions, puts the OUT_OF_SCOPE ones through the gate, and
     writes it all into results/ for you. Targets come from criteria.md; the
     verdict column is your call.

     Criterion 3 is measured in one deterministic pass rather than three, so
     the same number goes in all three run columns. That's correct, not lazy.

     Milestone 1. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

<!-- Underneath, paste the REAL output for each criterion from one of your
     runs — the actual text your system produced, not a description of it.
     Name the file and function that produced it. -->

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |

## Diagnoses

<!-- For each miss: which stage caused it, and how. The stage alone isn't
     enough — you need the mechanism.

     Not a diagnosis: "Question 3 didn't work."
     A diagnosis:     "Question 3 asks about laundry costs. The answer is in
                       one sentence that got split across two chunks, so
                       neither chunk on its own contains it."

     The five stages: loading → chunking → embedding → retrieval → generation.

     Look for a pattern. If three misses all ask about numbers, that's one
     problem, not three.

     Missed nothing? Say so, then say honestly whether your targets were set
     low, and which one you'd tighten and to what.

     Milestone 3. -->

## The Improvement

**What I changed:**

**Why I picked it:**

<!-- Connect it to a specific diagnosis above in one sentence. If you can't,
     you picked a fix because it sounded impressive. -->

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

**Did it help?**

<!-- Say plainly whether it did, and how you know. If it made things worse,
     say that — a change that backfired, honestly reported, earns full credit
     and is more interesting than one that worked. What matters is that you can
     tell.

     Milestone 4. -->

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->
