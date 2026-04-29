# Zeno Research — AI Socratic Tutoring for Secondary Humanities

Research, evaluation methodology, and published papers exploring 
AI-powered Socratic tutoring for Grade 9–12 humanities students 
(English Literature, IB English, AP/SAT prep).

Built and maintained by Greg O'Keefe — BC-certified teacher, tutor, 
and independent researcher.

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

1. **The Economic Conversion of Cognitive Production**  
   Life in the pre-AI era — how cognitive labour was valued 
   before AI began replicating it at scale.  
   [Read on OSF](https://doi.org/10.35542/osf.io/67d5x_v1)

2. **The Intelligence Premium**  
   How AI redistributes the returns on human cognitive work 
   and what that means for knowledge workers.  
   [Read on OSF](https://doi.org/10.35542/osf.io/r74sg_v1)

3. **The Cognitive Allocation Gap**  
   How AI tools are shifting cognitive load away from students 
   and what that means for assessment and pedagogy.  
   [Read on OSF](https://doi.org/10.35542/osf.io/u5yv2_v1)

4. **BC Secondary School AI Policy Audit**  
   65% of BC secondary schools lacked AI-specific academic 
   integrity language 26 months post-ChatGPT.  
   [Read on OSF](https://doi.org/10.35542/osf.io/nhbfp_v1)

5. **The Endogenous Machine**  
   AI as a trajectory rather than a noun — the institutional 
   obsolescence thesis.  
   [Read on OSF](https://doi.org/10.35542/osf.io/c9nj3_v1)

6. **The Gap Engine**  
   Architecture and design of a Socratic tutoring system for 
   secondary humanities.  
   [Read on OSF](https://doi.org/10.35542/osf.io/j23sh_v1)

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

## Files in This Repository

**`zeno_harness_v2.py`**  
Synthetic tutoring session simulator. Runs Claude Sonnet as Zeno 
(tutor) against Claude Haiku as a student persona. Scores each 
turn using the Synchronicity Evaluator and logs Descent Protocol 
activations. Requires an Anthropic API key.

**`Student_A_System_Prompt_v2.txt`**  
Example synthetic student persona using a state variable 
architecture. Models energy, vocabulary confidence, engagement, 
patience, and metacognitive awareness as independent variables 
with different depletion rates. Derived from real tutoring 
observations, anonymized.

**`animal_farm_student_summary.txt`**  
Example student-context compression. The full novel (30,061 words) 
distilled to 719 words of imperfect recall — what a student who 
read it once quickly would actually retain. Fed to the student 
model while Zeno receives the full text.

---

## Contact

Greg O'Keefe  
greg.okeefe@gmail.com or https://gregokeefe.substack.com/
