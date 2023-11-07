#!/usr/bin/env python3

from pathlib import Path
import sys


if __name__ == '__main__':
    source_path = str(Path(__file__).parent / "src")
    if source_path not in sys.path:
        sys.path.append(source_path)

    from unisport_abrechnung.cli.unisport_abrechnung import main
    sys.exit(main())
