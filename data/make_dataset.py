"""
Dataset builder for the fine-tuned classifier.

Takes clean Python snippets and INJECTS each known bug type to produce labeled
examples automatically, then writes data/bugs.csv. The same controlled
injection is reused by the reliability tests.

Taxonomy: state_bug, logic_inverted, missing_validation, off_by_one,
dead_control, clean
"""

OUTPUT_CSV = "data/bugs.csv"

CATEGORIES = [
    "state_bug",
    "logic_inverted",
    "missing_validation",
    "off_by_one",
    "dead_control",
    "clean",
]


def build_dataset(output_csv: str = OUTPUT_CSV) -> None:
    """Generate labeled (snippet, category) rows and write them to CSV."""
    ...  # to be implemented


if __name__ == "__main__":
    build_dataset()
