"""Print error lines from a sample log using three reading approaches."""

import re
from io import StringIO
from pathlib import Path


def find_errors(fpath: Path) -> None:
    """Print lines containing ``ERROR`` while iterating over the file."""
    with fpath.open(encoding="utf-8") as log_file:
        for line in log_file:
            if "ERROR" in line:
                print(line.strip())
    print()


def find_errors_in_memory(fpath: Path) -> None:
    """Read the file into memory, then print lines containing ``ERROR``."""
    log_content = fpath.read_text(encoding="utf-8")
    memory_log = StringIO(log_content)
    for line in memory_log:
        if "ERROR" in line:
            print(line.strip())
    print()


def find_errors_with_regex(fpath: Path) -> None:
    """Print lines containing ``ERROR`` with a regular expression."""
    log_content = fpath.read_text(encoding="utf-8")
    results = re.findall(r".*ERROR.*", log_content)
    for result in results:
        print(result)


if __name__ == "__main__":
    log_path = Path("log.txt")
    find_errors(log_path)
    find_errors_in_memory(log_path)
    find_errors_with_regex(log_path)
