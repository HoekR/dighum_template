# Step-back review

**Status:** draft  
**Applies to:** all DH projects with iterative eval / method work, especially LLM-assisted  
**Portable:** yes  
**Companion:** [iteration-decision-framework](iteration-decision-framework.md), [claims-and-eval-gate](claims-and-eval-gate.md), `docs/EVALUATION_STRATEGIES.md` §7

## Rule

Review the **series** of attempts at a question as a whole, not only the last result. Do this as a regular step, not only when stuck. When several attempts of *different kinds* have failed, or a result looks strange, the problem is probably not in the method but in the frame (the unit, the question, or the sources). Question the frame; do not try another fix.

Converging failure is a result, like converging success. When independent approaches agree on an answer, the answer holds; when different approaches all fail, the conclusion is that the question does not fit the available data in this form. The diagnostic question after a run of failures is: **what did all the attempts have in common?** That is where the frame sits. Record it as one positive claim about the sources ("N methods converge: X is not in the sentence"), not as N retractions.

The step itself is human. An LLM works inside the frame it was given: it can improve hypotheses within the hermeneutic circle, but stepping outside it (asking what counts as part and what as whole) requires knowledge of the sources. The rule for the agent is therefore a **handoff**, not "step back yourself".

This is not hypothesis-forming. A hypothesis, its test and its refinement all stay inside the circle; so do failed fixes. Stepping back means questioning the circle itself: what counts as part and what as whole (the sentence was taken as the whole; it turned out to be a part of the entry, governed by its heading). Seen from inside, that move looks like serendipity. It is not: it is deliberate, triggered by persistent failure or something strange, and informed by knowing how the sources were made.

## Handoff (what the agent does)

**Trigger:** attempt budget reached for a concern (see iteration-decision-framework), ≥2–3 failed fixes of different kinds on the same eval question, or any result that looks strange.

Then the agent:

1. **Stops proposing fixes.** No fix number four.
2. **Lays out the series on one page:** each attempt, what it changed, what it measured, the outcome (absolute numbers).
3. **Lists what all attempts had in common**, the assumptions none of them varied: unit of analysis, the question, the source shape (structure, genre, gaps, preprocessing). The shared assumption is the prime suspect.
4. **Shows failures in context:** full page or entry, not snippets; error breakdown by structural position (title / head / body).
5. **Offers cheap hypotheses about the sources**, not the method, explicitly as candidates for the human to judge.

**Human:** decides whether the frame holds. **Agent:** records the outcome as a claim (adopt / defer / stop / retract).

## Why

Evaluations built on one frame cannot find the better frame. Seen from inside, a reframing looks like luck, so the agent records it as an accident, and then the lesson can't be taught. It is not luck. It is a deliberate step back, informed by knowing how the material was made. Agents are strong at single-loop iteration (change the action) and weak at double-loop (question the assumptions behind the actions). They also present their own frame fluently enough that the human stops stepping out of it.

## Example

trifecta-annotation, Step B/C (2026): bigger model, grounding, span extraction, few-shots, split classifier, retrieval all failed with the sentence as unit. Stepping back and asking where in the document the goal is named showed that 71% of 3,326 recipes name it in the title and never in the body. The agent had read the extractor that ignored 4,795 TEI entry heads and never questioned it.
