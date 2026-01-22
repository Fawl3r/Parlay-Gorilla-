from __future__ import annotations


class ConsoleReporter:
    def print_lines(self, lines: list[str]) -> None:
        for line in lines:
            print(line)
