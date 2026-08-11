"""Command line entry point for the `aula` static site generator."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .errors import Report
from .loader import load_site


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aula", description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)

    check = subcommands.add_parser("check", help="validate the content without building")
    _add_content_argument(check)
    check.add_argument(
        "--strict", action="store_true", help="treat warnings as errors (used by CI)"
    )
    check.add_argument(
        "--format",
        choices=["human", "github"],
        default="human",
        help="human-readable messages, or GitHub Actions annotations",
    )
    check.add_argument(
        "--borradores", action="store_true", help='include content marked estado = "borrador"'
    )

    build = subcommands.add_parser("build", help="validate the content and write the site")
    _add_content_argument(build)
    build.add_argument("--out", type=Path, required=True, help="output directory")
    build.add_argument(
        "--borradores", action="store_true", help='include content marked estado = "borrador"'
    )
    build.add_argument("--base-url", help="override base_url from site.toml")
    return parser


def _add_content_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--content", type=Path, default=Path("content"), help="the content directory"
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    content: Path = args.content
    if not content.is_dir():
        print(f"aula: there is no content directory at {content}", file=sys.stderr)
        return 2

    report = Report(root=content.resolve().parent)
    site = load_site(content.resolve(), report, include_drafts=args.borradores)

    strict = getattr(args, "strict", False)
    output_format = getattr(args, "format", "human")
    if report.problems:
        text = (
            report.format_github(strict)
            if output_format == "github"
            else report.format_human(strict)
        )
        print(text, file=sys.stderr)

    if site is None or report.has_errors(strict):
        return 1

    if args.command == "check":
        lessons = sum(1 for _ in site.walk())
        activities = sum(len(leccion.actividades) for _, _, leccion in site.walk())
        print(f"{len(site.cursos)} courses, {lessons} lessons, {activities} activities: all good")
        return 0

    print("aula build: rendering is not implemented yet", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
