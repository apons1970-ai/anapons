"""Command line entry point for the `aula` static site generator."""

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(prog="aula", description=__doc__)
    parser.add_argument("command", choices=["build", "check"])
    args = parser.parse_args()
    print(f"aula {args.command}: not implemented yet", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
