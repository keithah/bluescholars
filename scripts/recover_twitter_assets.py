#!/usr/bin/env python3
"""Resume capture-linked image and stylesheet acquisition for the Twitter archive."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from restore.twitter import recover_linked_assets


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--max-files", type=int, default=75)
    parser.add_argument("--delay", type=float, default=0.25)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--retry-failed", action="store_true")
    args = parser.parse_args()
    if args.max_files < 1 or args.delay < 0 or args.timeout < 1:
        parser.error("max-files and timeout must be positive; delay must not be negative")
    result = recover_linked_assets(args.root, args.max_files, args.delay,
                                   args.timeout, args.retry_failed)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
