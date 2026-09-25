---
doc: learner-profile
status: approved
---

# Learner profile

**Who.** Aleksandr Khrukalo, Bishkek. Independent Android and AI developer, KHLab. Seven apps live
in the Amazon Appstore, an agent skill contributed upstream to a vendor's own skill set, and four
earlier proofs of concept in this hackathon, each asking the same question of a different artifact:
what evidence backs this claim?

**What I am practising here.** Scoping under a real constraint. The previous project taught me that
the whole value of a checker is its refusal to guess; this one starts from that lesson rather than
discovering it. Before writing code I probed two candidate ideas against thirteen real repositories
to find out whether the findings would be true, and the probe immediately produced two false
positives. That is the material the scope is built from.

**What I already know.** Python, the `ast` module, packaging metadata, pytest, CI.

**Where I get it wrong.** I widen a rule until the tool always has something to say. The fix that
worked three times now is to name, in the spec, the cases the tool must decline.

**What "done" looks like for me.** It stays silent on maintained projects, it explains the cases it
declined, and the one thing it does say is something a maintainer would act on.
