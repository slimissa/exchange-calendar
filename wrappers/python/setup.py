#!/usr/bin/env python3
"""
setup.py — Package configuration for exchange-calendar.

This is the legacy setup.py shim. Modern Python packaging uses
pyproject.toml as the single source of truth. This file exists
for backward compatibility with older pip versions and tools
that do not yet support PEP 517/518 fully.

The canonical configuration is in pyproject.toml.
"""

from setuptools import setup, find_packages

setup(
    name="exchange-calendar",
    version="1.0.0",
    description="Canonical, versioned, machine-readable registry of global exchange trading calendars",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="slimissa",
    author_email="slimissa@users.noreply.github.com",
    url="https://github.com/slimissa/exchange-calendar",
    license="Apache-2.0",
    packages=find_packages(where="."),
    package_dir={"": "."},
    include_package_data=True,
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="exchange calendar trading holidays finance market data",
    project_urls={
        "Source": "https://github.com/slimissa/exchange-calendar",
        "Bug Reports": "https://github.com/slimissa/exchange-calendar/issues",
        "Documentation": "https://github.com/slimissa/exchange-calendar#readme",
    },
)