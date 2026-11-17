import subprocess
from pathlib import Path
import re
from io import StringIO

def find_errors(fpath: Path) -> None:
    with open(fpath, "r") as file:
        for line in file:
            # print(line)
            if "ERROR" in line:
                print(line.strip())
        print("\n")

def find_errors_in_memory(fpath: Path) -> None:
    log_content = fpath.read_text()
    memory_log = StringIO(log_content)
    for line in memory_log:
        if "ERROR" in line:
            print(line.strip())
    print("\n")
    
def find_errors_with_regex(fpath: Path) -> None:
    log_content = fpath.read_text()
    results = re.findall(f".*ERROR.*", log_content)
    for result in results:
        print(result)
    
if __name__ == "__main__":
    fpath = Path() / "log.txt"
    find_errors(fpath)

    find_errors_in_memory(fpath)
    
    find_errors_with_regex(fpath)
