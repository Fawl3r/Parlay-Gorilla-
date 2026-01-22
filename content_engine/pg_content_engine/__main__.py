from __future__ import annotations

import sys

from .cli import ContentEngineCli


def main() -> int:
    return ContentEngineCli().run()


if __name__ == "__main__":
    sys.exit(main())
