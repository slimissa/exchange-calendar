"""Version guard for the divergence tools.

The reference libraries' versions decide what docs/DIVERGENCE.md says, so the
divergence tools refuse to run against any other version. The pins live in
one place, requirements-dev.txt (``name==version`` lines); this module reads
them from there and compares them to what is installed.

Usage from a tool:

    import divergence_pins
    rc = divergence_pins.check()
    if rc:
        return rc
"""
import re
import sys
from importlib import metadata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS = REPO_ROOT / "requirements-dev.txt"
LIBRARIES = ("exchange_calendars", "pandas_market_calendars")
EXIT_UNPINNED = 2


def _canonical(name):
    return re.sub(r"[-_.]+", "_", name).lower()


def read_pins(path=REQUIREMENTS):
    """Return {library: pinned version} for LIBRARIES, read from path.

    Raises ValueError if a library is missing or not pinned with ``==``.
    """
    pins = {}
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        m = re.match(r"^([A-Za-z0-9_.\-]+)\s*==\s*([^\s;]+)", line)
        if m and _canonical(m.group(1)) in LIBRARIES:
            pins[_canonical(m.group(1))] = m.group(2)
    missing = [lib for lib in LIBRARIES if lib not in pins]
    if missing:
        raise ValueError(f"{path} does not pin {', '.join(missing)} with '=='")
    return pins


def installed_versions():
    versions = {}
    for lib in LIBRARIES:
        try:
            versions[lib] = metadata.version(lib)
        except metadata.PackageNotFoundError:
            versions[lib] = None
    return versions


def mismatches(found, pins):
    """[(library, found, pinned)] for every library whose version is not the pin."""
    return [(lib, found.get(lib), pins[lib]) for lib in LIBRARIES if found.get(lib) != pins[lib]]


def check(found=None, what="installed", path=REQUIREMENTS, stream=None):
    """0 if every library in ``found`` (default: installed) matches its pin, else 2.

    On a mismatch, prints each library's version and pin and the install command.
    """
    stream = stream or sys.stderr
    try:
        pins = read_pins(path)
    except (OSError, ValueError) as exc:
        print(f"ERROR: cannot read the reference-library pins: {exc}", file=stream)
        return EXIT_UNPINNED
    found = installed_versions() if found is None else found
    bad = mismatches(found, pins)
    if not bad:
        return 0
    print(f"ERROR: reference libraries ({what}) do not match the pins in {Path(path).name}:", file=stream)
    for lib, have, want in bad:
        print(f"  {lib}: {what} {have or 'not installed'}, pinned {want}", file=stream)
    print("Run: pip install -r requirements-dev.txt", file=stream)
    return EXIT_UNPINNED
