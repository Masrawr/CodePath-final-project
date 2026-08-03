"""
Dataset builder for the fine-tuned classifier.

Takes clean Python snippets and INJECTS each known bug type to produce labeled
examples automatically, then writes data/bugs.csv. Because we control the
injection, every row's label is exact (no hand-labeling). The same controlled
injection is reused by the reliability tests.

Taxonomy (one label per snippet):
    state_bug          - a value is regenerated on every Streamlit rerun
    logic_inverted     - higher/lower (or other) comparison branches swapped
    missing_validation - user input used without range/type checks
    off_by_one         - an index or count arithmetic is shifted by one
    dead_control       - a button/handler exists but never updates state
    clean              - correct code, no bug

Run:  python3 data/make_dataset.py
"""

import csv
import itertools
import os

OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "bugs.csv")

CATEGORIES = [
    "state_bug",
    "logic_inverted",
    "missing_validation",
    "off_by_one",
    "dead_control",
    "clean",
]

# How many examples to emit per category (kept balanced across classes).
PER_CATEGORY = 80

# --- Parameter pools: swapping these gives many distinct-looking snippets ----
SECRET_VARS = ["secret", "target", "answer", "number", "code", "hidden"]
GUESS_VARS = ["guess", "attempt", "value", "pick", "choice", "entry"]
LOWS = [0, 1]
HIGHS = [10, 20, 50, 100]
COLLECTIONS = ["items", "rows", "cards", "scores", "names"]
KEYS = ["secret", "target", "answer", "number"]


# --- Snippet templates -------------------------------------------------------
# Each function returns (clean_code, buggy_code) for one scenario, so the clean
# side feeds the "clean" class and the buggy side feeds its bug category.

def scenario_compare(sv, gv):
    """Higher/lower comparison -> logic_inverted when branches are swapped."""
    clean = (
        f"def check_guess({gv}, {sv}):\n"
        f"    if {gv} == {sv}:\n"
        f"        return 'Win'\n"
        f"    if {gv} > {sv}:\n"
        f"        return 'Too High'\n"
        f"    return 'Too Low'"
    )
    buggy = (
        f"def check_guess({gv}, {sv}):\n"
        f"    if {gv} == {sv}:\n"
        f"        return 'Win'\n"
        f"    if {gv} > {sv}:\n"
        f"        return 'Too Low'\n"
        f"    return 'Too High'"
    )
    return clean, buggy


def scenario_validation(gv, low, high):
    """Range check -> missing_validation when the bounds check is dropped."""
    clean = (
        f"def parse_{gv}(raw):\n"
        f"    {gv} = int(raw)\n"
        f"    if {gv} < {low} or {gv} > {high}:\n"
        f"        return None\n"
        f"    return {gv}"
    )
    buggy = (
        f"def parse_{gv}(raw):\n"
        f"    {gv} = int(raw)\n"
        f"    return {gv}"
    )
    return clean, buggy


def scenario_index(coll):
    """Loop bound -> off_by_one when range overshoots the collection length."""
    clean = (
        f"def show({coll}):\n"
        f"    for i in range(len({coll})):\n"
        f"        print({coll}[i])"
    )
    buggy = (
        f"def show({coll}):\n"
        f"    for i in range(len({coll}) + 1):\n"
        f"        print({coll}[i])"
    )
    return clean, buggy


def scenario_score(gv):
    """Score math -> off_by_one when attempts is shifted by one."""
    clean = (
        f"def score({gv}s):\n"
        f"    points = 100 - 10 * {gv}s\n"
        f"    return max(points, 10)"
    )
    buggy = (
        f"def score({gv}s):\n"
        f"    points = 100 - 10 * ({gv}s + 1)\n"
        f"    return max(points, 10)"
    )
    return clean, buggy


def scenario_state(key, low, high):
    """Streamlit init -> state_bug when the value is regenerated every rerun."""
    clean = (
        f"if '{key}' not in st.session_state:\n"
        f"    st.session_state.{key} = random.randint({low}, {high})\n"
        f"{key} = st.session_state.{key}"
    )
    buggy = (
        f"if '{key}' not in st.session_state:\n"
        f"    st.session_state.{key} = random.randint({low}, {high})\n"
        f"{key} = random.randint({low}, {high})"
    )
    return clean, buggy


def scenario_button(key):
    """Button handler -> dead_control when the click never updates state."""
    clean = (
        f"if st.button('New Game'):\n"
        f"    st.session_state.{key} = 'playing'\n"
        f"    st.rerun()"
    )
    buggy = (
        f"if st.button('New Game'):\n"
        f"    pass"
    )
    return clean, buggy


def _cycle(pool):
    """Endless cycle over a pool so we can take exactly PER_CATEGORY items."""
    return itertools.cycle(pool)


def _generate():
    """Yield (snippet, label) rows, balanced to PER_CATEGORY per class.

    Buggy rows go straight into their class. Clean rows are collected per
    scenario so the final `clean` class stays diverse across ALL scenario
    types (compare, validation, index/score, state, button) instead of being
    dominated by whichever scenario ran first.
    """
    buggy_rows = []
    clean_by_scenario = {}  # scenario name -> list of unique clean snippets

    def add(scenario, clean, buggy, label):
        buggy_rows.append((buggy, label))
        bucket = clean_by_scenario.setdefault(scenario, [])
        if clean not in bucket:
            bucket.append(clean)

    # logic_inverted
    combos = itertools.cycle(list(itertools.product(SECRET_VARS, GUESS_VARS)))
    for _ in range(PER_CATEGORY):
        sv, gv = next(combos)
        clean, buggy = scenario_compare(sv, gv)
        add("compare", clean, buggy, "logic_inverted")

    # missing_validation
    combos = itertools.cycle(list(itertools.product(GUESS_VARS, LOWS, HIGHS)))
    for _ in range(PER_CATEGORY):
        gv, low, high = next(combos)
        clean, buggy = scenario_validation(gv, low, high)
        add("validation", clean, buggy, "missing_validation")

    # off_by_one (split between the index and score scenarios)
    coll_cycle = _cycle(COLLECTIONS)
    gv_cycle = _cycle(GUESS_VARS)
    for i in range(PER_CATEGORY):
        if i % 2 == 0:
            clean, buggy = scenario_index(next(coll_cycle))
            add("index", clean, buggy, "off_by_one")
        else:
            clean, buggy = scenario_score(next(gv_cycle))
            add("score", clean, buggy, "off_by_one")

    # state_bug
    combos = itertools.cycle(list(itertools.product(KEYS, LOWS, HIGHS)))
    for _ in range(PER_CATEGORY):
        key, low, high = next(combos)
        clean, buggy = scenario_state(key, low, high)
        add("state", clean, buggy, "state_bug")

    # dead_control
    key_cycle = _cycle(KEYS + ["status", "score", "attempts"])
    for _ in range(PER_CATEGORY):
        clean, buggy = scenario_button(next(key_cycle))
        add("button", clean, buggy, "dead_control")

    # Round-robin across scenarios to fill PER_CATEGORY diverse clean rows.
    clean_rows = []
    scenarios = list(clean_by_scenario)
    cursors = {s: 0 for s in scenarios}
    while len(clean_rows) < PER_CATEGORY:
        progressed = False
        for s in scenarios:
            if len(clean_rows) >= PER_CATEGORY:
                break
            bucket = clean_by_scenario[s]
            if cursors[s] < len(bucket):
                clean_rows.append((bucket[cursors[s]], "clean"))
                cursors[s] += 1
                progressed = True
        if not progressed:  # every bucket exhausted (not enough uniques)
            break

    return buggy_rows + clean_rows


def build_dataset(output_csv: str = OUTPUT_CSV) -> None:
    """Generate labeled (snippet, category) rows and write them to CSV."""
    rows = _generate()

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["snippet", "label"])
        writer.writerows(rows)

    counts = {}
    for _, label in rows:
        counts[label] = counts.get(label, 0) + 1
    print(f"Wrote {len(rows)} rows to {output_csv}")
    for label in CATEGORIES:
        print(f"  {label:20s} {counts.get(label, 0)}")


if __name__ == "__main__":
    build_dataset()
