"""Run a lightweight evaluation pass against a saved proposal result payload."""

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from services.evaluation.ragas_eval import evaluate_generation


def main() -> None:
    """Load a JSON result payload and print simple evaluation metrics."""
    parser = argparse.ArgumentParser(description="Evaluate a generated proposal payload.")
    parser.add_argument("--result_json", required=True, help="Path to a saved result JSON file")
    args = parser.parse_args()

    payload = json.loads(Path(args.result_json).read_text(encoding="utf-8"))
    metrics = evaluate_generation(payload)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
