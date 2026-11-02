"""Check requirements.txt pins against PyPI for Python 3.11, without installing anything."""
import json
import sys
from urllib.error import HTTPError
from urllib.request import urlopen

from packaging.specifiers import SpecifierSet
from packaging.version import Version

lines = [l.strip() for l in open(sys.argv[1] if len(sys.argv) > 1 else "requirements.txt")]
lines = [l for l in lines if l and not l.startswith("#")]
not_found = incompatible = 0
highest = (Version("0"), "none")

for line in lines:
    name, version = map(str.strip, line.split("=="))
    try:
        rp = json.load(urlopen(f"https://pypi.org/pypi/{name}/{version}/json"))["info"]["requires_python"]
    except HTTPError as e:
        if e.code != 404:
            raise
        not_found += 1
        continue
    if not rp:
        continue
    spec = SpecifierSet(rp)
    incompatible += "3.11" not in spec
    low = max((Version(s.version) for s in spec if s.operator in (">=", ">", "~=")), default=Version("0"))
    if low > highest[0]:
        highest = (low, f"{name}=={version} (>={low})")

print(f"Dependencies checked: {len(lines)}")
print(f"Not found on PyPI: {not_found}")
print(f"Incompatible with Python 3.11: {incompatible}")
print(f"Highest requirement: {highest[1]}")
