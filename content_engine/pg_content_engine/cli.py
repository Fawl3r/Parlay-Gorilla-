from __future__ import annotations

import argparse
from typing import Sequence

from .cli_reporter import ConsoleReporter
from .storage import ContentEnginePathResolver, JsonFileGateway
from .workflows.workflow_factory import WorkflowFactory


class ContentEngineCli:
    def __init__(self) -> None:
        self._reporter = ConsoleReporter()
        self._factory = WorkflowFactory(ContentEnginePathResolver(), JsonFileGateway())

    def run(self, args: Sequence[str] | None = None) -> int:
        parser = self._build_parser()
        parsed = parser.parse_args(args=args)
        if parsed.channel == "x":
            return self._handle_x(parsed)
        if parsed.channel == "video":
            return self._handle_video(parsed)
        self._reporter.print_lines(["Unknown command."])
        return 1

    def _build_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog="pg_content_engine")
        subparsers = parser.add_subparsers(dest="channel", required=True)
        self._add_x_commands(subparsers)
        self._add_video_commands(subparsers)
        return parser

    def _add_x_commands(self, subparsers: argparse._SubParsersAction) -> None:
        x_parser = subparsers.add_parser("x")
        x_sub = x_parser.add_subparsers(dest="action", required=True)
        validate = x_sub.add_parser("validate")
        validate.set_defaults(action="validate")
        approve = x_sub.add_parser("approve")
        approve.add_argument("--keep", action="store_true", help="Keep items in queue after approval.")
        approve.set_defaults(action="approve")

    def _add_video_commands(self, subparsers: argparse._SubParsersAction) -> None:
        video_parser = subparsers.add_parser("video")
        video_sub = video_parser.add_subparsers(dest="action", required=True)
        validate = video_sub.add_parser("validate")
        validate.set_defaults(action="validate")
        approve = video_sub.add_parser("approve")
        approve.add_argument("--keep", action="store_true", help="Keep items in queue after approval.")
        approve.set_defaults(action="approve")

    def _handle_x(self, parsed: argparse.Namespace) -> int:
        processor = self._factory.build_x_processor()
        if parsed.action == "validate":
            report = processor.validate_queue()
            self._reporter.print_lines(report.summary_lines())
            return 0
        if parsed.action == "approve":
            summary = processor.approve_queue(keep=parsed.keep)
            self._reporter.print_lines(summary.summary_lines())
            return 0
        self._reporter.print_lines(["Unknown x command."])
        return 1

    def _handle_video(self, parsed: argparse.Namespace) -> int:
        processor = self._factory.build_video_processor()
        if parsed.action == "validate":
            report = processor.validate_queue()
            self._reporter.print_lines(report.summary_lines())
            return 0
        if parsed.action == "approve":
            summary = processor.approve_queue(keep=parsed.keep)
            self._reporter.print_lines(summary.summary_lines())
            return 0
        self._reporter.print_lines(["Unknown video command."])
        return 1
