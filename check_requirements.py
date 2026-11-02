"""Check requirements.txt pins against PyPI for Python 3.11, without installing anything."""
import json
import sys
import urllib.error
import urllib.request

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version

TARGET = Version("3.11")


def min_python(spec):
    """Lowest Python version a requires_python string allows, or None if it has no lower bound."""
    lows = [Version(s.version.rstrip(".*")) for s in SpecifierSet(spec) if s.operator in (">=", ">", "~=", "==", "===")]
    return max(lows, default=None)


def release_info(name, version):
    """PyPI 'info' block for name==version, or None if the project or release does not exist."""
    try:
        with urllib.request.urlopen(f"https://pypi.org/pypi/{name}/{version}/json", timeout=15) as r:
            return json.load(r)["info"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def main(path):
    lines = [l.strip() for l in open(path).read().splitlines()]
    lines = [l for l in lines if l and not l.startswith("#")]
    not_found = incompatible = 0
    highest = None

    for line in lines:
        req = Requirement(line)
        version = next(s.version for s in req.specifier if s.operator == "==")
        info = release_info(req.name, version)
        if info is None:
            not_found += 1
            continue
        rp = info.get("requires_python") or ""
        if not rp:
            continue
        incompatible += TARGET not in SpecifierSet(rp)
        low = min_python(rp)
        if low and (highest is None or low > highest[0]):
            highest = (low, f"{req.name}=={version} (>={low})")

    print(f"Dependencies checked: {len(lines)}")
    print(f"Not found on PyPI: {not_found}")
    print(f"Incompatible with Python {TARGET}: {incompatible}")
    print("Highest requirement:", highest[1] if highest else "none")


if __name__ == "__main__":
    assert min_python(">=3.7,<3.11") == Version("3.7")
    assert min_python("<3.11") is None and TARGET not in SpecifierSet(">=3.7,<3.11")
    main(sys.argv[1] if len(sys.argv) > 1 else "requirements.txt")
