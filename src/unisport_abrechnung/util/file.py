from collections.abc import Iterator
from itertools import count
from pathlib import Path


def find_free_file_name(file: Path):
    def candidates() -> Iterator[Path]:
        yield file
        for i in count(1):
            yield file.with_stem(file.stem + f"_{i}")

    for candidate in candidates():
        if not candidate.exists():
            return candidate
