"""Command line entry point for the `aula` static site generator."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .errors import Report
from .loader import load_site
from .render import render_site


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aula", description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)

    check = subcommands.add_parser("check", help="validate the content without building")
    _add_content_argument(check)
    _add_drafts_argument(check)
    check.add_argument(
        "--strict", action="store_true", help="treat warnings as errors (used by CI)"
    )
    check.add_argument(
        "--format",
        choices=["human", "github"],
        default="human",
        help="human-readable messages, or GitHub Actions annotations",
    )

    build = subcommands.add_parser("build", help="validate the content and write the site")
    _add_content_argument(build)
    _add_drafts_argument(build)
    build.add_argument("--out", type=Path, required=True, help="output directory")
    build.add_argument("--base-url", help="override base_url from site.toml")

    serve = subcommands.add_parser("serve", help="build, serve locally and rebuild on change")
    _add_content_argument(serve)
    _add_drafts_argument(serve)
    serve.add_argument("--out", type=Path, help="output directory (a temporary one by default)")
    serve.add_argument("--port", type=int, default=8000)
    return parser


def _add_content_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--content", type=Path, default=Path("content"), help="the content directory"
    )


def _add_drafts_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--borradores", action="store_true", help='include content marked estado = "borrador"'
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    content: Path = args.content
    if not content.is_dir():
        print(f"aula: there is no content directory at {content}", file=sys.stderr)
        return 2

    if args.command == "serve":
        return _serve(args)

    site, report = _load(args)
    strict = getattr(args, "strict", False)
    _print_problems(report, strict, getattr(args, "format", "human"))
    if site is None or report.has_errors(strict):
        return 1

    if args.command == "check":
        lessons = sum(1 for _ in site.walk())
        activities = sum(len(leccion.actividades) for _, _, leccion in site.walk())
        print(f"{len(site.cursos)} courses, {lessons} lessons, {activities} activities: all good")
        return 0

    if args.base_url:
        site.base_url = _normalise(args.base_url)
    pages = render_site(site, args.out.resolve(), report)
    if report.has_errors():
        _print_problems(report, strict, "human")
        return 1
    print(f"{pages} pages written to {args.out}")
    return 0


def _load(args) -> tuple[object, Report]:
    content = args.content.resolve()
    report = Report(root=content.parent)
    return load_site(content, report, include_drafts=args.borradores), report


def _print_problems(report: Report, strict: bool, output_format: str) -> None:
    if not report.problems:
        return
    text = (
        report.format_github(strict) if output_format == "github" else report.format_human(strict)
    )
    print(text, file=sys.stderr)


def _normalise(url: str) -> str:
    if not url.startswith("/"):
        url = "/" + url
    return url if url.endswith("/") else url + "/"


def _serve(args) -> int:
    """Build into a directory, serve it, and rebuild whenever the content changes."""
    import http.server
    import tempfile
    import threading
    import time

    out = (args.out or Path(tempfile.mkdtemp(prefix="aula-"))).resolve()
    content = args.content.resolve()

    def rebuild() -> None:
        site, report = _load(args)
        _print_problems(report, False, "human")
        if site is None or report.has_errors():
            print("aula: the site was not rebuilt; fix the errors above", file=sys.stderr)
            return
        site.base_url = "/"
        pages = render_site(site, out, report)
        _print_problems(report, False, "human")
        print(f"aula: {pages} pages rebuilt")

    rebuild()

    def watch() -> None:
        """Poll modification times. Cheap enough for a content tree this size."""
        previous = _snapshot(content)
        while True:
            time.sleep(0.5)
            current = _snapshot(content)
            if current != previous:
                previous = current
                rebuild()

    threading.Thread(target=watch, daemon=True).start()

    handler = _handler_for(out, http.server)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"aula: serving http://127.0.0.1:{args.port}/  (Ctrl-C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\naula: stopped")
    return 0


def _handler_for(directory: Path, http_server):
    class Handler(http_server.SimpleHTTPRequestHandler):
        def __init__(self, *handler_args, **handler_kwargs):
            super().__init__(*handler_args, directory=str(directory), **handler_kwargs)

        def log_message(self, *_args):  # keep the console for build output
            pass

    return Handler


def _snapshot(content: Path) -> dict[str, float]:
    return {
        str(path): path.stat().st_mtime
        for path in content.rglob("*")
        if path.is_file() and not path.name.startswith(".")
    }


if __name__ == "__main__":
    raise SystemExit(main())
