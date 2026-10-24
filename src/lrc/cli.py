"""`lrc` command line (docs/USAGE.md)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from lrc import __version__, api, blux_adapter, engine, handoff, templates
from lrc.errors import EXIT_CHECK_FAILED, EXIT_FAILURE, EXIT_OK, EXIT_USAGE, ErrorCode, LrcError
from lrc.tree import read_manifest

COMMANDS = ("create", "scaffold", "compile", "plan", "migrate", "rollback", "validate", "templates", "version")
HIDDEN = ("blux-capability",)


def _spec_args(p: argparse.ArgumentParser, *, positional: bool = True) -> None:
    if positional:
        p.add_argument("spec", nargs="?", type=Path, help=".lrc schema or lrc.spec JSON file")
    else:
        p.add_argument("--spec", type=Path, help=".lrc schema or lrc.spec JSON file")
    p.add_argument("--template", "-T", action="append", default=[], metavar="ID", help="built-in template (repeatable)")
    p.add_argument("--set", action="append", default=[], metavar="KEY=VALUE", help="set or override a variable")
    p.add_argument("--base-dir", type=Path, help="directory @include/@copy may read from (default: the spec's)")


def _out(p: argparse.ArgumentParser) -> None:
    p.add_argument("--json", action="store_true", help="print the JSON document instead of a summary")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lrc",
        description="Deterministic repository creation, scaffolding and migration.",
        epilog="Exit codes: 0 done, 1 blocked by a check (nothing changed), 2 usage, 3 failed (rolled back), "
        "4 failed and rollback failed. Legacy form: lrc SCHEMA [-o DIR] [--dry-run] [--force] [--audit].",
    )
    parser.add_argument("--version", action="version", version=f"lrc {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    p = sub.add_parser("create", help="create a new repository (all or nothing)")
    _spec_args(p)
    p.add_argument("-o", "--out", type=Path, help="new repository directory (default: ./<project slug>)")
    p.add_argument("--git", action="store_true", default=None, help="make the reproducible initial git commit")
    p.add_argument("--blux", nargs="?", const="", metavar="PROJECT_ID", help="also generate .blux/")
    p.add_argument("-n", "--dry-run", action="store_true", help="show the plan; write nothing")
    p.add_argument("--audit", action="store_true", help="run DAT on the new repository (DAT handoff)")
    p.add_argument("--dat", metavar="EXE", help="DAT executable for --audit (default: dat)")
    _out(p)

    for name, text in (
        ("scaffold", "add a plan to an existing, unmanaged directory"),
        ("migrate", "move an LRC repository to a new plan"),
    ):
        p = sub.add_parser(name, help=text)
        _spec_args(p)
        p.add_argument("-o", "--out", "--target", dest="out", type=Path, required=True, help="the repository")
        p.add_argument(
            "-f", "--force", action="store_true", help="overwrite conflicting files (backed up in the journal)"
        )
        if name == "migrate":
            p.add_argument("--prune", action="store_true", help="delete unmodified files the new plan drops")
        p.add_argument("-n", "--dry-run", action="store_true", help="show what would change; change nothing")
        _out(p)

    for name in ("compile", "plan"):
        p = sub.add_parser(
            name, help="compile a spec to its plan (no writes)" if name == "compile" else "alias of compile"
        )
        _spec_args(p)
        p.add_argument("--git", action="store_true", default=None)
        p.add_argument("--blux", nargs="?", const="", metavar="PROJECT_ID")
        p.add_argument("--content", action="store_true", help="include file contents in the plan")
        p.add_argument("-o", "--output", type=Path, help="also write the plan JSON to this file")
        _out(p)

    p = sub.add_parser("validate", help="check a spec and/or that a repository still matches its manifest")
    p.add_argument("target", nargs="?", type=Path)
    _spec_args(p, positional=False)
    _out(p)

    p = sub.add_parser("rollback", help="undo the last (or a given) scaffold/migrate transaction")
    p.add_argument("target", type=Path)
    p.add_argument("--tx", metavar="ID", help="transaction id (default: the last committed one)")
    _out(p)

    p = sub.add_parser("templates", help="list built-in templates")
    _out(p)
    sub.add_parser("version", help="print the version")
    p = sub.add_parser("blux-capability")  # BLUX ADR-0009 entrypoint; not for people
    p.add_argument("capability_id", choices=blux_adapter.CAPABILITIES)
    return parser


def _variables(pairs: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for pair in pairs:
        key, eq, value = pair.partition("=")
        if not eq or not key:
            raise LrcError(ErrorCode.INVALID_INPUT, f"--set needs KEY=VALUE, got {pair!r}.")
        out[key] = value
    return out


def _request(args: argparse.Namespace) -> api.Request:
    blux = getattr(args, "blux", None)
    return api.Request(
        spec_file=args.spec,
        templates=list(args.template),
        variables=_variables(args.set),
        base_dir=args.base_dir,
        git=getattr(args, "git", None),
        blux=None if blux is None else ({"project_id": blux} if blux else {}),
    )


def _print_json(doc: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(doc, sort_keys=True, indent=2, ensure_ascii=False) + "\n")


def _print_result(doc: dict[str, Any]) -> None:
    counts = ", ".join(f"{n} {a}" for a, n in doc["summary"].items()) or "nothing"
    head = {
        "created": "Created",
        "applied": "Applied",
        "unchanged": "Already up to date:",
        "planned": "Plan for",
        "blocked": "Blocked:",
        "rolled_back": "Rolled back",
    }[doc["outcome"]]
    print(f"{head} {doc['target']} ({doc['operation']}: {counts})")
    if doc["outcome"] in ("planned", "blocked"):
        for c in doc["changes"]:
            if c["action"] != "unchanged":
                print(f"  {c['action']:<9} {c['path']}" + (f"  ({c['reason']})" if c.get("reason") else ""))
    if doc.get("plan_id"):
        print(f"  plan {doc['plan_id'][:16]}  tree {doc['tree_digest'][:16]}")
    if doc.get("git"):
        print(f"  git: {doc['git']['commit']} on {doc['git']['branch']}")
    if doc.get("transaction") and doc["outcome"] == "applied":
        print(f"  transaction {doc['transaction']} (undo: lrc rollback {doc['target']})")
    for w in doc.get("warnings", []):
        print(f"  warning: {w.get('origin', '')}: {w['message']}")
    if doc.get("audit"):
        a = doc["audit"]
        print(f"  DAT audit: {a['verdict']} ({a['findings']} findings, {a['blocking']} blocking)")
    elif doc.get("handoff"):
        print(f"  next: dat audit {doc['handoff']['input']['target']}")


def _emit(doc: dict[str, Any], as_json: bool) -> None:
    if as_json:
        _print_json(doc)
    else:
        _print_result(doc)


def _print_error(exc: LrcError, as_json: bool) -> None:
    if as_json:
        _print_json({"error": exc.to_dict()})
        return
    print(f"lrc: {exc.code.value}: {exc.message}", file=sys.stderr)
    for item in exc.details.get("issues", [])[1:] if exc.code is ErrorCode.PLAN_INVALID else []:
        where = f"{item['origin']}: " if item.get("origin") else ""
        print(f"  {where}{item['message']}", file=sys.stderr)
    for item in exc.details.get("conflicts", []):
        print(f"  conflict: {item['path']} ({item['reason']})", file=sys.stderr)


def _default_target(req: api.Request) -> Path:
    plan = api.compile_plan(req)
    if not plan.project["slug"]:
        raise LrcError(ErrorCode.INVALID_INPUT, "The spec has no project name; pass -o DIR.")
    return Path(plan.project["slug"])


def _create(args: argparse.Namespace) -> int:
    req = _request(args)
    target = args.out if args.out is not None else _default_target(req)
    dat = handoff.resolve(args.dat) if args.audit and not args.dry_run else None
    doc = api.create(req, target, dry_run=args.dry_run)
    code = EXIT_OK
    if dat is not None:
        doc["audit"] = handoff.run_dat(Path(doc["target"]), executable=dat)
        code = EXIT_CHECK_FAILED if doc["audit"]["verdict"] == "fail" else EXIT_OK
    _emit(doc, args.json)
    return code


def _apply(args: argparse.Namespace) -> int:
    req = _request(args)
    if args.command == "scaffold":
        doc = api.scaffold(req, args.out, force=args.force, dry_run=args.dry_run)
    else:
        doc = api.migrate(req, args.out, force=args.force, prune=args.prune, dry_run=args.dry_run)
    _emit(doc, args.json)
    return EXIT_CHECK_FAILED if doc["outcome"] == "blocked" else EXIT_OK


def _compile(args: argparse.Namespace) -> int:
    doc = api.compile_doc(_request(args), include_content=args.content)
    if args.output:
        args.output.write_text(json.dumps(doc, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.json:
        _print_json(doc)
    else:
        s = doc["summary"]
        print(
            f"{doc['spec']['label']}: {s['files']} files, {s['dirs']} dirs, "
            f"{s['symlinks']} symlinks, {s['bytes']} bytes"
        )
        for e in doc["entries"]:
            mode = e.get("mode", "    ")
            print(f"  {e['type']:<7} {mode} {e['path']}" + (f" -> {e['target']}" if e["type"] == "symlink" else ""))
        for w in doc["warnings"]:
            print(f"  warning: {w.get('origin', '')}: {w['message']}")
        print(f"plan {doc['plan_id']}")
    return EXIT_OK


def _validate(args: argparse.Namespace) -> int:
    req = _request(args) if (args.spec or args.template) else None
    doc = api.validate_doc(req, args.target)
    if args.json:
        _print_json(doc)
    else:
        what = " and ".join(x for x in (doc["target"], doc["spec"] and doc["spec"]["label"]) if x)
        print(
            f"{doc['verdict'].upper()}: {what} "
            f"({doc['summary']['errors']} errors, {doc['summary']['warnings']} warnings)"
        )
        for i in doc["issues"]:
            where = i.get("path") or i.get("origin") or ""
            print(f"  {i['severity']:<7} {i['code']:<22} {where}  {i['message']}")
    return EXIT_CHECK_FAILED if doc["verdict"] == "fail" else EXIT_OK


def _rollback(args: argparse.Namespace) -> int:
    doc = engine.rollback(args.target, args.tx)
    _emit(doc, args.json)
    return EXIT_OK


def _templates(args: argparse.Namespace) -> int:
    docs = [t.describe() for t in templates.catalog()]
    if args.json:
        _print_json({"templates": docs})
    else:
        for t in docs:
            print(f"{t['id']:<12} {t['version']:<7} {t['summary']}  (aliases: {', '.join(t['aliases'])})")
    return EXIT_OK


LEGACY_REMOVED = {
    "--bootstrap": "lrc --bootstrap was removed (it edited shell rc files); install with `pipx install outervoid-lrc`.",
    "-b": "lrc --bootstrap was removed (it edited shell rc files); install with `pipx install outervoid-lrc`.",
    "--platform-info": "lrc --platform-info was removed: output no longer depends on the platform.",
}


def _legacy(argv: list[str]) -> int:
    """LRC 1.x: `lrc SCHEMA [-o DIR] [--dry-run] [--force] [--audit] [-v]`."""
    p = argparse.ArgumentParser(prog="lrc", description="LRC 1.x compatible form (see `lrc --help`).")
    p.add_argument("spec", type=Path)
    p.add_argument("-o", "--out", "--output", dest="out", type=Path)
    p.add_argument("-n", "--dry-run", action="store_true")
    p.add_argument("-f", "--force", action="store_true")
    p.add_argument("--audit", action="store_true")
    p.add_argument("--base-dir", type=Path)
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)
    req = api.Request(spec_file=args.spec, base_dir=args.base_dir)
    dat = handoff.resolve() if args.audit and not args.dry_run else None
    target = args.out if args.out is not None else _default_target(req)
    if not target.exists() or (target.is_dir() and not any(target.iterdir())):
        doc = api.create(req, target, dry_run=args.dry_run)
    elif not args.force:
        engine.check_new_target(target)  # raises TARGET_EXISTS with guidance
        raise AssertionError("unreachable")
    elif read_manifest(target) is not None:
        doc = api.migrate(req, target, force=True, dry_run=args.dry_run)
    else:
        doc = api.scaffold(req, target, force=True, dry_run=args.dry_run)
    code = EXIT_OK
    if dat is not None:
        doc["audit"] = handoff.run_dat(Path(doc["target"]), executable=dat)
        code = EXIT_CHECK_FAILED if doc["audit"]["verdict"] == "fail" else EXIT_OK
    _print_result(doc)
    return code


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in LEGACY_REMOVED:
        print(f"lrc: {LEGACY_REMOVED[argv[0]]}", file=sys.stderr)
        return EXIT_USAGE
    legacy = bool(argv) and not argv[0].startswith("-") and argv[0] not in (*COMMANDS, *HIDDEN)
    if not legacy:
        parser = build_parser()
        try:
            args = parser.parse_args(argv)
        except SystemExit as exc:
            return EXIT_OK if exc.code == 0 else EXIT_USAGE
        if args.command is None:
            parser.print_help()
            return EXIT_USAGE
        if args.command == "blux-capability":
            return blux_adapter.main(args.capability_id)
        if args.command == "version":
            print(f"lrc {__version__}")
            return EXIT_OK
    as_json = not legacy and bool(getattr(args, "json", False))
    try:
        if legacy:
            try:
                return _legacy(argv)
            except SystemExit as exc:
                return EXIT_OK if exc.code == 0 else EXIT_USAGE
        handler = {
            "create": _create,
            "scaffold": _apply,
            "migrate": _apply,
            "compile": _compile,
            "plan": _compile,
            "validate": _validate,
            "rollback": _rollback,
            "templates": _templates,
        }[args.command]
        return handler(args)
    except LrcError as exc:
        _print_error(exc, as_json)
        return exc.exit_code
    except KeyboardInterrupt:
        print("lrc: interrupted", file=sys.stderr)
        return EXIT_FAILURE
