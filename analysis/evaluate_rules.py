"""Score the Lambda's rule-based sentiment classifier against star ratings.

Ratings 4-5 are treated as POSITIVE, 1-2 as NEGATIVE, 3 as NEUTRAL.
Runs locally with no AWS access: the classifier is loaded from the Lambda
source without importing boto3.
"""
import ast
import csv
import logging
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parent.parent
LAMBDA = ROOT / "backend/lambda/sentiment-processor/lambda_function.py"
DATA = ROOT / "sample-data/customer-feedback-demo.csv"


def load_classifier():
    tree = ast.parse(LAMBDA.read_text())
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "analyze_sentiment")
    ns = {"Dict": Dict, "Any": Any, "logger": logging.getLogger(__name__)}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(LAMBDA), "exec"), ns)
    return ns["analyze_sentiment"]


def label_from_rating(rating: int) -> str:
    return "POSITIVE" if rating >= 4 else "NEGATIVE" if rating <= 2 else "NEUTRAL"


def main():
    analyze = load_classifier()
    rows = list(csv.DictReader(DATA.open()))
    confusion, misses = Counter(), []
    for r in rows:
        truth = label_from_rating(int(r["rating"]))
        pred = analyze(r["feedback"])["Sentiment"]
        confusion[(truth, pred)] += 1
        if truth != pred:
            misses.append((truth, pred, r["feedback"]))

    correct = sum(v for (t, p), v in confusion.items() if t == p)
    print(f"Rows: {len(rows)}  Accuracy vs star rating: {correct / len(rows):.0%}\n")
    labels = ["POSITIVE", "NEUTRAL", "NEGATIVE"]
    print("truth \\ pred".ljust(14) + "".join(l[:3].rjust(6) for l in labels))
    for t in labels:
        print(t.ljust(14) + "".join(str(confusion[(t, p)]).rjust(6) for p in labels))

    # Substring matching: 'unhelpful' also matches 'helpful', 'dislike' matches 'like'.
    traps = [w for r in rows for w in re.findall(r"\b(unhelpful|dislike|unreliable)\b", r["feedback"].lower())]
    print(f"\nWords that trigger both a negative and a positive substring match: {Counter(traps)}")
    print("\nMisclassified examples:")
    for t, p, text in misses:
        print(f"  [{t} -> {p}] {text}")


if __name__ == "__main__":
    main()
