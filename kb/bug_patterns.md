# Bug Pattern Knowledge Base

Each `##` card describes one common bug the retriever can surface for the
detector. Keep cards short and self-contained — one bug pattern per card.

## Streamlit state resets on rerun (state_bug)
Streamlit re-runs the whole script on every interaction. A value assigned to a
plain variable (e.g. `secret = random.randint(...)`) is regenerated every rerun.
Fix: store it once in `st.session_state` and read it back.

## Inverted higher/lower logic (logic_inverted)
Comparison branches are swapped, so the hint says "go higher" when the guess is
already too high. Fix: `guess > secret -> "Too High"`, `guess < secret -> "Too Low"`.

## Missing input validation (missing_validation)
User input is used without range/type checks, so out-of-range or non-numeric
values are accepted. Fix: parse and bounds-check before using the value.

## Off-by-one in counters/scores (off_by_one)
An index or attempt/score calculation is shifted by one (e.g. `attempt + 1`),
producing wrong totals or an early/late cutoff. Fix: align the arithmetic to the
intended count.

## Dead control / no-op button (dead_control)
A button or handler exists but its branch never updates state or reruns, so
clicking does nothing. Fix: update `st.session_state` and call `st.rerun()`.
