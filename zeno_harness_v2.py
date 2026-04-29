"""
Zeno Stress-Test Harness v2
============================
Adds deterministic Descent Protocol detection, injection, and logging.
All other architecture unchanged from v1.

New in v2:
    - scorer now captures stuck_streak from JSON output
    - evaluate_descent() ports the gating logic from zeno-chat/index.ts
    - descent instruction injected into Zeno context when fired
    - CSV gains 4 new columns: stuck_streak, descent_fired, descent_level, descent_instruction

Usage:
    python zeno_harness_v2.py --student A --runs 5 --turns 10 --text animal_farm.txt
"""

import anthropic
import json
import csv
import argparse
import os
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ── CONFIGURATION ─────────────────────────────────────────────────────────────

CLAUDE_MODEL   = "claude-sonnet-4-6"
STUDENT_MODEL  = "claude-haiku-4-5-20251001"

ZENO_TEMPERATURE    = 0.7
STUDENT_TEMPERATURE = 0.9
SCORER_TEMPERATURE  = 0.2
RATE_LIMIT_DELAY    = 0.5

# ── SCORER SYSTEM PROMPT (verbatim from zeno-chat/index.ts) ───────────────────

SCORER_SYSTEM_PROMPT = """You are the Synchronicity Evaluator. You observe tutoring conversations between Zeno (a Socratic tutor) and a student. You do not participate in the conversation. You read and you judge.

After each student turn, evaluate the student's most recent response against this single question: did the student arrive at this understanding independently, or did they receive it from Zeno?

Score the student's most recent response on a scale of 0 to 100:

0–20: The student is not producing. They are deflecting, repeating Zeno's words, giving one-word answers, or saying they don't know.

21–40: The student is producing at a surface level. They are restating plot, using vocabulary without demonstrating understanding, or giving answers that are technically correct but show no depth of reasoning.

41–60: The student is producing at a mid level. They are making connections, showing causation, beginning to interpret — but the reasoning is incomplete or partially scaffolded by Zeno's prior framing.

61–80: The student is producing independently. They are generating interpretation, using evidence from the text, making analytical claims that go beyond what Zeno has provided.

81–100: The student is arriving. They are producing insight that is genuinely their own — synthesizing, arguing, applying concepts to new contexts without prompting.

METACOGNITIVE AWARENESS RULE: Distinguish between two types of stuckness:

1. METACOGNITIVE STUCKNESS (hold or nudge up): The student explicitly names or describes their own confusion — phrases like "I keep ending up in the same place," "I'm not sure what you're asking," "I don't know how to answer that," "I feel like I'm going in circles," or any explicit acknowledgment that they are stuck or confused. A student who can identify a gap in their own understanding is demonstrating real cognitive work. Do NOT reduce the score for this. Hold the score steady or nudge it up slightly (1-3 points).

2. REGRESSIVE STUCKNESS (reduce score): The student produces content that actively regresses — making incorrect claims that contradict previously demonstrated understanding, losing ground on concepts they had shown competence with, or disengaging without any self-awareness (e.g., one-word answers, topic avoidance, passive deflection). Only reduce the score for this type.

Also assess trajectory: is the score improving, flat, or declining across the last three turns?

STUCK STREAK: Examine the last several student turns. A "stuck streak" is the number of consecutive recent student turns (including the most recent) that are circling the same question or impasse without meaningfully advancing the underlying understanding. Reset the count to 0 when the student moves to a new question or breaks through. Only count turns on the SAME question.

Output format — JSON only, no other text:
{ "score": [integer 0-100], "level": [integer -1 to 4], "trajectory": ["improving" | "flat" | "declining"], "stuck_streak": [integer 0-10], "diagnosis": "[one sentence describing what the student is doing and what Zeno should do next]" }"""


# ── DESCENT GATING (port of zeno-chat/index.ts) ───────────────────────────────

def evaluate_descent(score: int, trajectory: str, stuck_streak: int):
    """
    Pure port of the Descent gating condition from zeno-chat/index.ts.
    Fires only when all three conditions are true:
        stuck_streak >= 2
        trajectory in {flat, declining}
        score < 50
    Returns None if no descent, otherwise a dict with descent_level,
    reason, and instruction (the string injected into Zeno's context).
    """
    trajectory_stalled = trajectory in ("flat", "declining")
    if not (stuck_streak >= 2 and trajectory_stalled and score < 50):
        return None

    if stuck_streak >= 4:
        descent_level = "L3"
    elif stuck_streak == 3:
        descent_level = "L2"
    else:
        descent_level = "L1"

    reason = (
        f"student stalled for {stuck_streak} consecutive turns on the same "
        f"question (trajectory {trajectory}, score {score})"
    )

    if descent_level == "L1":
        action = "reframe with a context probe using something the student already knows from the text"
    elif descent_level == "L2":
        action = "build an experiential bridge — strip the literary context and find the concept in the student's own life"
    else:
        action = "give the definition cleanly in one sentence, then immediately return to L1 with the same question reframed"

    instruction = (
        f"[DESCENT: {descent_level} — {reason}. "
        f"Apply the Descent Protocol now: {action}.]"
    )

    return {
        "descent_level": descent_level,
        "reason": reason,
        "instruction": instruction,
    }


# ── LOAD PROMPTS ──────────────────────────────────────────────────────────────

def load_prompt(filepath):
    with open(filepath, "r") as f:
        return f.read()


# ── API CALLS ─────────────────────────────────────────────────────────────────

def call_zeno(client, zeno_prompt, conversation, text_context, descent_instruction=None):
    """
    Call Zeno via Anthropic API.
    If descent_instruction is provided, inject it as the final user message
    so Zeno receives the deterministic Descent directive.
    """
    messages = [{"role": "user", "content": f"[TEXT FOR THIS SESSION]\n\n{text_context}"}]
    messages += conversation

    if descent_instruction:
        messages.append({"role": "user", "content": descent_instruction})

    response = client.messages.create(
        model=CLAUDE_MODEL,
        system=zeno_prompt,
        messages=messages,
        max_tokens=512,
        temperature=ZENO_TEMPERATURE
    )
    time.sleep(RATE_LIMIT_DELAY)
    return response.content[0].text.strip()


def call_student(client, student_prompt, conversation, text_context):
    """Call the Student persona via Claude Haiku."""
    student_system = (
        student_prompt
        + f"\n\n---\nTEXT YOU HAVE READ FOR THIS SESSION:\n\n{text_context}\n\n"
        + "You have read this text but may not remember all details clearly. "
        + "You know roughly what happens but struggle to explain what it means. "
        + "Do NOT quote the text directly or fluently. Recall it imperfectly, "
        + "the way a student who read it once quickly would."
    )

    flipped = []
    for msg in conversation:
        if msg["role"] == "user":
            flipped.append({"role": "assistant", "content": msg["content"]})
        else:
            flipped.append({"role": "user", "content": msg["content"]})

    if not flipped:
        flipped = [{"role": "user", "content": "The tutor is about to open the session. Wait for their first message."}]

    response = client.messages.create(
        model=STUDENT_MODEL,
        system=student_system,
        messages=flipped,
        max_tokens=256,
        temperature=STUDENT_TEMPERATURE
    )
    time.sleep(RATE_LIMIT_DELAY)
    return response.content[0].text.strip()


def call_scorer(client, conversation):
    """
    Call the Scorer LLM using the production SCORER_SYSTEM_PROMPT.
    Returns parsed dict with score, level, trajectory, stuck_streak, diagnosis.
    """
    formatted = []
    for msg in conversation:
        speaker = "STUDENT" if msg["role"] == "user" else "ZENO"
        formatted.append(f"{speaker}: {msg['content']}")

    conversation_text = "\n\n".join(formatted)

    scorer_message = (
        "Here is the tutoring conversation so far. "
        "Evaluate the STUDENT's most recent response only.\n\n"
        f"{conversation_text}\n\n"
        "Return your evaluation as JSON only. No other text."
    )

    response = client.messages.create(
        model=CLAUDE_MODEL,
        system=SCORER_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": scorer_message}],
        max_tokens=256,
        temperature=SCORER_TEMPERATURE
    )
    time.sleep(RATE_LIMIT_DELAY)

    raw = response.content[0].text.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        parsed = json.loads(raw.strip())
        return {
            "score":        int(parsed.get("score", -1)),
            "level":        int(parsed.get("level", -99)),
            "trajectory":   parsed.get("trajectory", "unknown"),
            "stuck_streak": int(parsed.get("stuck_streak", 0)),
            "diagnosis":    parsed.get("diagnosis", ""),
        }
    except (json.JSONDecodeError, ValueError):
        return {
            "score": -1, "level": -99, "trajectory": "parse_error",
            "stuck_streak": 0, "diagnosis": f"Parse error: {raw[:100]}"
        }


# ── SESSION RUNNER ────────────────────────────────────────────────────────────

def run_session(client, zeno_prompt, student_prompt, zeno_text, student_text,
                num_turns, run_id, student_type):
    """
    Run one complete synthetic tutoring session.
    Returns a list of turn records including Descent telemetry.
    """
    conversation = []
    turn_records = []

    print(f"\n  [Run {run_id}] Starting session...")

    # Zeno opens
    zeno_opening = call_zeno(client, zeno_prompt, conversation, zeno_text)
    conversation.append({"role": "assistant", "content": zeno_opening})
    print(f"  ZENO: {zeno_opening[:80]}...")

    for turn_num in range(1, num_turns + 1):

        # Student responds
        student_response = call_student(client, student_prompt, conversation, student_text)
        conversation.append({"role": "user", "content": student_response})
        print(f"  STUDENT (turn {turn_num}): {student_response[:80]}...")

        # Score the student turn
        score_data = call_scorer(client, conversation)
        stuck_streak = score_data.get("stuck_streak", 0)
        print(f"  SCORE: {score_data['score']} | {score_data['trajectory']} | streak:{stuck_streak} | {score_data['diagnosis'][:60]}...")

        # Evaluate Descent
        descent = evaluate_descent(
            score=score_data["score"],
            trajectory=score_data["trajectory"],
            stuck_streak=stuck_streak
        )

        if descent:
            print(f"  *** DESCENT FIRED: {descent['descent_level']} — {descent['reason'][:60]}...")

        # Record this turn
        turn_records.append({
            "run_id":               run_id,
            "student_type":         student_type,
            "turn":                 turn_num,
            "zeno_prior":           zeno_opening if turn_num == 1 else conversation[-3]["content"],
            "student_response":     student_response,
            "score":                score_data["score"],
            "level":                score_data["level"],
            "trajectory":           score_data["trajectory"],
            "diagnosis":            score_data["diagnosis"],
            "stuck_streak":         stuck_streak,
            "descent_fired":        1 if descent else 0,
            "descent_level":        descent["descent_level"] if descent else "",
            "descent_instruction":  descent["instruction"] if descent else "",
        })

        # Zeno responds (inject Descent instruction if fired)
        if turn_num < num_turns:
            descent_instruction = descent["instruction"] if descent else None
            zeno_response = call_zeno(
                client, zeno_prompt, conversation, zeno_text,
                descent_instruction=descent_instruction
            )
            conversation.append({"role": "assistant", "content": zeno_response})
            label = " [DESCENT]" if descent else ""
            print(f"  ZENO{label}: {zeno_response[:80]}...")

    return turn_records


# ── RESULTS WRITER ────────────────────────────────────────────────────────────

def write_results(all_records, output_path):
    if not all_records:
        print("No records to write.")
        return
    fieldnames = list(all_records[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_records)
    print(f"\nResults written to: {output_path}")


def print_summary(all_records, student_type):
    if not all_records:
        return

    scores = [r["score"] for r in all_records if r["score"] >= 0]
    descents = [r for r in all_records if r["descent_fired"] == 1]

    by_turn = {}
    for r in all_records:
        t = r["turn"]
        if t not in by_turn:
            by_turn[t] = []
        if r["score"] >= 0:
            by_turn[t].append(r["score"])

    print(f"\n{'─'*50}")
    print(f"SUMMARY — Student {student_type}")
    print(f"{'─'*50}")
    print(f"Total turns scored:  {len(scores)}")
    print(f"Overall mean score:  {sum(scores)/len(scores):.1f}")
    print(f"Descent activations: {len(descents)}")

    if descents:
        levels = {}
        for d in descents:
            lv = d["descent_level"]
            levels[lv] = levels.get(lv, 0) + 1
        print(f"  By level: { {k: levels[k] for k in sorted(levels)} }")

    print(f"\nMean score by turn:")
    for turn in sorted(by_turn.keys()):
        turn_scores = by_turn[turn]
        mean = sum(turn_scores) / len(turn_scores)
        bar = "█" * int(mean / 5)
        print(f"  Turn {turn:2d}: {mean:5.1f}  {bar}")

    trajectories = [r["trajectory"] for r in all_records]
    total = len(trajectories)
    for label in ("improving", "flat", "declining"):
        count = trajectories.count(label)
        print(f"  {label.capitalize():10s}: {count}/{total} ({100*count//total}%)")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Zeno Stress-Test Harness v2")
    parser.add_argument("--student", choices=["A", "B"], required=True)
    parser.add_argument("--runs",    type=int, default=5)
    parser.add_argument("--turns",   type=int, default=10)
    parser.add_argument("--text",    type=str, default=None)
    parser.add_argument("--zeno-prompt",      type=str, default="zeno_system_prompt.txt")
    parser.add_argument("--student-a-prompt", type=str, default="Student_A_System_Prompt_v2.txt")
    parser.add_argument("--student-b-prompt", type=str, default="Student_B_System_Prompt.txt")
    parser.add_argument("--student-text",     type=str, default=None,
                        help="Path to student's version of the text (e.g. a summary). Falls back to --text if omitted.")
    parser.add_argument("--output",           type=str, default=None)
    args = parser.parse_args()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found.")
    client = anthropic.Anthropic(api_key=api_key)

    print("Loading prompts...")
    zeno_prompt = load_prompt(args.zeno_prompt)

    if args.student == "A":
        student_prompt = load_prompt(args.student_a_prompt)
        student_label  = "A (Cecilia)"
    else:
        student_prompt = load_prompt(args.student_b_prompt)
        student_label  = "B (Jason)"

    if args.text and os.path.exists(args.text):
        zeno_text = load_prompt(args.text)
        print(f"Zeno text loaded: {args.text}")
    else:
        zeno_text = "[No text loaded. Zeno operating in general Socratic mode.]"
        print("Warning: No text file provided.")

    if args.student_text and os.path.exists(args.student_text):
        student_text = load_prompt(args.student_text)
        print(f"Student text loaded: {args.student_text}")
    else:
        student_text = zeno_text
        print("No separate student text provided — student will use same text as Zeno.")

    if args.output:
        output_path = args.output
    else:
        timestamp   = datetime.now().strftime("%H%M%S")
        output_path = f"zeno_results_v2_student{args.student}_{timestamp}.csv"

    print(f"\nStarting {args.runs} sessions with Student {student_label}")
    print(f"Turns per session: {args.turns}")
    print(f"Output: {output_path}")
    print("─" * 50)

    all_records = []
    for run_id in range(1, args.runs + 1):
        try:
            records = run_session(
                client=client,
                zeno_prompt=zeno_prompt,
                student_prompt=student_prompt,
                zeno_text=zeno_text,
                student_text=student_text,
                num_turns=args.turns,
                run_id=run_id,
                student_type=args.student
            )
            all_records.extend(records)
        except Exception as e:
            print(f"\n  [Run {run_id}] ERROR: {e}")
            continue

    write_results(all_records, output_path)
    print_summary(all_records, args.student)


if __name__ == "__main__":
    main()
