"""CLI interface for IniForge."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .converter import convert_config, detect_format
from .diff import diff_configs, format_diff_text, format_diff_unified
from .env_parser import parse_env
from .ini_parser import parse_ini
from .merge import MergeStrategy, merge_configs
from .models import ConfigFile
from .properties_parser import parse_properties
from .query import query_config
from .validator import format_validation_report, validate_config


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="iniforge",
        description="Configuration File Processing Toolkit — parse, query, diff, merge, convert",
    )
    parser.add_argument("--version", action="version", version=f"iniforge {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Parse command
    parse_cmd = subparsers.add_parser("parse", help="Parse and display a config file")
    parse_cmd.add_argument("file", help="Config file to parse")
    parse_cmd.add_argument("--format", "-f", choices=["ini", "properties", "env", "auto"], default="auto")
    parse_cmd.add_argument("--json", action="store_true", help="Output as JSON")
    parse_cmd.add_argument("--sections", action="store_true", help="Show sections only")

    # Query command
    query_cmd = subparsers.add_parser("query", help="Query a config file")
    query_cmd.add_argument("file", help="Config file to query")
    query_cmd.add_argument("query_expr", help="Query expression (dot notation)")
    query_cmd.add_argument("--format", "-f", choices=["ini", "properties", "env", "auto"], default="auto")

    # Diff command
    diff_cmd = subparsers.add_parser("diff", help="Diff two config files")
    diff_cmd.add_argument("file1", help="Base config file")
    diff_cmd.add_argument("file2", help="Modified config file")
    diff_cmd.add_argument("--format1", "-f1", choices=["ini", "properties", "env", "auto"], default="auto")
    diff_cmd.add_argument("--format2", "-f2", choices=["ini", "properties", "env", "auto"], default="auto")
    diff_cmd.add_argument("--unified", "-u", action="store_true", help="Unified diff format")

    # Merge command
    merge_cmd = subparsers.add_parser("merge", help="Merge two config files")
    merge_cmd.add_argument("file1", help="Base config file")
    merge_cmd.add_argument("file2", help="Override config file")
    merge_cmd.add_argument("--strategy", "-s", choices=["override", "keep", "union", "deep"], default="override")
    merge_cmd.add_argument("--format", "-f", choices=["ini", "properties", "env", "auto"], default="auto")
    merge_cmd.add_argument("--output", "-o", help="Output file")

    # Convert command
    convert_cmd = subparsers.add_parser("convert", help="Convert config file format")
    convert_cmd.add_argument("file", help="Input config file")
    convert_cmd.add_argument("--to", "-t", required=True, choices=["ini", "properties", "env", "json", "yaml", "toml"])
    convert_cmd.add_argument(
        "--from",
        "-f",
        dest="from_format",
        choices=["ini", "properties", "env", "auto"],
        default="auto",
    )
    convert_cmd.add_argument("--output", "-o", help="Output file")

    # Validate command
    validate_cmd = subparsers.add_parser("validate", help="Validate a config file")
    validate_cmd.add_argument("file", help="Config file to validate")
    validate_cmd.add_argument("--format", "-f", choices=["ini", "properties", "env", "auto"], default="auto")
    validate_cmd.add_argument("--strict", action="store_true", help="Strict mode (warnings are errors)")
    validate_cmd.add_argument("--json", action="store_true", help="Output as JSON")

    # Info command
    info_cmd = subparsers.add_parser("info", help="Show config file info")
    info_cmd.add_argument("file", help="Config file")
    info_cmd.add_argument("--format", "-f", choices=["ini", "properties", "env", "auto"], default="auto")

    # Detect command
    detect_cmd = subparsers.add_parser("detect", help="Detect config file format")
    detect_cmd.add_argument("file", help="Config file")

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    try:
        if args.command == "parse":
            return _cmd_parse(args)
        elif args.command == "query":
            return _cmd_query(args)
        elif args.command == "diff":
            return _cmd_diff(args)
        elif args.command == "merge":
            return _cmd_merge(args)
        elif args.command == "convert":
            return _cmd_convert(args)
        elif args.command == "validate":
            return _cmd_validate(args)
        elif args.command == "info":
            return _cmd_info(args)
        elif args.command == "detect":
            return _cmd_detect(args)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


def _load_config(file_path: str, fmt: str = "auto") -> ConfigFile:
    """Load and parse a config file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    content = path.read_text(encoding="utf-8")

    if fmt == "auto":
        fmt = detect_format(content)

    if fmt == "ini":
        return parse_ini(content, source_file=file_path)
    elif fmt == "properties":
        return parse_properties(content, source_file=file_path)
    elif fmt == "env":
        return parse_env(content, source_file=file_path)
    else:
        raise ValueError(f"Unsupported format: {fmt}")


def _cmd_parse(args: argparse.Namespace) -> int:
    """Parse and display a config file."""
    config = _load_config(args.file, args.format)

    if args.json:
        print(json.dumps(config.to_dict(), indent=2, ensure_ascii=False))
    elif args.sections:
        for section in config.sections:
            print(f"[{section.name}]")
            for entry in section.entries:
                print(f"  {entry.key} = {entry.value}")
    else:
        print(f"Format: {config.format}")
        print(f"Sections: {len(config.sections)}")
        print(f"Total entries: {sum(len(s.entries) for s in config.all_sections)}")
        print()

        if config.globals.entries:
            print("[globals]")
            for entry in config.globals.entries:
                print(f"  {entry.key} = {entry.value}")

        for section in config.sections:
            print(f"\n[{section.name}]")
            for entry in section.entries:
                print(f"  {entry.key} = {entry.value}")

    return 0


def _cmd_query(args: argparse.Namespace) -> int:
    """Query a config file."""
    config = _load_config(args.file, args.format)
    result = query_config(config, args.query_expr)

    if result is None:
        print(f"Key not found: {args.query_expr}", file=sys.stderr)
        return 1

    if isinstance(result, dict):
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result)

    return 0


def _cmd_diff(args: argparse.Namespace) -> int:
    """Diff two config files."""
    config1 = _load_config(args.file1, args.format1)
    config2 = _load_config(args.file2, args.format2)

    result = diff_configs(config1, config2)

    if args.unified:
        print(format_diff_unified(result))
    else:
        print(format_diff_text(result))

    return 0 if result.identical else 1


def _cmd_merge(args: argparse.Namespace) -> int:
    """Merge two config files."""
    config1 = _load_config(args.file1, args.format)
    config2 = _load_config(args.file2, args.format)

    strategy = MergeStrategy(args.strategy)
    merged = merge_configs(config1, config2, strategy)

    # Determine output format
    output_fmt = args.format if args.format != "auto" else config1.format

    from .converter import convert_config

    output = convert_config(merged, output_fmt)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Written to {args.output}")
    else:
        print(output)

    return 0


def _cmd_convert(args: argparse.Namespace) -> int:
    """Convert config file format."""
    config = _load_config(args.file, args.from_format)
    output = convert_config(config, args.to)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Written to {args.output}")
    else:
        print(output)

    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    """Validate a config file."""
    config = _load_config(args.file, args.format)

    result = validate_config(config)

    if args.json:
        data = {
            "valid": result.valid,
            "score": result.score,
            "issues": [
                {"rule": i.rule, "message": i.message, "severity": i.severity.value, "path": i.path}
                for i in result.issues
            ],
        }
        print(json.dumps(data, indent=2))
    else:
        print(format_validation_report(result))

    return 0 if result.valid else 1


def _cmd_info(args: argparse.Namespace) -> int:
    """Show config file info."""
    config = _load_config(args.file, args.format)

    print(f"File: {args.file}")
    print(f"Format: {config.format}")
    print(f"Sections: {len(config.sections)}")
    total = sum(len(s.entries) for s in config.all_sections)
    print(f"Total entries: {total}")

    if config.sections:
        print("\nSections:")
        for section in config.sections:
            print(f"  [{section.name}] — {len(section.entries)} entries")

    return 0


def _cmd_detect(args: argparse.Namespace) -> int:
    """Detect config file format."""
    path = Path(args.file)
    if not path.exists():
        print(f"File not found: {args.file}", file=sys.stderr)
        return 1

    content = path.read_text(encoding="utf-8")
    fmt = detect_format(content)
    print(f"Detected format: {fmt}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
