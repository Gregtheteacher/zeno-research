# zeno-research
Research and evaluation tools for AI-powered Socratic tutoring in secondary humanities (Grades 9–12). Includes synthetic student simulation harness, Synchronicity Score methodology, and published papers on the Cognitive Allocation Gap and Gap Engine architecture.
# Zeno Research — AI Socratic Tutoring for Secondary Humanities

Research, evaluation methodology, and published papers exploring 
AI-powered Socratic tutoring for Grade 9–12 humanities students 
(English Literature, IB English, AP/SAT prep).

Built and maintained by Greg O'Keefe — BC-certified teacher, 
independent researcher, and founder of EM Academy Canada.

---

## The Problem

AI tutoring systems work well in mathematics and STEM because 
answers are verifiable. In humanities — literary analysis, 
historical interpretation, ethical reasoning — there is no 
ground truth to check against. Most AI tools in this space 
either give students the answer directly or retreat to generic 
encouragement. Neither produces learning.

The deeper threat is substitution: AI assembling meaning on 
behalf of students rather than helping them build it themselves.

---

## The Research Program

### Published Papers

1. **The Cognitive Allocation Gap** — EdArXiv/OSF  
   How AI tools are shifting cognitive load away from students 
   and what that means for assessment and pedagogy.

2. **BC Secondary School AI Policy Audit**  
   65% of BC secondary schools lacked AI-specific academic 
   integrity language 26 months post-ChatGPT.

3. **The Endogenous Machine**  
   AI as a trajectory rather than a noun — the institutional 
   obsolescence thesis.

4. **Institutional Semantic Drift (ISD)**  
   How institutions lose the ability to adapt to conceptual 
   change over time.

*(Links to all papers on EdArXiv/OSF — add URLs here)*

---

## The Gap Engine (Project Zeno)

A Socratic tutoring system built on three core architectural 
principles:

**Synchronicity Score** — A per-turn metric measuring the gap 
between where a student currently is and where the DLC target 
requires them to be. Tracks trajectory across a session.

**Descent Protocol** — A deterministic intervention that fires 
when a student stalls. Instead of providing the answer, the 
system descends through three levels: context probe → 
experiential bridge → definition as bridge. Returns to the 
original question after each level.

**Non-Substitution Rule** — The system never assembles meaning 
for the student. Socratic questioning only. This is enforced 
architecturally, not just as a prompt suggestion.

---

## This Repository

**What's here:**
- Synthetic student simulation harness (`zeno_harness_v2.py`)
- Synchronicity Score evaluation methodology
- Descent Protocol specification and gating logic
- Student persona framework (state variable architecture)
- Baseline results from April 2026 runs

**What's not here:**
- Full Zeno system prompt (proprietary)
- DLC pack content (proprietary)
- Live student session data

---

## Contact

Greg O'Keefe  
greg.okeefe@gmail.com or https://gregokeefe.substack.com/
[Your email or Substack link]
