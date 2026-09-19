.PHONY: package build-wheel

# package — keep the Python wrapper's bundled calendar.json in sync with
# the registry built from exchanges/.
#
# wrappers/python/exchange_calendar/calendar.json is a shipped copy of
# the build artifact, so `pip install` users get a working registry
# without needing exchanges/ or tools/ at all. Nothing keeps that copy
# in sync automatically -- this target is the one command that does.
#
# Idempotent: tools/build.py's output is deterministic for a given set
# of exchanges/*.json files (no timestamps, sorted keys/exchanges), so
# running `make package` twice in a row with no source changes produces
# byte-for-byte identical output both times.
package:
	python3 tools/build.py
	cp calendar.json wrappers/python/exchange_calendar/calendar.json
	@echo "Synced wrappers/python/exchange_calendar/calendar.json"

# build-wheel — package, then build the Python wrapper's wheel.
# Requires the `build` package (pip install build).
build-wheel: package
	cd wrappers/python && python3 -m build
